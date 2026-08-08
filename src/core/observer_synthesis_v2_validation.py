"""Independent fail-closed validation for R14 observer grammar catalogs."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_core_codec import canonical_observer_bytes
from .observer_core_semantics import infer_observer_kind
from .observer_core_types import Apply, Input, LeafKind, Pair, PairKind, PrimitiveId
from .observer_synthesis_v2_catalog_provenance import verify_catalog_brand_v2
from .observer_synthesis_v2_grammar import BOUNDARY, GRAMMAR_SCHEMA
from .observer_synthesis_v2_types import (
    ObserverCandidateV2,
    ObserverGrammarEnumerationV2,
    ObserverGrammarStratumV2,
    ObserverGrammarV2,
)

logger = logging.getLogger(__name__)


def _response_kind_matches(value: object, expected: object) -> bool:
    logger.debug(
        "_response_kind_matches entry value=%s expected=%s",
        type(value).__name__,
        type(expected).__name__,
    )
    if type(expected) is LeafKind:
        result = type(value) is LeafKind and value is expected
    elif type(expected) is PairKind and type(value) is PairKind:
        result = _response_kind_matches(
            value.left,
            expected.left,
        ) and _response_kind_matches(value.right, expected.right)
    else:
        result = False
    logger.debug("_response_kind_matches exit result=%s", result)
    return result


def _observer_rank_v2(observer: object) -> tuple[int, int]:
    """Recover exact grammar cost/depth without constructing candidate DTOs."""
    logger.debug("_observer_rank_v2 entry type=%s", type(observer).__name__)
    if type(observer) is Input:
        result = (0, 0)
    elif type(observer) is Apply:
        child_cost, child_depth = _observer_rank_v2(observer.child)
        if (
            observer.primitive not in {PrimitiveId.TAIL, PrimitiveId.CREST}
            or infer_observer_kind(observer.child) is not LeafKind.RECURRENCE
        ):
            raise ValueError("invalid-catalog-apply")
        result = (child_cost + 1, child_depth + 1)
    elif type(observer) is Pair:
        left_cost, left_depth = _observer_rank_v2(observer.left)
        right_cost, right_depth = _observer_rank_v2(observer.right)
        result = (
            left_cost + right_cost + 1,
            max(left_depth, right_depth) + 1,
        )
    else:
        raise ValueError("invalid-catalog-observer")
    logger.debug("_observer_rank_v2 exit cost=%d depth=%d", *result)
    return result


def _candidate_matches(candidate: object, cost: int, max_depth: int) -> bool:
    logger.debug("_candidate_matches entry type=%s", type(candidate).__name__)
    if type(candidate) is not ObserverCandidateV2:
        logger.error("R14 candidate validation rejected type=%s", type(candidate).__name__)
        return False
    try:
        canonical = canonical_observer_bytes(candidate.observer)
        inferred = infer_observer_kind(candidate.observer)
        actual_cost, actual_depth = _observer_rank_v2(candidate.observer)
        result = (
            type(candidate.cost) is int
            and type(candidate.depth) is int
            and type(candidate.canonical) is bytes
            and type(candidate.digest) is str
            and canonical == candidate.canonical
            and _response_kind_matches(candidate.response_kind, inferred)
            and candidate.cost == actual_cost == cost
            and candidate.depth == actual_depth
            and candidate.depth <= max_depth
            and candidate.digest == sha256(canonical).hexdigest()
        )
    except Exception as exc:
        logger.error("R14 candidate validation rejected error=%s", type(exc).__name__)
        return False
    logger.debug("_candidate_matches exit result=%s", result)
    return result


def verify_observer_grammar_enumeration_v2(
    report: object,
    construction_ledger: object = None,
) -> bool:
    """Verify one sealed catalog in place without constructing it again."""
    logger.debug(
        "verify_observer_grammar_enumeration_v2 entry type=%s",
        type(report).__name__,
    )
    if type(report) is not ObserverGrammarEnumerationV2:
        logger.error("R14 catalog validation rejected report type")
        return False
    if type(report.grammar) is not ObserverGrammarV2:
        logger.error("R14 catalog validation rejected grammar type")
        return False
    try:
        grammar = report.grammar
        scalar_ok = (
            verify_catalog_brand_v2(report, construction_ledger)
            and type(grammar.schema) is str
            and grammar.schema == GRAMMAR_SCHEMA
            and type(grammar.grammar_id) is str
            and bool(grammar.grammar_id)
            and type(grammar.max_cost) is int
            and 0 <= grammar.max_cost <= 6
            and type(grammar.max_depth) is int
            and 0 <= grammar.max_depth <= 4
            and type(grammar.candidate_limit) is int
            and type(grammar.canonical_bytes_limit) is int
            and type(report.strata) is tuple
            and type(report.candidates) is tuple
            and type(report.canonical_bytes) is int
            and type(report.max_row_bytes) is int
            and type(report.catalog_digest) is str
            and report.complete is True
            and type(report.boundary) is str
            and report.boundary == BOUNDARY
            and len(report.strata) == grammar.max_cost + 1
            and 0 < len(report.candidates) <= grammar.candidate_limit
            and 0 < report.canonical_bytes <= grammar.canonical_bytes_limit
        )
        if not scalar_ok:
            logger.error("R14 catalog validation rejected scalar fields")
            return False
        flattened: list[ObserverCandidateV2] = []
        seen: set[bytes] = set()
        for expected_cost, row in enumerate(report.strata):
            if (
                type(row) is not ObserverGrammarStratumV2
                or type(row.candidates) is not tuple
                or type(row.cost) is not int
                or type(row.canonical_bytes) is not int
                or row.cost != expected_cost
                or row.canonical_bytes
                != sum(len(item.canonical) for item in row.candidates)
            ):
                logger.error("R14 catalog validation rejected stratum")
                return False
            if any(
                not _candidate_matches(item, expected_cost, grammar.max_depth)
                for item in row.candidates
            ):
                return False
            ordering = tuple(
                (item.depth, item.canonical) for item in row.candidates
            )
            if ordering != tuple(sorted(ordering)):
                return False
            for item in row.candidates:
                if item.canonical in seen:
                    return False
                seen.add(item.canonical)
                flattened.append(item)
        if len(flattened) != len(report.candidates) or any(
            left is not right
            for left, right in zip(flattened, report.candidates, strict=True)
        ):
            return False
        digest = sha256(b"veyra.observer-synthesis-v2.catalog.v1\0")
        for item in flattened:
            digest.update(len(item.canonical).to_bytes(8, "big"))
            digest.update(item.canonical)
        result = (
            report.canonical_bytes == sum(len(item.canonical) for item in flattened)
            and report.max_row_bytes == max(len(item.canonical) for item in flattened)
            and report.catalog_digest == digest.hexdigest()
        )
    except (AttributeError, TypeError, ValueError, RecursionError) as exc:
        logger.error("R14 catalog validation rejected error=%s", type(exc).__name__)
        return False
    logger.debug("verify_observer_grammar_enumeration_v2 exit result=%s", result)
    return result

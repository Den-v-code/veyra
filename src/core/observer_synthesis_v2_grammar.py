"""Exact dynamic-programming grammar for ordered closed R11 observers."""
from __future__ import annotations

from hashlib import sha256
import logging
from typing import NoReturn

from .observer_core_codec import canonical_observer_bytes
from .observer_core_semantics import infer_observer_kind
from .observer_core_types import (
    Apply,
    Input,
    LeafKind,
    ObserverExpr,
    Pair,
    PairKind,
    PrimitiveId,
    ResponseKind,
)
from .observer_synthesis_v2_budget import BudgetLedger
from .observer_synthesis_v2_catalog_provenance import _brand_catalog_v2, catalog_digest_v2
from .observer_synthesis_v2_types import (
    ObserverCandidateV2,
    ObserverGrammarEnumerationV2,
    ObserverGrammarStratumV2,
    ObserverGrammarV2,
)

logger = logging.getLogger(__name__)

GRAMMAR_SCHEMA = "veyra.observer-synthesis-v2.grammar.r14.1.v1"
DEFAULT_GRAMMAR_ID = "r11-ordered-tail-crest-pair-cost6-depth4"
DEFAULT_MAX_COST = 6
DEFAULT_MAX_DEPTH = 4
DEFAULT_CANDIDATE_LIMIT = 2048
DEFAULT_CANONICAL_BYTES_LIMIT = 8 * 1024 * 1024
EXPECTED_DEFAULT_STRATA = (1, 3, 8, 27, 104, 358, 1064)
EXPECTED_DEFAULT_CANDIDATES = 1565
EXPECTED_DEFAULT_CANONICAL_BYTES = 488_550
EXPECTED_DEFAULT_MAX_ROW_BYTES = 338
EXPECTED_DEFAULT_CATALOG_DIGEST = "23408184aba5d55d283e4a9440e1859beaefa9d73a909d283057d59b527437cf"
BOUNDARY = (
    "complete only for the exact ordered Input/TAIL/CREST/Pair R11 grammar "
    "within declared cost/depth limits; no synthesis, minimality, promotion, "
    "or arbitrary-observer completeness claim"
)

DEFAULT_GRAMMAR = ObserverGrammarV2(
    GRAMMAR_SCHEMA,
    DEFAULT_GRAMMAR_ID,
    DEFAULT_MAX_COST,
    DEFAULT_MAX_DEPTH,
    DEFAULT_CANDIDATE_LIMIT,
    DEFAULT_CANONICAL_BYTES_LIMIT,
)


class ObserverGrammarV2Error(ValueError):
    """Stable fail-closed grammar construction error."""


def _reject(reason: str) -> NoReturn:
    logger.error("observer_synthesis_v2_grammar rejected reason=%s", reason)
    raise ObserverGrammarV2Error(reason)


def _validate_grammar(grammar: object) -> ObserverGrammarV2:
    logger.debug("_validate_grammar entry type=%s", type(grammar).__name__)
    if type(grammar) is not ObserverGrammarV2:
        _reject("invalid-v2-grammar-type")
    texts = (grammar.schema, grammar.grammar_id)
    integers = (
        grammar.max_cost,
        grammar.max_depth,
        grammar.candidate_limit,
        grammar.canonical_bytes_limit,
    )
    if (
        any(type(item) is not str or not item for item in texts)
        or grammar.schema != GRAMMAR_SCHEMA
        or any(type(item) is not int or item < 0 for item in integers)
        or grammar.candidate_limit < 1
        or grammar.canonical_bytes_limit < 1
        or grammar.max_cost > DEFAULT_MAX_COST
        or grammar.max_depth > DEFAULT_MAX_DEPTH
        or grammar.candidate_limit > DEFAULT_CANDIDATE_LIMIT
        or grammar.canonical_bytes_limit > DEFAULT_CANONICAL_BYTES_LIMIT
    ):
        _reject("invalid-v2-grammar-limits")
    logger.debug(
        "_validate_grammar exit id=%s cost=%d depth=%d",
        grammar.grammar_id,
        grammar.max_cost,
        grammar.max_depth,
    )
    return grammar


def _candidate(
    observer: ObserverExpr,
    expected_kind: ResponseKind,
    cost: int,
    depth: int,
    ledger: BudgetLedger | None,
    grammar: ObserverGrammarV2,
    retained: int,
) -> ObserverCandidateV2:
    logger.debug(
        "_candidate entry type=%s cost=%d depth=%d",
        type(observer).__name__,
        cost,
        depth,
    )
    actual_kind = infer_observer_kind(observer)
    if actual_kind != expected_kind:
        _reject("v2-candidate-kind-mismatch")
    canonical = canonical_observer_bytes(observer)
    if len(canonical) > grammar.canonical_bytes_limit - retained:
        _reject("v2-canonical-bytes-limit")
    if ledger is not None:
        ledger.charge_candidate(len(canonical))
    result = ObserverCandidateV2(
        observer,
        actual_kind,
        cost,
        depth,
        canonical,
        sha256(canonical).hexdigest(),
    )
    logger.debug("_candidate exit digest=%s bytes=%d", result.digest[:12], len(canonical))
    return result


def _append_unique(
    rows: list[ObserverCandidateV2],
    candidate: ObserverCandidateV2,
    seen: set[bytes],
    grammar: ObserverGrammarV2,
    retained: int,
) -> int:
    logger.debug("_append_unique entry cost=%d retained=%d", candidate.cost, retained)
    if candidate.canonical in seen:
        _reject("duplicate-v2-observer-candidate")
    updated = retained + len(candidate.canonical)
    seen.add(candidate.canonical)
    rows.append(candidate)
    logger.debug("_append_unique exit candidates=%d retained=%d", len(seen), updated)
    return updated


def _require_candidate_slot(
    seen: set[bytes],
    grammar: ObserverGrammarV2,
) -> None:
    logger.debug("_require_candidate_slot entry candidates=%d", len(seen))
    if len(seen) >= grammar.candidate_limit:
        _reject("v2-candidate-limit")
    logger.debug("_require_candidate_slot exit")


def _build_cost_stratum(
    cost: int,
    buckets: list[list[ObserverCandidateV2]],
    grammar: ObserverGrammarV2,
    seen: set[bytes],
    retained: int,
    ledger: BudgetLedger | None,
) -> tuple[list[ObserverCandidateV2], int]:
    logger.debug("_build_cost_stratum entry cost=%d retained=%d", cost, retained)
    rows: list[ObserverCandidateV2] = []
    for child in buckets[cost - 1]:
        if child.response_kind is not LeafKind.RECURRENCE:
            continue
        depth = child.depth + 1
        if depth > grammar.max_depth:
            continue
        for primitive, kind in (
            (PrimitiveId.TAIL, LeafKind.RECURRENCE),
            (PrimitiveId.CREST, LeafKind.MARK),
        ):
            _require_candidate_slot(seen, grammar)
            retained = _append_unique(
                rows,
                _candidate(
                    Apply(primitive, child.observer),
                    kind,
                    cost,
                    depth,
                    ledger,
                    grammar,
                    retained,
                ),
                seen,
                grammar,
                retained,
            )
    for left_cost in range(cost):
        right_cost = cost - 1 - left_cost
        for left in buckets[left_cost]:
            for right in buckets[right_cost]:
                depth = 1 + max(left.depth, right.depth)
                if depth > grammar.max_depth:
                    continue
                pair_kind: ResponseKind = PairKind(left.response_kind, right.response_kind)
                _require_candidate_slot(seen, grammar)
                retained = _append_unique(
                    rows,
                    _candidate(
                        Pair(left.observer, right.observer),
                        pair_kind,
                        cost,
                        depth,
                        ledger,
                        grammar,
                        retained,
                    ),
                    seen,
                    grammar,
                    retained,
                )
    rows.sort(key=lambda item: (item.depth, item.canonical))
    logger.debug(
        "_build_cost_stratum exit cost=%d candidates=%d retained=%d",
        cost,
        len(rows),
        retained,
    )
    return rows, retained


def _verify_default_pins(report: ObserverGrammarEnumerationV2) -> None:
    logger.debug("_verify_default_pins entry candidates=%d", len(report.candidates))
    actual = (
        tuple(len(item.candidates) for item in report.strata),
        len(report.candidates),
        report.canonical_bytes,
        report.max_row_bytes,
        report.catalog_digest,
    )
    expected = (
        EXPECTED_DEFAULT_STRATA,
        EXPECTED_DEFAULT_CANDIDATES,
        EXPECTED_DEFAULT_CANONICAL_BYTES,
        EXPECTED_DEFAULT_MAX_ROW_BYTES,
        EXPECTED_DEFAULT_CATALOG_DIGEST,
    )
    if actual != expected:
        logger.error("default v2 grammar drift actual=%r expected=%r", actual, expected)
        _reject("default-v2-grammar-pin-mismatch")
    logger.debug("_verify_default_pins exit")


def enumerate_observer_grammar_v2(
    grammar: ObserverGrammarV2 = DEFAULT_GRAMMAR,
    *,
    ledger: BudgetLedger | None = None,
) -> ObserverGrammarEnumerationV2:
    """Enumerate the complete typed ordered grammar by exact cost strata."""
    logger.debug("enumerate_observer_grammar_v2 entry")
    valid = _validate_grammar(grammar)
    if ledger is not None and type(ledger) is not BudgetLedger:
        _reject("invalid-v2-grammar-ledger")
    seed = _candidate(Input(), LeafKind.RECURRENCE, 0, 0, ledger, valid, 0)
    buckets: list[list[ObserverCandidateV2]] = [[seed]]
    seen = {seed.canonical}
    retained = len(seed.canonical)
    for cost in range(1, valid.max_cost + 1):
        rows, retained = _build_cost_stratum(
            cost, buckets, valid, seen, retained, ledger
        )
        buckets.append(rows)
    strata = tuple(
        ObserverGrammarStratumV2(
            cost,
            tuple(rows),
            sum(len(item.canonical) for item in rows),
        )
        for cost, rows in enumerate(buckets)
    )
    candidates = tuple(item for stratum in strata for item in stratum.candidates)
    provisional = ObserverGrammarEnumerationV2(
        valid,
        strata,
        candidates,
        retained,
        max(len(item.canonical) for item in candidates),
        catalog_digest_v2(candidates),
        True,
        BOUNDARY,
    )
    result = _brand_catalog_v2(provisional, ledger)
    if valid == DEFAULT_GRAMMAR:
        _verify_default_pins(result)
    logger.debug(
        "enumerate_observer_grammar_v2 exit candidates=%d bytes=%d",
        len(result.candidates),
        result.canonical_bytes,
    )
    return result

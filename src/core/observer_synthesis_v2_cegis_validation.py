"""Trusted snapshot validation for R14.3b CEGIS inputs."""
from __future__ import annotations

import logging
from typing import NoReturn

from .observer_core_semantics import MAX_RECURRENCE_DEPTH, MAX_RECURRENCE_NODES
from .observer_synthesis_v2_corpus import MAX_CORPUS_CASES
from .observer_synthesis_v2_grammar import (
    DEFAULT_GRAMMAR,
    EXPECTED_DEFAULT_CANDIDATES,
    EXPECTED_DEFAULT_CANONICAL_BYTES,
    EXPECTED_DEFAULT_CATALOG_DIGEST,
)
from .observer_synthesis_v2_protocol import (
    ObserverCaseV2,
    ObserverSynthesisProtocolError,
    SplitId,
    build_observer_case_v2,
    validate_observer_case_v2,
)
from .observer_synthesis_v2_cegis_snapshot import (
    TrustedCegisCatalogSnapshotError,
    _trusted_cegis_catalog_snapshot_v2,
)
from .observer_synthesis_v2_types import (
    ObserverGrammarEnumerationV2,
    ObserverGrammarV2,
)
from .observer_synthesis_v2_validation import verify_observer_grammar_enumeration_v2
from .proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)


class InvalidCegisV2(ValueError):
    """Internal fail-closed input/evaluation rejection."""

    def __init__(self, reason: str) -> None:
        logger.debug("InvalidCegisV2.__init__ entry reason=%s", reason)
        self.reason = reason
        super().__init__(reason)
        logger.debug("InvalidCegisV2.__init__ exit")


def reject_cegis_v2(reason: str) -> NoReturn:
    logger.error("reject_cegis_v2 entry=error reason=%s", reason)
    raise InvalidCegisV2(reason)


def _trusted_recurrence(term: CoreTerm) -> CoreTerm:
    logger.debug("_trusted_recurrence entry type=%s", type(term).__name__)
    pulses = 0
    nodes = 0
    depth = 0
    seen: set[int] = set()
    node: object = term
    while True:
        nodes += 1
        identity = id(node)
        if (
            nodes > MAX_RECURRENCE_NODES
            or depth > MAX_RECURRENCE_DEPTH
            or identity in seen
        ):
            reject_cegis_v2("train-recurrence-resource-or-cycle")
        if type(node) is Silence:
            break
        if type(node) is not Pulse:
            reject_cegis_v2("train-recurrence-mutated")
        seen.add(identity)
        pulses += 1
        node = node.tail
        depth += 1
    trusted: CoreTerm = Silence()
    for _ in range(pulses):
        trusted = Pulse(trusted)
    logger.debug("_trusted_recurrence exit pulses=%d", pulses)
    return trusted


def _trusted_case(case: ObserverCaseV2) -> ObserverCaseV2:
    logger.debug("_trusted_case entry case_id=%d", case.case_id)
    headers = (
        case.case_id,
        case.group_id,
        case.split,
        case.expected,
        case.required_for_winner,
        case.payload_digest,
        case.clone_digest,
        case.case_digest,
    )
    trusted = build_observer_case_v2(
        headers[0],
        headers[1],
        headers[2],
        _trusted_recurrence(case.left),
        _trusted_recurrence(case.right),
        headers[3],
        headers[4],
    )
    if (
        trusted.payload_digest != headers[5]
        or trusted.clone_digest != headers[6]
        or trusted.case_digest != headers[7]
    ):
        reject_cegis_v2("train-case-mutated")
    logger.debug("_trusted_case exit case_id=%d", trusted.case_id)
    return trusted


def validate_cegis_catalog_v2(
    catalog: object,
    construction_ledger: object = None,
) -> ObserverGrammarEnumerationV2:
    """Validate one sealed catalog and return a separately branded snapshot."""
    logger.debug("validate_cegis_catalog_v2 entry type=%s", type(catalog).__name__)
    if type(catalog) is not ObserverGrammarEnumerationV2:
        reject_cegis_v2("invalid-exact-default-catalog")
    grammar = catalog.grammar
    scalar_shape = (
        type(grammar) is ObserverGrammarV2
        and type(catalog.strata) is tuple
        and type(catalog.candidates) is tuple
        and type(catalog.canonical_bytes) is int
        and type(catalog.max_row_bytes) is int
        and type(catalog.catalog_digest) is str
        and type(catalog.boundary) is str
        and catalog.complete is True
    )
    if not scalar_shape:
        reject_cegis_v2("invalid-exact-default-catalog")
    grammar_shape = (
        type(grammar.schema) is str
        and type(grammar.grammar_id) is str
        and type(grammar.max_cost) is int
        and type(grammar.max_depth) is int
        and type(grammar.candidate_limit) is int
        and type(grammar.canonical_bytes_limit) is int
    )
    if not grammar_shape:
        reject_cegis_v2("invalid-exact-default-catalog")
    exact_scalars = (
        grammar.schema == DEFAULT_GRAMMAR.schema
        and grammar.grammar_id == DEFAULT_GRAMMAR.grammar_id
        and grammar.max_cost == DEFAULT_GRAMMAR.max_cost
        and grammar.max_depth == DEFAULT_GRAMMAR.max_depth
        and grammar.candidate_limit == DEFAULT_GRAMMAR.candidate_limit
        and grammar.canonical_bytes_limit == DEFAULT_GRAMMAR.canonical_bytes_limit
        and len(catalog.candidates) == EXPECTED_DEFAULT_CANDIDATES
        and catalog.canonical_bytes == EXPECTED_DEFAULT_CANONICAL_BYTES
        and catalog.catalog_digest == EXPECTED_DEFAULT_CATALOG_DIGEST
    )
    if not exact_scalars or not verify_observer_grammar_enumeration_v2(
        catalog,
        construction_ledger,
    ):
        reject_cegis_v2("invalid-exact-default-catalog")
    try:
        trusted = _trusted_cegis_catalog_snapshot_v2(catalog, construction_ledger)
    except TrustedCegisCatalogSnapshotError:
        reject_cegis_v2("invalid-exact-default-catalog")
    logger.debug(
        "validate_cegis_catalog_v2 exit candidates=%d",
        len(trusted.candidates),
    )
    return trusted


def validate_cegis_train_cases_v2(
    train_cases: object,
) -> tuple[ObserverCaseV2, ...]:
    """Validate and deep-rebuild ordered TRAIN rows without shared terms."""
    logger.debug(
        "validate_cegis_train_cases_v2 entry type=%s",
        type(train_cases).__name__,
    )
    if (
        type(train_cases) is not tuple
        or not train_cases
        or len(train_cases) > MAX_CORPUS_CASES
    ):
        reject_cegis_v2("invalid-train-case-container")
    try:
        checked = tuple(validate_observer_case_v2(case) for case in train_cases)
        trusted = tuple(_trusted_case(case) for case in checked)
    except ObserverSynthesisProtocolError:
        reject_cegis_v2("invalid-train-case")
    ids = tuple(case.case_id for case in trusted)
    groups = tuple(case.group_id for case in trusted)
    payloads = tuple(case.payload_digest for case in trusted)
    clones = tuple(case.clone_digest for case in trusted)
    digests = tuple(case.case_digest for case in trusted)
    if (
        ids[0] != 101
        or ids != tuple(sorted(ids))
        or any(len(set(rows)) != len(rows) for rows in (ids, groups, payloads, clones, digests))
        or any(
            case.split is not SplitId.TRAIN or case.required_for_winner is not True
            for case in trusted
        )
    ):
        reject_cegis_v2("invalid-train-case-closure")
    logger.debug("validate_cegis_train_cases_v2 exit cases=%d", len(trusted))
    return trusted

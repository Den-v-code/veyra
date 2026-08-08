"""Fixed semantic replay for the five P1-D2 inference rows."""

from __future__ import annotations

import logging

from .productivity_counterpressure_basis import check_basis_source
from .productivity_counterpressure_digest import symbolic_formula_digest, symbol_tuple_digest
from .productivity_counterpressure_types import (
    BasisUse, CounterpressureEvidence, CounterpressureInference,
    CounterpressureOutcomeKind, CounterpressureRequest, CounterpressureStatus,
    DecreasingTreeRequest, DescentCountermodelEvidence,
    FiniteRunInsufficiencyEvidence, LedgerInsufficiencyEvidence, LongRunRequest,
    NonuniformLedgerRequest, ShrinkingStageRequest, ShrinkingTailCountermodelEvidence,
    TargetChooserRequest, TargetDependenceEvidence, ChooserTargetIndependence,
)

logger = logging.getLogger(__name__)
CHOOSER_RULE_ID = "read-target-and-copy-v1"
DESCENT_FORMULA_ID = "canonical-descending-fin-row-v1"


def replay_counterpressure(
    request: CounterpressureRequest,
) -> tuple[
    CounterpressureInference, CounterpressureOutcomeKind, CounterpressureStatus,
    CounterpressureEvidence, BasisUse, str | None,
]:
    """Derive one closed row; caller already performed representation preflight."""
    logger.debug("replay_counterpressure entry type=%s", type(request).__name__)
    if type(request) is NonuniformLedgerRequest:
        status = CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH
        evidence: CounterpressureEvidence = LedgerInsufficiencyEvidence(
            len(request.rows), tuple(row.depth for row in request.rows),
            len(frozenset(row.selector_label for row in request.rows)), False, status,
        )
        result = (
            CounterpressureInference.LEDGER_GENERATOR,
            CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY,
            status, evidence, BasisUse.NONE, None,
        )
    elif type(request) is DecreasingTreeRequest:
        basis = check_basis_source(request.basis)
        status = CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        first = None if request.sample_depth == 0 else request.sample_depth - 1
        last = None if request.sample_depth == 0 else 0
        evidence = DescentCountermodelEvidence(
            request.sample_depth, request.sample_depth, first, last,
            symbolic_formula_digest(DESCENT_FORMULA_ID, request.sample_depth),
            basis.basis_digest, status,
        )
        result = (
            CounterpressureInference.FINITE_DEPTH_BRANCH,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            status, evidence, BasisUse.BOUND, basis.basis_digest,
        )
    elif type(request) is TargetChooserRequest:
        status = CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        target = tuple(list(request.target))
        output = tuple(list(target))
        target_commitment = symbol_tuple_digest("chooser-sequence", target)
        output_commitment = symbol_tuple_digest("chooser-sequence", output)
        evidence = TargetDependenceEvidence(
            len(target), target_commitment, output_commitment, True, True,
            ChooserTargetIndependence.REFUTED, CHOOSER_RULE_ID, status,
        )
        result = (
            CounterpressureInference.POSTHOC_INDEPENDENCE,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            status, evidence, BasisUse.NONE, None,
        )
    elif type(request) is LongRunRequest:
        status = CounterpressureStatus.INSUFFICIENT_TO_ESTABLISH
        evidence = FiniteRunInsufficiencyEvidence(
            0, request.steps, request.steps + 1, False, status,
        )
        result = (
            CounterpressureInference.LONG_RUN_FAMILY,
            CounterpressureOutcomeKind.EVIDENCE_INSUFFICIENCY,
            status, evidence, BasisUse.NONE, None,
        )
    elif type(request) is ShrinkingStageRequest:
        basis = check_basis_source(request.basis)
        status = CounterpressureStatus.REFUTES_MATHEMATICAL_IMPLICATION
        n = request.sample_index
        evidence = ShrinkingTailCountermodelEvidence(
            n, n, n + 1, n, n, n + 1, basis.basis_digest, status,
        )
        result = (
            CounterpressureInference.NESTED_COMMON_POINT,
            CounterpressureOutcomeKind.MATHEMATICAL_COUNTERMODEL,
            status, evidence, BasisUse.BOUND, basis.basis_digest,
        )
    else:
        raise TypeError("unknown-counterpressure-request")
    logger.debug("replay_counterpressure exit inference=%s", result[0].value)
    return result

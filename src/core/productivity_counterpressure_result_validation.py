"""Hostile-safe fail-fast revalidation for P1-D2 results."""

from __future__ import annotations

import logging

from .productivity_counterpressure_common import exact_digest, reject
from .productivity_counterpressure_digest import (
    certificate_digest, evidence_digest, refusal_digest,
)
from .productivity_counterpressure_types import (
    CounterpressureCertificate, CounterpressurePolicy, CounterpressureRequest,
    CounterpressureResourceLimit, CounterpressureResult, DescentCountermodelEvidence,
    FiniteRunInsufficiencyEvidence, LedgerInsufficiencyEvidence,
    ShrinkingTailCountermodelEvidence, TargetDependenceEvidence,
)

logger = logging.getLogger(__name__)


def _exact_shape(value: object, expected_type: type, field: str) -> None:
    logger.debug("_exact_shape entry field=%s", field)
    if type(value) is not expected_type:
        reject(f"result-{field}-variant-drift")
    if set(vars(value)) != set(expected_type.__dataclass_fields__):
        reject(f"result-{field}-shape-drift")
    logger.debug("_exact_shape exit field=%s", field)


def _exact_enum(value: object, expected: object, field: str) -> None:
    logger.debug("_exact_enum entry field=%s", field)
    if type(value) is not type(expected) or value is not expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_enum exit field=%s", field)


def _exact_str(value: object, expected: str, field: str) -> None:
    logger.debug("_exact_str entry field=%s", field)
    if type(value) is not str or value != expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_str exit field=%s", field)


def _exact_int(value: object, expected: int, field: str) -> None:
    logger.debug("_exact_int entry field=%s", field)
    if type(value) is not int or value != expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_int exit field=%s", field)


def _exact_bool(value: object, expected: bool, field: str) -> None:
    logger.debug("_exact_bool entry field=%s", field)
    if type(value) is not bool or value is not expected:
        reject(f"result-{field}-drift")
    logger.debug("_exact_bool exit field=%s", field)


def _outer_permanent(value: object, expected: object) -> None:
    logger.debug("_outer_permanent entry")
    _exact_enum(value.generator_nonexistence, expected.generator_nonexistence, "generator")
    _exact_enum(value.all_depth_family, expected.all_depth_family, "all-depth")
    _exact_enum(value.completed_carrier, expected.completed_carrier, "carrier")
    _exact_enum(
        value.historical_target_independence,
        expected.historical_target_independence, "target-independence",
    )
    _exact_str(value.scope, expected.scope, "scope")
    logger.debug("_outer_permanent exit")


def _certificate_outer(
    value: CounterpressureCertificate, expected: CounterpressureCertificate,
) -> None:
    logger.debug("_certificate_outer entry")
    _exact_enum(value.request_kind, expected.request_kind, "request-kind")
    exact_digest(value.request_digest, "result-request-digest")
    _exact_str(value.request_digest, expected.request_digest, "request-digest")
    _exact_enum(value.inference_id, expected.inference_id, "inference")
    _exact_enum(value.outcome_kind, expected.outcome_kind, "outcome")
    _exact_enum(value.status, expected.status, "status")
    exact_digest(value.evidence_digest, "result-evidence-digest")
    _exact_str(value.evidence_digest, expected.evidence_digest, "evidence-digest")
    _exact_enum(value.basis_use, expected.basis_use, "basis-use")
    if expected.basis_digest is None:
        if value.basis_digest is not None:
            reject("result-basis-digest-drift")
    else:
        exact_digest(value.basis_digest, "result-basis-digest")
        _exact_str(value.basis_digest, expected.basis_digest, "basis-digest")
    exact_digest(value.policy_digest, "result-policy-digest")
    _exact_str(value.policy_digest, expected.policy_digest, "policy-digest")
    exact_digest(value.certificate_digest, "result-certificate-digest")
    _exact_str(value.certificate_digest, expected.certificate_digest, "certificate-digest")
    _outer_permanent(value, expected)
    if type(value.evidence) is not type(expected.evidence):
        reject("result-evidence-variant-drift")
    logger.debug("_certificate_outer exit")


def _validate_evidence(value: object, expected: object) -> None:
    logger.debug("_validate_evidence entry type=%s", type(value).__name__)
    if type(value) is LedgerInsufficiencyEvidence and type(expected) is LedgerInsufficiencyEvidence:
        _exact_int(value.row_count, expected.row_count, "row-count")
        if type(value.depths) is not tuple or len(value.depths) != len(expected.depths):
            reject("result-depths-shape-drift")
        for index, (actual, wanted) in enumerate(zip(value.depths, expected.depths, strict=True)):
            _exact_int(actual, wanted, f"depth-{index}")
        _exact_int(value.selector_count, expected.selector_count, "selector-count")
        _exact_bool(value.common_source_supplied, False, "common-source")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif type(value) is DescentCountermodelEvidence and type(expected) is DescentCountermodelEvidence:
        _exact_int(value.sample_depth, expected.sample_depth, "descent-sample")
        _exact_int(value.witness_length, expected.witness_length, "descent-length")
        _optional_int(value.first_or_none, expected.first_or_none, "descent-first")
        _optional_int(value.last_or_none, expected.last_or_none, "descent-last")
        exact_digest(value.witness_formula_digest, "result-formula-digest")
        _exact_str(value.witness_formula_digest, expected.witness_formula_digest, "formula")
        exact_digest(value.basis_digest, "result-evidence-basis-digest")
        _exact_str(value.basis_digest, expected.basis_digest, "evidence-basis")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif type(value) is TargetDependenceEvidence and type(expected) is TargetDependenceEvidence:
        _exact_int(value.target_length, expected.target_length, "target-length")
        exact_digest(value.target_digest, "result-target-digest")
        exact_digest(value.output_digest, "result-output-digest")
        _exact_str(value.target_digest, expected.target_digest, "target-digest")
        _exact_str(value.output_digest, expected.output_digest, "output-digest")
        _exact_bool(value.exact_match, True, "exact-match")
        _exact_bool(value.target_read, True, "target-read")
        _exact_enum(
            value.chooser_target_independence,
            expected.chooser_target_independence, "chooser-independence",
        )
        _exact_str(value.chooser_rule_id, expected.chooser_rule_id, "chooser-rule")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif (
        type(value) is FiniteRunInsufficiencyEvidence
        and type(expected) is FiniteRunInsufficiencyEvidence
    ):
        _exact_int(value.first_depth, 0, "run-first")
        _exact_int(value.last_depth, expected.last_depth, "run-last")
        _exact_int(value.executed_count, expected.executed_count, "run-count")
        _exact_bool(value.materialized, False, "materialized")
        _exact_enum(value.status, expected.status, "evidence-status")
    elif (
        type(value) is ShrinkingTailCountermodelEvidence
        and type(expected) is ShrinkingTailCountermodelEvidence
    ):
        for name in (
            "sample_index", "local_witness", "nested_from", "nested_into",
            "diagonal_candidate", "excluding_stage",
        ):
            _exact_int(getattr(value, name), getattr(expected, name), name)
        exact_digest(value.basis_digest, "result-evidence-basis-digest")
        _exact_str(value.basis_digest, expected.basis_digest, "evidence-basis")
        _exact_enum(value.status, expected.status, "evidence-status")
    else:
        reject("result-evidence-variant-drift")
    logger.debug("_validate_evidence exit")


def _optional_int(value: object, expected: int | None, field: str) -> None:
    logger.debug("_optional_int entry field=%s", field)
    if expected is None:
        if value is not None:
            reject(f"result-{field}-drift")
    else:
        _exact_int(value, expected, field)
    logger.debug("_optional_int exit field=%s", field)


def _validate_refusal(
    value: CounterpressureResourceLimit, expected: CounterpressureResourceLimit,
) -> None:
    logger.debug("_validate_refusal entry")
    _exact_enum(value.request_kind, expected.request_kind, "request-kind")
    exact_digest(value.request_digest, "result-request-digest")
    _exact_str(value.request_digest, expected.request_digest, "request-digest")
    _exact_enum(value.failed_bound, expected.failed_bound, "failed-bound")
    _exact_int(value.required_value, expected.required_value, "required")
    _exact_int(value.allowed_value, expected.allowed_value, "allowed")
    exact_digest(value.policy_digest, "result-policy-digest")
    _exact_str(value.policy_digest, expected.policy_digest, "policy-digest")
    exact_digest(value.refusal_digest, "result-refusal-digest")
    _exact_str(value.refusal_digest, expected.refusal_digest, "refusal-digest")
    _outer_permanent(value, expected)
    if refusal_digest(value) != value.refusal_digest:
        reject("result-refusal-commitment-drift")
    logger.debug("_validate_refusal exit")


def validate_counterpressure_result(
    value: CounterpressureResult, request: CounterpressureRequest,
    policy: CounterpressurePolicy,
) -> CounterpressureResult:
    """Rederive fixed semantics; accept no prior certificate as evidence."""
    logger.debug("validate_counterpressure_result entry")
    from .productivity_counterpressure_runtime import _derive_counterpressure_result
    expected = _derive_counterpressure_result(request, policy)
    if type(expected) is CounterpressureResourceLimit:
        _exact_shape(value, CounterpressureResourceLimit, "union")
        _validate_refusal(value, expected)
        logger.debug("validate_counterpressure_result exit refusal")
        return expected
    _exact_shape(value, CounterpressureCertificate, "union")
    _certificate_outer(value, expected)
    _exact_shape(value.evidence, type(expected.evidence), "evidence")
    _validate_evidence(value.evidence, expected.evidence)
    if evidence_digest(value.evidence) != value.evidence_digest:
        reject("result-evidence-commitment-drift")
    if certificate_digest(value) != value.certificate_digest:
        reject("result-certificate-commitment-drift")
    logger.debug("validate_counterpressure_result exit certificate")
    return expected

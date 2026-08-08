"""Nonpromoting finite candidate-law counterexample assessments for P1-D3."""

from __future__ import annotations

import logging

from .all_depth_family_common import exact_digest, exact_shape, reject
from .all_depth_family_counterexample_types import (
    CounterexampleLawVector, FamilyLaw, FamilyLawCounterexampleAssessment,
    FamilyNonexistence, FiniteFamilyLawWitness,
)
from .all_depth_family_counterexample_validation import (
    EVALUATOR_ID, WITNESS_VERSION, snapshot_family_law_witness, witness_refutes_law,
)
from .all_depth_family_digest import digest
from .all_depth_family_sources import snapshot_family_source
from .all_depth_family_spec import snapshot_family_spec
from .all_depth_family_types import (
    AllDepthFamilySpec, CompletedCarrierStatus, FamilyEvidenceStatus,
    FamilyIntroductionSource, LawStatus,
)

logger = logging.getLogger(__name__)


def _evaluator_digest() -> str:
    logger.debug("_evaluator_digest entry")
    result = digest("veyra.p1d3.law-evaluator.v1", (
        ("evaluator", EVALUATOR_ID.encode()), ("grammar", WITNESS_VERSION.encode()),
    ))
    logger.debug("_evaluator_digest exit")
    return result


def _law_vector(law: FamilyLaw) -> CounterexampleLawVector:
    logger.debug("_law_vector entry law=%s", law.value)
    values = {name: LawStatus.OPEN for name in CounterexampleLawVector.__dataclass_fields__}
    values[law.value.replace("-", "_")] = LawStatus.REFUTED
    result = CounterexampleLawVector(**values)
    logger.debug("_law_vector exit")
    return result


def _result_digest(
    spec: str, source: str, law: FamilyLaw, witness: str,
    evaluator: str, statuses: CounterexampleLawVector,
) -> str:
    logger.debug("_result_digest entry")
    result = digest("veyra.p1d3.law-counterexample-assessment.v1", (
        ("spec", spec.encode()), ("source", source.encode()),
        ("law", law.value.encode()), ("witness", witness.encode()),
        ("evaluator", evaluator.encode()),
        *((name, value.value.encode()) for name, value in vars(statuses).items()),
        ("family-evidence", FamilyEvidenceStatus.OPEN.value.encode()),
        ("family-nonexistence", FamilyNonexistence.NOT_PROVED.value.encode()),
        ("afip-introduction", b"false"),
        ("completed-carrier", CompletedCarrierStatus.NOT_ESTABLISHED.value.encode()),
        ("scope", b"finite-candidate-law-counterexample-no-afip-impact"),
    ))
    logger.debug("_result_digest exit")
    return result


def _assess_family_law_counterexample(
    spec: AllDepthFamilySpec, source: FamilyIntroductionSource,
    witness: FiniteFamilyLawWitness,
) -> FamilyLawCounterexampleAssessment:
    logger.debug("_assess_family_law_counterexample entry")
    spec = snapshot_family_spec(spec)
    source = snapshot_family_source(source)
    witness = snapshot_family_law_witness(witness)
    if source.spec != spec:
        reject("law-counterexample-spec-source-transplant")
    if not witness_refutes_law(witness):
        reject("witness-does-not-refute-law")
    evaluator = _evaluator_digest()
    statuses = _law_vector(witness.law)
    result = FamilyLawCounterexampleAssessment(
        spec.specification_digest, source.source_digest, witness.law,
        witness.witness_digest, EVALUATOR_ID, evaluator, LawStatus.REFUTED,
        statuses, _result_digest(
            spec.specification_digest, source.source_digest, witness.law,
            witness.witness_digest, evaluator, statuses,
        ),
    )
    logger.debug("_assess_family_law_counterexample exit")
    return result


def assess_family_law_counterexample(
    spec: AllDepthFamilySpec, source: FamilyIntroductionSource,
    witness: FiniteFamilyLawWitness,
) -> FamilyLawCounterexampleAssessment:
    """Assess one finite candidate law without changing AFIP family admission."""
    logger.debug("assess_family_law_counterexample entry")
    candidate = _assess_family_law_counterexample(spec, source, witness)
    result = validate_family_law_counterexample_assessment(spec, source, witness, candidate)
    logger.debug("assess_family_law_counterexample exit")
    return result


def validate_family_law_counterexample_assessment(
    spec: AllDepthFamilySpec, source: FamilyIntroductionSource,
    witness: FiniteFamilyLawWitness, value: FamilyLawCounterexampleAssessment,
) -> FamilyLawCounterexampleAssessment:
    """Validate every result field before fresh semantic recomputation."""
    logger.debug("validate_family_law_counterexample_assessment entry")
    exact_shape(value, FamilyLawCounterexampleAssessment, "law-counterexample-assessment")
    try:
        for name in (
            "specification_digest", "source_digest", "witness_digest",
            "evaluator_digest", "result_digest",
        ):
            exact_digest(getattr(value, name), name.replace("_", "-"))
        if type(value.law) is not FamilyLaw or type(value.affected_status) is not LawStatus:
            reject("law-assessment-enum-lookalike")
        if type(value.evaluator_id) is not str or value.evaluator_id != EVALUATOR_ID:
            reject("law-assessment-evaluator-drift")
        exact_shape(value.law_statuses, CounterexampleLawVector, "counterexample-law-vector")
        if any(type(item) is not LawStatus for item in vars(value.law_statuses).values()):
            reject("law-vector-status-lookalike")
        if (
            type(value.family_evidence) is not FamilyEvidenceStatus
            or type(value.family_nonexistence) is not FamilyNonexistence
            or type(value.afip_introduction) is not bool
            or type(value.completed_carrier) is not CompletedCarrierStatus
            or type(value.scope) is not str
        ):
            reject("law-assessment-permanent-field-lookalike")
    except AttributeError:
        reject("law-counterexample-assessment-missing-fields")
    expected = _assess_family_law_counterexample(spec, source, witness)
    if value != expected:
        reject("law-counterexample-assessment-semantic-drift")
    if (
        value.affected_status is not LawStatus.REFUTED
        or value.family_evidence is not FamilyEvidenceStatus.OPEN
        or value.family_nonexistence is not FamilyNonexistence.NOT_PROVED
        or value.afip_introduction is not False
        or value.completed_carrier is not CompletedCarrierStatus.NOT_ESTABLISHED
    ):
        reject("law-counterexample-assessment-promotion")
    statuses = vars(value.law_statuses)
    affected = value.law.value.replace("-", "_")
    if statuses[affected] is not LawStatus.REFUTED or any(
        status is not LawStatus.OPEN for name, status in statuses.items() if name != affected
    ):
        reject("law-counterexample-unrelated-status-drift")
    logger.debug("validate_family_law_counterexample_assessment exit")
    return expected

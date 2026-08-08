"""Fresh fail-fast revalidation of P1-D3 operational projections."""

from __future__ import annotations

import logging

from .all_depth_family_common import exact_digest, exact_shape, reject
from .all_depth_family_types import (
    CompletedCarrierStatus, FamilyIntroductionSource, FamilyProjectionArtifact,
    FamilyProjectionRefusal, FamilyProjectionResult, ProjectionResourceBound,
    ProjectionStatus,
)
from .productivity_types import ExecutionPolicy, PeriodicPrefixStage

logger = logging.getLogger(__name__)


def validate_family_projection(
    family_source: FamilyIntroductionSource, n: int, policy: ExecutionPolicy,
    value: FamilyProjectionResult,
) -> FamilyProjectionResult:
    """Recompute from source/depth/policy and reject forged union variants."""
    logger.debug("validate_family_projection entry")
    from .all_depth_family_projection import _project_family_stage
    expected = _project_family_stage(family_source, n, policy)
    if type(value) is not type(expected):
        reject("family-projection-union-variant-drift")
    if type(value) is FamilyProjectionArtifact:
        _validate_artifact(value)
    elif type(value) is FamilyProjectionRefusal:
        _validate_refusal(value)
    else:
        reject("unknown-family-projection-result")
    if value != expected:
        reject("family-projection-semantic-drift")
    logger.debug("validate_family_projection exit")
    return expected


def _validate_common(value) -> None:
    logger.debug("_validate_common entry")
    for field in (
        "source_digest", "family_term_digest", "introduction_evidence_digest",
        "policy_digest", "run_digest",
    ):
        exact_digest(getattr(value, field), field.replace("_", "-"))
    if type(value.completed_carrier) is not CompletedCarrierStatus:
        reject("projection-completed-carrier-lookalike")
    if type(value.scope) is not str:
        reject("invalid-projection-scope")
    logger.debug("_validate_common exit")


def _validate_artifact(value: FamilyProjectionArtifact) -> None:
    logger.debug("_validate_artifact entry")
    exact_shape(value, FamilyProjectionArtifact, "family-projection-artifact")
    _validate_common(value)
    if type(value.status) is not ProjectionStatus or value.status is not ProjectionStatus.CONSTRUCTED:
        reject("projection-artifact-status-drift")
    if type(value.depth) is not int or value.depth < 0:
        reject("projection-artifact-depth-drift")
    exact_shape(value.stage, PeriodicPrefixStage, "projected-stage")
    if (
        type(value.stage.depth) is not int or value.stage.depth != value.depth
        or type(value.stage.symbols) is not tuple
        or any(type(symbol) is not str for symbol in value.stage.symbols)
        or type(value.stage.output_encoding_id) is not str
    ):
        reject("projected-stage-shape-drift")
    exact_digest(value.output_digest, "output-digest")
    exact_digest(value.projection_digest, "projection-digest")
    logger.debug("_validate_artifact exit")


def _validate_refusal(value: FamilyProjectionRefusal) -> None:
    logger.debug("_validate_refusal entry")
    exact_shape(value, FamilyProjectionRefusal, "family-projection-refusal")
    _validate_common(value)
    if type(value.status) is not ProjectionStatus or value.status not in (
        ProjectionStatus.RESOURCE_LIMIT, ProjectionStatus.PROJECTION_UNAVAILABLE,
    ):
        reject("projection-refusal-status-drift")
    if type(value.requested_depth) is not int or value.requested_depth < 0:
        reject("projection-refusal-depth-drift")
    if value.status is ProjectionStatus.RESOURCE_LIMIT:
        if (
            type(value.failed_bound) is not ProjectionResourceBound
            or type(value.required_value) is not int or value.required_value < 0
            or type(value.allowed_value) is not int or value.allowed_value < 0
        ):
            reject("resource-refusal-payload-drift")
    elif any(item is not None for item in (
        value.failed_bound, value.required_value, value.allowed_value,
    )):
        reject("unavailable-refusal-resource-payload")
    exact_digest(value.refusal_digest, "refusal-digest")
    logger.debug("_validate_refusal exit")

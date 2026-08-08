"""Resource-bounded finite projection from admitted P1-D3 sources."""

from __future__ import annotations

import logging

from .all_depth_family_common import exact_natural, reject
from .all_depth_family_digest import projection_result_digest, projection_run_digest
from .all_depth_family_sources import snapshot_family_source
from .all_depth_family_types import (
    FamilyIntroductionSource, FamilyProjectionArtifact, FamilyProjectionRefusal,
    FamilyProjectionResult, ProjectionCapability, ProjectionResourceBound,
    ProjectionStatus,
)
from .productivity import (
    OUTPUT_ENCODING_ID, RESTRICTION_LAW_ID, TOTALITY_BASIS_ID,
    construct_at_depth, productive_process_source,
)
from .productivity_types import (
    ConstructionArtifact, ExecutionPolicy, ResourceBound, ResourceLimitResult,
)
from .productivity_validation import snapshot_execution_policy

logger = logging.getLogger(__name__)


def _result_fields(source, policy, run, depth, status):
    logger.debug("_result_fields entry status=%s", status.value)
    result = (
        ("source", source.source_digest.encode()),
        ("family", source.term.family_term_digest.encode()),
        ("introduction", source.introduction_evidence_digest.encode()),
        ("policy", policy.policy_digest.encode()), ("run", run.encode()),
        ("depth", depth.to_bytes(8, "big")), ("status", status.value.encode()),
    )
    logger.debug("_result_fields exit")
    return result


def _project_family_stage(
    family_source: FamilyIntroductionSource, n: int, policy: ExecutionPolicy,
) -> FamilyProjectionResult:
    logger.debug("_project_family_stage entry")
    source = snapshot_family_source(family_source)
    policy = snapshot_execution_policy(policy)
    n = exact_natural(n, "projection-depth", maximum=1_000_000)
    run = projection_run_digest(
        source.source_digest, source.term.family_term_digest,
        source.introduction_evidence_digest, policy.policy_digest, n,
    )
    if source.capability is not ProjectionCapability.PERIODIC_EXECUTABLE:
        status = ProjectionStatus.PROJECTION_UNAVAILABLE
        fields = _result_fields(source, policy, run, n, status) + (
            ("failed", b"none"), ("required", b"none"), ("allowed", b"none"),
        )
        result = FamilyProjectionRefusal(
            source.source_digest, source.term.family_term_digest,
            source.introduction_evidence_digest, policy.policy_digest, run, n,
            status, None, None, None, projection_result_digest(fields),
        )
        logger.debug("_project_family_stage exit unavailable")
        return result
    if source.term.program is None or source.generator_digest is None:
        reject("executable-family-capability-without-program")
    d1_source = productive_process_source(
        source.term.program, TOTALITY_BASIS_ID, RESTRICTION_LAW_ID,
        OUTPUT_ENCODING_ID, policy,
    )
    if d1_source.generator_digest != source.generator_digest:
        reject("projection-generator-transplant")
    d1_result = construct_at_depth(d1_source, n)
    if type(d1_result) is ResourceLimitResult:
        failed = (
            ProjectionResourceBound.DEPTH
            if d1_result.failed_bound is ResourceBound.DEPTH
            else ProjectionResourceBound.OUTPUT_BYTES
        )
        status = ProjectionStatus.RESOURCE_LIMIT
        fields = _result_fields(source, policy, run, n, status) + (
            ("failed", failed.value.encode()),
            ("required", d1_result.required_value.to_bytes(8, "big")),
            ("allowed", d1_result.allowed_value.to_bytes(8, "big")),
        )
        result = FamilyProjectionRefusal(
            source.source_digest, source.term.family_term_digest,
            source.introduction_evidence_digest, policy.policy_digest, run, n,
            status, failed, d1_result.required_value, d1_result.allowed_value,
            projection_result_digest(fields),
        )
        logger.debug("_project_family_stage exit resource-limit")
        return result
    if type(d1_result) is not ConstructionArtifact:
        reject("unexpected-d1-projection-result")
    stage = type(d1_result.stage)(
        d1_result.stage.depth, tuple(list(d1_result.stage.symbols)),
        d1_result.stage.output_encoding_id,
    )
    fields = _result_fields(source, policy, run, n, ProjectionStatus.CONSTRUCTED) + (
        ("output", d1_result.output_digest.encode()),
    )
    result = FamilyProjectionArtifact(
        source.source_digest, source.term.family_term_digest,
        source.introduction_evidence_digest, policy.policy_digest, run, n, stage,
        d1_result.output_digest, projection_result_digest(fields),
    )
    logger.debug("_project_family_stage exit constructed depth=%d", n)
    return result


def project_family_stage(
    family_source: FamilyIntroductionSource, n: int, policy: ExecutionPolicy,
) -> FamilyProjectionResult:
    """Project one demanded coordinate without changing family admission status."""
    logger.debug("project_family_stage entry")
    candidate = _project_family_stage(family_source, n, policy)
    from .all_depth_family_projection_validation import validate_family_projection
    result = validate_family_projection(family_source, n, policy, candidate)
    logger.debug("project_family_stage exit type=%s", type(result).__name__)
    return result

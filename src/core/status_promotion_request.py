"""Exact P2-S request DTO construction and hostile-safe snapshots."""

from __future__ import annotations

import logging

from .status_promotion_catalog import promotion_registry
from .status_promotion_common import (
    exact_digest, exact_identifier, exact_shape, exact_tuple, reject,
)
from .status_promotion_digest import digest, frame, nested_rows, text_rows
from .status_promotion_types import (
    AssumptionNode, ClaimDescriptor, EvidenceStatus, IndexBinding, JudgmentKind,
    PositiveProvenance, PromotionAuditRequest, PromotionRegistry,
)
from .status_promotion_validation import (
    REQUEST_VERSION, _enum, index_binding, validate_premise_artifact,
)

logger = logging.getLogger(__name__)


def assumption_node(
    assumption_id: str, claim_id: str, depends_on: tuple[str, ...], evidence_digest: str,
) -> AssumptionNode:
    logger.debug("assumption_node entry")
    exact_tuple(depends_on, "depends-on")
    dependencies = tuple(exact_identifier(item, "dependency-id") for item in depends_on)
    if len(set(dependencies)) != len(dependencies):
        reject("duplicate-dependency")
    result = AssumptionNode(
        exact_identifier(assumption_id, "assumption-id"),
        exact_identifier(claim_id, "assumption-claim-id"), dependencies,
        exact_digest(evidence_digest, "assumption-evidence-digest"),
    )
    logger.debug("assumption_node exit")
    return result


def claim_descriptor(
    claim_id: str, kind: JudgmentKind, status: EvidenceStatus,
    provenance: PositiveProvenance | None, indices: tuple[IndexBinding, ...],
    registry: PromotionRegistry | None = None,
) -> ClaimDescriptor:
    logger.debug("claim_descriptor entry")
    registry = promotion_registry() if registry is None else registry
    exact_tuple(indices, "descriptor-indices")
    _enum(kind, JudgmentKind, "descriptor-kind")
    _enum(status, EvidenceStatus, "descriptor-status")
    if provenance is not None:
        _enum(provenance, PositiveProvenance, "descriptor-provenance")
    checked = tuple(index_binding(item.name, item.value_digest) if (
        exact_shape(item, IndexBinding, "descriptor-index") is None
    ) else item for item in indices)
    if len({item.name for item in checked}) != len(checked):
        reject("duplicate-descriptor-index")
    _validate_pair(registry, kind, status, provenance)
    value = digest("veyra.p2s.claim-descriptor.v1", (
        ("claim-id", exact_identifier(claim_id, "claim-id").encode()),
        ("kind", kind.value.encode()), ("status", status.value.encode()),
        ("provenance", b"none" if provenance is None else provenance.value.encode()),
        *nested_rows("index", tuple(frame("veyra.p2s.index-binding.v1", (
            ("name", item.name.encode()), ("value", item.value_digest.encode()),
        )) for item in checked)),
    ))
    result = ClaimDescriptor(claim_id, kind, status, provenance, checked, value)
    logger.debug("claim_descriptor exit")
    return result


def _validate_pair(
    registry: PromotionRegistry, kind: JudgmentKind, status: EvidenceStatus,
    provenance: PositiveProvenance | None,
) -> None:
    logger.debug("_validate_pair entry")
    domains = tuple(item for item in registry.domains if item.kind is kind)
    if len(domains) != 1 or status not in domains[0].allowed_statuses:
        reject("status-outside-kind-domain")
    if status in (EvidenceStatus.OPEN, EvidenceStatus.REFUTED):
        if provenance is not None:
            reject("nonpositive-status-has-positive-provenance")
    elif provenance is None or not any(
        pair.status is status and pair.provenance is provenance
        for pair in domains[0].positive_pairs
    ):
        reject("invalid-positive-provenance-pair")
    logger.debug("_validate_pair exit")


def validate_claim_descriptor(
    value: object, registry: PromotionRegistry,
) -> ClaimDescriptor:
    logger.debug("validate_claim_descriptor entry")
    exact_shape(value, ClaimDescriptor, "claim-descriptor")
    exact_identifier(value.claim_id, "claim-id")
    _enum(value.kind, JudgmentKind, "descriptor-kind")
    _enum(value.status, EvidenceStatus, "descriptor-status")
    if value.provenance is not None:
        _enum(value.provenance, PositiveProvenance, "descriptor-provenance")
    exact_tuple(value.indices, "descriptor-indices")
    expected = claim_descriptor(
        value.claim_id, value.kind, value.status, value.provenance, value.indices, registry,
    )
    exact_digest(value.descriptor_digest, "descriptor-digest")
    if value != expected:
        reject("descriptor-digest-mismatch")
    logger.debug("validate_claim_descriptor exit")
    return value


def promotion_audit_request(
    rule_id: str, premises: tuple, assumptions: tuple[AssumptionNode, ...],
    conclusion: ClaimDescriptor, registry: PromotionRegistry | None = None,
) -> PromotionAuditRequest:
    logger.debug("promotion_audit_request entry")
    registry = promotion_registry() if registry is None else registry
    exact_tuple(premises, "request-premises")
    exact_tuple(assumptions, "request-assumptions")
    premise_values = tuple(validate_premise_artifact(item) for item in premises)
    assumption_values = tuple(validate_assumption_node(item) for item in assumptions)
    conclusion_value = validate_claim_descriptor(conclusion, registry)
    value = digest("veyra.p2s.audit-request.v1", (
        ("version", REQUEST_VERSION.encode()),
        ("rule-id", exact_identifier(rule_id, "rule-id").encode()),
        *nested_rows("premise", tuple(_premise_frame(item) for item in premise_values)),
        *nested_rows("assumption", tuple(_assumption_frame(item) for item in assumption_values)),
        ("conclusion", conclusion_value.descriptor_digest.encode()),
    ))
    result = PromotionAuditRequest(
        REQUEST_VERSION, rule_id, premise_values, assumption_values, conclusion_value, value,
    )
    logger.debug("promotion_audit_request exit")
    return result


def _premise_frame(item) -> bytes:
    logger.debug("_premise_frame entry premise=%s", item.premise_name)
    result = frame("veyra.p2s.premise-artifact.v1", (
        ("name", item.premise_name.encode()), ("kind", item.artifact_kind.encode()),
        ("artifact", item.artifact_digest.encode()),
        *nested_rows("index", tuple(frame("veyra.p2s.index-binding.v1", (
            ("name", binding.name.encode()), ("value", binding.value_digest.encode()),
        )) for binding in item.indices)),
        *nested_rows("evidence", tuple(frame("veyra.p2s.evidence-field.v1", (
            ("name", evidence.name.encode()),
            ("value", evidence.evidence_digest.encode()),
        )) for evidence in item.evidence_fields)),
    ))
    logger.debug("_premise_frame exit")
    return result


def _assumption_frame(item: AssumptionNode) -> bytes:
    logger.debug("_assumption_frame entry")
    result = frame("veyra.p2s.assumption.v1", (
        ("id", item.assumption_id.encode()), ("claim", item.claim_id.encode()),
        *text_rows("depends", item.depends_on), ("evidence", item.evidence_digest.encode()),
    ))
    logger.debug("_assumption_frame exit")
    return result


def validate_assumption_node(value: object) -> AssumptionNode:
    logger.debug("validate_assumption_node entry")
    exact_shape(value, AssumptionNode, "assumption-node")
    result = assumption_node(
        value.assumption_id, value.claim_id, value.depends_on, value.evidence_digest,
    )
    if value != result:
        reject("assumption-node-mismatch")
    logger.debug("validate_assumption_node exit")
    return value


def validate_request_shallow(value: object) -> PromotionAuditRequest:
    """Validate only the outer DTO and bounded containers before traversal."""
    logger.debug("validate_request_shallow entry")
    exact_shape(value, PromotionAuditRequest, "audit-request")
    exact_identifier(value.version, "request-version")
    exact_identifier(value.rule_id, "request-rule-id")
    exact_tuple(value.premises, "request-premises")
    exact_tuple(value.assumptions, "request-assumptions")
    exact_shape(value.conclusion, ClaimDescriptor, "request-conclusion")
    exact_digest(value.request_digest, "request-digest")
    logger.debug("validate_request_shallow exit")
    return value


def validate_request_deep(
    value: PromotionAuditRequest, registry: PromotionRegistry,
) -> PromotionAuditRequest:
    logger.debug("validate_request_deep entry")
    validate_request_shallow(value)
    expected = promotion_audit_request(
        value.rule_id, value.premises, value.assumptions, value.conclusion, registry,
    )
    if value != expected:
        reject("request-digest-mismatch")
    logger.debug("validate_request_deep exit")
    return value

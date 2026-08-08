"""Bounded named-promotion schema audit with assumption-DAG pressure."""

from __future__ import annotations

import logging

from .status_promotion_common import exact_digest, exact_identifier, exact_shape, exact_tuple, reject
from .status_promotion_digest import digest, text_rows
from .status_promotion_request import validate_request_deep, validate_request_shallow
from .status_promotion_types import (
    MetaAuditDecision, MetaOntologicalStatus, PromotionAuditPolicy,
    PromotionAuditRequest, PromotionAuditResult, PromotionRegistry,
    PromotionResourceLimit, PromotionRule, PromotionSchemaAudit, ResourceBound,
)
from .status_promotion_validation import validate_policy, validate_registry

logger = logging.getLogger(__name__)


def _resource(
    operation: str, request_digest: str, bound: ResourceBound,
    required: int, allowed: int, policy: PromotionAuditPolicy,
) -> PromotionResourceLimit:
    logger.debug("_resource entry bound=%s", bound.value)
    value = digest("veyra.p2s.resource-refusal.v1", (
        ("operation", operation.encode()), ("request", request_digest.encode()),
        ("bound", bound.value.encode()), ("required", required.to_bytes(8, "big")),
        ("allowed", allowed.to_bytes(8, "big")),
        ("policy", policy.policy_digest.encode()),
    ))
    result = PromotionResourceLimit(
        operation, request_digest, bound, required, allowed, policy.policy_digest, value,
    )
    logger.debug("_resource exit")
    return result


def audit_promotion_request(
    registry: PromotionRegistry, request: PromotionAuditRequest,
    policy: PromotionAuditPolicy,
) -> PromotionAuditResult:
    """Audit exact rule syntax; never establish the rule conclusion itself."""
    logger.debug("audit_promotion_request entry")
    validate_registry(registry)
    validate_policy(policy)
    validate_request_shallow(request)
    if len(request.premises) > policy.max_premises:
        return _resource(
            "promotion-audit", request.request_digest, ResourceBound.PREMISE_COUNT,
            len(request.premises), policy.max_premises, policy,
        )
    if len(request.assumptions) > policy.max_assumptions:
        return _resource(
            "promotion-audit", request.request_digest, ResourceBound.ASSUMPTION_COUNT,
            len(request.assumptions), policy.max_assumptions, policy,
        )
    validate_request_deep(request, registry)
    fields = sum(len(item.indices) + len(item.evidence_fields) for item in request.premises)
    fields += len(request.conclusion.indices)
    if fields > policy.max_fields:
        return _resource(
            "promotion-audit", request.request_digest, ResourceBound.FIELD_COUNT,
            fields, policy.max_fields, policy,
        )
    rules = tuple(item for item in registry.rules if item.rule_id == request.rule_id)
    if len(rules) != 1:
        reject("unknown-or-duplicate-promotion-rule")
    result = _audit_rule(registry, rules[0], request, policy)
    logger.debug("audit_promotion_request exit decision=%s", result.decision.value)
    return result


def _audit_rule(
    registry: PromotionRegistry, rule: PromotionRule, request: PromotionAuditRequest,
    policy: PromotionAuditPolicy,
) -> PromotionSchemaAudit:
    logger.debug("_audit_rule entry rule=%s", rule.rule_id)
    conclusion = request.conclusion
    if (
        conclusion.kind is not rule.output_kind
        or conclusion.status is not rule.output_status
        or conclusion.provenance is not rule.output_provenance
    ):
        reject("conclusion-does-not-match-named-rule")
    if tuple(item.name for item in conclusion.indices) != rule.output_indices:
        reject("conclusion-indices-not-exact")
    if len(request.premises) != len(rule.premise_signatures):
        reject("premise-count-not-exact")
    for artifact, signature in zip(request.premises, rule.premise_signatures):
        if artifact.artifact_kind in rule.forbidden_source_types:
            reject("forbidden-promotion-source")
        if artifact.premise_name != signature.premise_name:
            reject("premise-name-not-exact")
        if artifact.artifact_kind != signature.artifact_kind:
            reject("premise-artifact-kind-not-exact")
        if tuple(item.name for item in artifact.indices) != signature.required_indices:
            reject("premise-indices-not-exact")
        if tuple(item.name for item in artifact.evidence_fields) != (
            signature.required_evidence_fields
        ):
            reject("premise-evidence-fields-not-exact")
    closure = _assumption_closure(request)
    value = digest("veyra.p2s.schema-audit.v1", (
        ("registry", registry.registry_digest.encode()),
        ("rule", rule.rule_digest.encode()),
        ("request", request.request_digest.encode()),
        ("policy", policy.policy_digest.encode()),
        ("conclusion", conclusion.descriptor_digest.encode()),
        *text_rows("premise", tuple(item.artifact_digest for item in request.premises)),
        *text_rows("assumption", closure), *text_rows("nonclaim", rule.permanent_nonclaims),
        ("decision", MetaAuditDecision.SCHEMA_CONFORMANT.value.encode()),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = PromotionSchemaAudit(
        registry.registry_digest, rule.rule_digest, request.request_digest,
        policy.policy_digest, conclusion, request.premises, closure,
        rule.permanent_nonclaims, MetaAuditDecision.SCHEMA_CONFORMANT, value,
    )
    logger.debug("_audit_rule exit")
    return result


def _assumption_closure(request: PromotionAuditRequest) -> tuple[str, ...]:
    logger.debug("_assumption_closure entry rows=%d", len(request.assumptions))
    nodes = {item.assumption_id: item for item in request.assumptions}
    if len(nodes) != len(request.assumptions):
        reject("duplicate-assumption-id")
    for item in request.assumptions:
        if item.claim_id == request.conclusion.claim_id:
            reject("conclusion-in-assumption-closure")
        if any(dependency not in nodes for dependency in item.depends_on):
            reject("missing-assumption-dependency")
    visiting: set[str] = set()
    visited: set[str] = set()
    ordered: list[str] = []

    def visit(node_id: str) -> None:
        logger.debug("visit entry node=%s", node_id)
        if node_id in visiting:
            reject("cyclic-assumption-dag")
        if node_id not in visited:
            visiting.add(node_id)
            for dependency in nodes[node_id].depends_on:
                visit(dependency)
            visiting.remove(node_id)
            visited.add(node_id)
            ordered.append(node_id)
        logger.debug("visit exit node=%s", node_id)

    for node in request.assumptions:
        visit(node.assumption_id)
    result = tuple(ordered)
    logger.debug("_assumption_closure exit rows=%d", len(result))
    return result


def validate_schema_audit(
    value: object, registry: PromotionRegistry, request: PromotionAuditRequest,
    policy: PromotionAuditPolicy,
) -> PromotionSchemaAudit:
    """Freshly replay and compare an exact successful audit DTO."""
    logger.debug("validate_schema_audit entry")
    exact_shape(value, PromotionSchemaAudit, "promotion-schema-audit")
    for name in (
        "registry_digest", "rule_digest", "request_digest", "policy_digest", "audit_digest",
    ):
        exact_digest(getattr(value, name), f"audit-{name}")
    validate_request_deep(request, registry)
    from .status_promotion_request import validate_claim_descriptor
    from .status_promotion_validation import validate_premise_artifact
    validate_claim_descriptor(value.conclusion, registry)
    exact_tuple(value.premise_artifacts, "audit-premise-artifacts")
    for artifact in value.premise_artifacts:
        validate_premise_artifact(artifact)
    exact_tuple(value.assumption_closure, "audit-assumption-closure")
    exact_tuple(value.nonclaims, "audit-nonclaims")
    for item in value.assumption_closure:
        exact_identifier(item, "audit-assumption-id")
    for item in value.nonclaims:
        exact_identifier(item, "audit-nonclaim")
    if type(value.decision) is not MetaAuditDecision:
        reject("invalid-audit-decision")
    if type(value.ontological_establishment) is not MetaOntologicalStatus:
        reject("invalid-audit-ontology-status")
    exact_identifier(value.scope, "audit-scope")
    expected = audit_promotion_request(registry, request, policy)
    if type(expected) is not PromotionSchemaAudit or value != expected:
        reject("promotion-schema-audit-not-fresh")
    logger.debug("validate_schema_audit exit")
    return value

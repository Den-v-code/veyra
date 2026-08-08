"""Hostile-safe builders and exact snapshots for the P2-S calculus."""

from __future__ import annotations

import logging

from .status_promotion_catalog import promotion_registry
from .status_promotion_common import (
    exact_digest, exact_identifier, exact_natural, exact_shape,
    exact_tuple, reject,
)
from .status_promotion_digest import digest
from .status_promotion_types import (
    EvidenceField, EvidenceStatus, IndexBinding,
    JudgmentKind, PositiveProvenance, PremiseArtifact, PromotionAuditPolicy,
    PromotionRegistry,
)

logger = logging.getLogger(__name__)
REQUEST_VERSION = "p2-s-promotion-request-v1"
POLICY_VERSION = "p2-s-promotion-policy-v1"


def _enum(value: object, enum_type: type, field: str):
    logger.debug("_enum entry field=%s", field)
    if type(value) is not enum_type:
        reject(f"invalid-{field}")
    logger.debug("_enum exit field=%s", field)
    return value


def _names(values: tuple, field: str) -> tuple[str, ...]:
    logger.debug("_names entry field=%s", field)
    exact_tuple(values, field)
    result = tuple(exact_identifier(value, f"{field}-member") for value in values)
    if len(set(result)) != len(result):
        reject(f"duplicate-{field}")
    logger.debug("_names exit field=%s", field)
    return result


def validate_registry(value: object) -> PromotionRegistry:
    """Validate every bounded registry cell before canonical equality."""
    logger.debug("validate_registry entry")
    exact_shape(value, PromotionRegistry, "registry")
    exact_identifier(value.version, "registry-version")
    for field_name in (
        "domains", "rules", "premise_projections", "index_projections", "schema_targets",
    ):
        exact_tuple(getattr(value, field_name), f"registry-{field_name}")
    exact_digest(value.registry_digest, "registry-digest")
    for domain in value.domains:
        from .status_promotion_types import KindStatusDomain, StatusProvenancePair
        exact_shape(domain, KindStatusDomain, "domain")
        _enum(domain.kind, JudgmentKind, "domain-kind")
        exact_tuple(domain.allowed_statuses, "allowed-statuses")
        exact_tuple(domain.positive_pairs, "positive-pairs")
        for status in domain.allowed_statuses:
            _enum(status, EvidenceStatus, "allowed-status")
        for pair in domain.positive_pairs:
            exact_shape(pair, StatusProvenancePair, "status-provenance-pair")
            _enum(pair.status, EvidenceStatus, "pair-status")
            _enum(pair.provenance, PositiveProvenance, "pair-provenance")
        exact_digest(domain.domain_digest, "domain-digest")
    _validate_rule_rows(value)
    _validate_projection_rows(value)
    _validate_schema_rows(value)
    if value != promotion_registry():
        reject("registry-not-canonical")
    logger.debug("validate_registry exit")
    return value


def _validate_rule_rows(value: PromotionRegistry) -> None:
    logger.debug("_validate_rule_rows entry")
    from .status_promotion_types import PremiseSignature, PromotionRule
    for rule in value.rules:
        exact_shape(rule, PromotionRule, "promotion-rule")
        exact_identifier(rule.rule_id, "rule-id")
        exact_digest(rule.statement_digest, "statement-digest")
        exact_tuple(rule.premise_signatures, "premise-signatures", nonempty=True)
        for premise in rule.premise_signatures:
            exact_shape(premise, PremiseSignature, "premise-signature")
            exact_identifier(premise.premise_name, "premise-name")
            exact_identifier(premise.artifact_kind, "artifact-kind")
            _names(premise.required_evidence_fields, "required-evidence-fields")
            _names(premise.required_indices, "required-indices")
        _enum(rule.output_kind, JudgmentKind, "output-kind")
        _enum(rule.output_status, EvidenceStatus, "output-status")
        _enum(rule.output_provenance, PositiveProvenance, "output-provenance")
        _names(rule.output_indices, "output-indices")
        _names(rule.forbidden_source_types, "forbidden-source-types")
        _names(rule.forbidden_conclusion_fields, "forbidden-conclusion-fields")
        exact_identifier(rule.assumption_policy_id, "assumption-policy-id")
        _names(rule.permanent_nonclaims, "permanent-nonclaims")
        exact_digest(rule.rule_digest, "rule-digest")
    logger.debug("_validate_rule_rows exit")


def _validate_projection_rows(value: PromotionRegistry) -> None:
    logger.debug("_validate_projection_rows entry")
    from .status_promotion_types import IndexProjectionRule, PremiseProjectionRule
    for item in value.premise_projections:
        exact_shape(item, PremiseProjectionRule, "premise-projection-rule")
        exact_identifier(item.projection_id, "projection-id")
        exact_identifier(item.source_rule_id, "source-rule-id")
        exact_identifier(item.premise_name, "projection-premise-name")
        exact_digest(item.projection_digest, "projection-digest")
    for item in value.index_projections:
        exact_shape(item, IndexProjectionRule, "index-projection-rule")
        exact_identifier(item.projection_id, "projection-id")
        _enum(item.kind, JudgmentKind, "projection-kind")
        _names(item.input_indices, "projection-input-indices")
        exact_identifier(item.hidden_index, "hidden-index")
        _names(item.retained_indices, "retained-indices")
        exact_digest(item.projection_digest, "projection-digest")
    logger.debug("_validate_projection_rows exit")


def _validate_schema_rows(value: PromotionRegistry) -> None:
    logger.debug("_validate_schema_rows entry")
    from .status_promotion_types import SchemaTarget
    for item in value.schema_targets:
        exact_shape(item, SchemaTarget, "schema-target")
        exact_identifier(item.schema_id, "schema-id")
        _names(item.exact_fields, "schema-fields")
        _names(item.forbidden_positive_fields, "schema-forbidden-fields")
        exact_digest(item.schema_digest, "schema-digest")
    logger.debug("_validate_schema_rows exit")


def promotion_policy(
    max_premises: int = 64, max_assumptions: int = 64,
    max_fields: int = 256, max_schemas: int = 16,
) -> PromotionAuditPolicy:
    logger.debug("promotion_policy entry")
    values = tuple(exact_natural(value, name) for name, value in (
        ("max-premises", max_premises), ("max-assumptions", max_assumptions),
        ("max-fields", max_fields), ("max-schemas", max_schemas),
    ))
    value = digest("veyra.p2s.policy.v1", (
        ("version", POLICY_VERSION.encode()),
        *tuple((name, number.to_bytes(8, "big")) for name, number in zip(
            ("max-premises", "max-assumptions", "max-fields", "max-schemas"), values)),
    ))
    result = PromotionAuditPolicy(POLICY_VERSION, *values, value)
    logger.debug("promotion_policy exit")
    return result


DEFAULT_POLICY = promotion_policy()


def validate_policy(value: object) -> PromotionAuditPolicy:
    logger.debug("validate_policy entry")
    exact_shape(value, PromotionAuditPolicy, "policy")
    exact_identifier(value.version, "policy-version")
    for name in ("max_premises", "max_assumptions", "max_fields", "max_schemas"):
        exact_natural(getattr(value, name), name)
    exact_digest(value.policy_digest, "policy-digest")
    expected = promotion_policy(
        value.max_premises, value.max_assumptions, value.max_fields, value.max_schemas,
    )
    if value != expected:
        reject("policy-digest-mismatch")
    logger.debug("validate_policy exit")
    return value


def index_binding(name: str, value_digest: str) -> IndexBinding:
    logger.debug("index_binding entry")
    result = IndexBinding(exact_identifier(name, "index-name"), exact_digest(
        value_digest, "index-value-digest"))
    logger.debug("index_binding exit")
    return result


def evidence_field(name: str, evidence_digest: str) -> EvidenceField:
    logger.debug("evidence_field entry")
    result = EvidenceField(exact_identifier(name, "evidence-name"), exact_digest(
        evidence_digest, "evidence-digest"))
    logger.debug("evidence_field exit")
    return result


def premise_artifact(
    premise_name: str, artifact_kind: str, artifact_digest: str,
    indices: tuple[IndexBinding, ...], evidence_fields: tuple[EvidenceField, ...],
) -> PremiseArtifact:
    logger.debug("premise_artifact entry")
    exact_tuple(indices, "artifact-indices")
    exact_tuple(evidence_fields, "artifact-evidence", nonempty=True)
    result = PremiseArtifact(
        exact_identifier(premise_name, "premise-name"),
        exact_identifier(artifact_kind, "artifact-kind"),
        exact_digest(artifact_digest, "artifact-digest"), indices, evidence_fields,
    )
    validate_premise_artifact(result)
    logger.debug("premise_artifact exit")
    return result


def validate_premise_artifact(value: object) -> PremiseArtifact:
    logger.debug("validate_premise_artifact entry")
    exact_shape(value, PremiseArtifact, "premise-artifact")
    exact_identifier(value.premise_name, "premise-name")
    exact_identifier(value.artifact_kind, "artifact-kind")
    exact_digest(value.artifact_digest, "artifact-digest")
    exact_tuple(value.indices, "artifact-indices")
    exact_tuple(value.evidence_fields, "artifact-evidence", nonempty=True)
    for item in value.indices:
        exact_shape(item, IndexBinding, "index-binding")
        index_binding(item.name, item.value_digest)
    for item in value.evidence_fields:
        exact_shape(item, EvidenceField, "evidence-field")
        evidence_field(item.name, item.evidence_digest)
    if len({item.name for item in value.indices}) != len(value.indices):
        reject("duplicate-artifact-index")
    if len({item.name for item in value.evidence_fields}) != len(value.evidence_fields):
        reject("duplicate-evidence-field")
    logger.debug("validate_premise_artifact exit")
    return value

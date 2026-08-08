"""Named premise and index projections for P2-S elimination."""

from __future__ import annotations

import logging

from .status_promotion_common import exact_bool, exact_digest, exact_shape, exact_tuple, reject
from .status_promotion_digest import digest, text_rows
from .status_promotion_request import validate_claim_descriptor
from .status_promotion_runtime import validate_schema_audit
from .status_promotion_types import (
    ClaimDescriptor, IndexBinding, IndexProjection, MetaOntologicalStatus, PremiseProjection,
    PromotionAuditPolicy, PromotionAuditRequest, PromotionRegistry,
    PromotionSchemaAudit,
)
from .status_promotion_validation import validate_registry
from .status_promotion_validation import index_binding

logger = logging.getLogger(__name__)


def project_premise_artifact(
    registry: PromotionRegistry, request: PromotionAuditRequest,
    audit: PromotionSchemaAudit, projection_id: str, policy: PromotionAuditPolicy,
) -> PremiseProjection:
    """Return the original premise artifact through an explicit named rule."""
    logger.debug("project_premise_artifact entry projection=%s", projection_id)
    validate_registry(registry)
    validate_schema_audit(audit, registry, request, policy)
    rules = tuple(item for item in registry.premise_projections if (
        item.projection_id == projection_id
    ))
    if len(rules) != 1 or rules[0].source_rule_id != request.rule_id:
        reject("invalid-premise-projection-rule")
    artifacts = tuple(item for item in request.premises if (
        item.premise_name == rules[0].premise_name
    ))
    if len(artifacts) != 1:
        reject("projected-premise-not-exact")
    value = digest("veyra.p2s.premise-projection.v1", (
        ("rule", rules[0].projection_digest.encode()),
        ("audit", audit.audit_digest.encode()),
        ("artifact", artifacts[0].artifact_digest.encode()),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = PremiseProjection(
        rules[0].projection_digest, audit.audit_digest, artifacts[0], value,
    )
    logger.debug("project_premise_artifact exit")
    return result


def project_index_existential(
    registry: PromotionRegistry, descriptor: ClaimDescriptor, projection_id: str,
) -> IndexProjection:
    """Hide exactly one named index while retaining an auditable binding."""
    logger.debug("project_index_existential entry projection=%s", projection_id)
    validate_registry(registry)
    validate_claim_descriptor(descriptor, registry)
    rules = tuple(item for item in registry.index_projections if (
        item.projection_id == projection_id
    ))
    if len(rules) != 1 or descriptor.kind is not rules[0].kind:
        reject("invalid-index-projection-rule")
    names = tuple(item.name for item in descriptor.indices)
    if names != rules[0].input_indices:
        reject("index-projection-input-not-exact")
    hidden = tuple(item for item in descriptor.indices if item.name == rules[0].hidden_index)
    retained = tuple(item for item in descriptor.indices if item.name in rules[0].retained_indices)
    if len(hidden) != 1 or tuple(item.name for item in retained) != rules[0].retained_indices:
        reject("index-projection-loss-not-named")
    value = digest("veyra.p2s.index-projection.v1", (
        ("rule", rules[0].projection_digest.encode()),
        ("source", descriptor.descriptor_digest.encode()),
        *text_rows("retained", tuple(item.value_digest for item in retained)),
        ("hidden-name", hidden[0].name.encode()),
        ("hidden-value", hidden[0].value_digest.encode()),
        ("existential", b"true"),
        ("ontology", MetaOntologicalStatus.NOT_CLAIMED.value.encode()),
    ))
    result = IndexProjection(
        rules[0].projection_digest, descriptor, retained, hidden[0], True, value,
    )
    logger.debug("project_index_existential exit")
    return result


def validate_index_projection(
    value: object, registry: PromotionRegistry, projection_id: str,
) -> IndexProjection:
    logger.debug("validate_index_projection entry")
    exact_shape(value, IndexProjection, "index-projection")
    exact_digest(value.projection_rule_digest, "index-projection-rule-digest")
    validate_claim_descriptor(value.source_descriptor, registry)
    exact_tuple(value.retained_indices, "index-projection-retained")
    for item in value.retained_indices:
        exact_shape(item, IndexBinding, "retained-index")
        index_binding(item.name, item.value_digest)
    exact_shape(value.hidden_binding, IndexBinding, "hidden-binding")
    index_binding(value.hidden_binding.name, value.hidden_binding.value_digest)
    exact_bool(value.existential, "projection-existential")
    exact_digest(value.projection_digest, "index-projection-digest")
    if type(value.ontological_establishment) is not MetaOntologicalStatus:
        reject("invalid-index-projection-ontology-status")
    expected = project_index_existential(registry, value.source_descriptor, projection_id)
    if value != expected:
        reject("index-projection-not-fresh")
    logger.debug("validate_index_projection exit")
    return value

"""Narrow public facade for the P2-S status/promotion meta-calculus."""

from .status_promotion_attacks import adjacent_cast_attack_matrix
from .status_promotion_common import (
    StatusPromotionValidationError as StatusPromotionValidationError,
)
from .status_promotion_catalog import (
    ASSUMPTION_POLICY_ID, FORBIDDEN_CONCLUSION_FIELDS, FORBIDDEN_SOURCE_TYPES,
    NONCLAIMS, REGISTRY_VERSION, promotion_registry,
)
from .status_promotion_projection import (
    project_index_existential, project_premise_artifact, validate_index_projection,
)
from .status_promotion_oracle import (
    LITERAL_ORACLE_DIGEST, audit_registry_against_literal_oracle,
)
from .status_promotion_request import (
    assumption_node, claim_descriptor, promotion_audit_request,
    validate_claim_descriptor, validate_request_deep, validate_request_shallow,
)
from .status_promotion_runtime import audit_promotion_request, validate_schema_audit
from .status_promotion_schema_audit import (
    SCHEMA_AUDIT_NONCLAIMS, SCHEMA_AUDIT_SCOPE, audit_allowlisted_schemas,
    validate_schema_audit_report,
)
from .status_promotion_types import *  # noqa: F403
from .status_promotion_validation import (
    DEFAULT_POLICY, evidence_field, index_binding, premise_artifact,
    promotion_policy, validate_policy, validate_premise_artifact, validate_registry,
)

__all__ = (
    "ASSUMPTION_POLICY_ID", "DEFAULT_POLICY", "FORBIDDEN_CONCLUSION_FIELDS",
    "FORBIDDEN_SOURCE_TYPES", "LITERAL_ORACLE_DIGEST", "NONCLAIMS", "REGISTRY_VERSION",
    "SCHEMA_AUDIT_NONCLAIMS", "SCHEMA_AUDIT_SCOPE",
    "adjacent_cast_attack_matrix", "assumption_node", "audit_allowlisted_schemas",
    "audit_registry_against_literal_oracle",
    "audit_promotion_request", "claim_descriptor", "evidence_field", "index_binding",
    "premise_artifact", "project_index_existential", "project_premise_artifact",
    "promotion_audit_request", "promotion_policy", "promotion_registry",
    "validate_claim_descriptor", "validate_index_projection", "validate_policy",
    "validate_premise_artifact", "validate_registry", "validate_request_deep",
    "validate_request_shallow", "validate_schema_audit", "validate_schema_audit_report",
    "StatusPromotionValidationError",
)

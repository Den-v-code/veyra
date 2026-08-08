"""Closed DTO grammar for the P2-S status/promotion meta-calculus."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

class JudgmentKind(str, Enum):
    PRESENTED = "presented"
    ADMISSIBLE = "admissible"
    OBSERVABLE = "observable"
    GENERABLE = "generable"
    COHERENT = "coherent"
    PERSISTENT = "persistent"
    CONFLUENT = "confluent"
    REFINEMENT_ROBUST = "refinement-robust"
    OBSERVER_ROLE = "observer-role"
    HISTORICALLY_ACTUALIZED = "historically-actualized"
    SCOPED_OBJECT = "scoped-object"
    ALL_DEPTH_FAMILY = "all-depth-family"
    COMPLETED_CARRIER = "completed-carrier"
    OBJECTIVELY_STABLE = "objectively-stable"
    PHYSICALLY_INSTANTIATED = "physically-instantiated"


class EvidenceStatus(str, Enum):
    ESTABLISHED = "established"
    ESTABLISHED_RELATIVE_TO_DOCTRINE = "established-relative-to-doctrine"
    ESTABLISHED_RELATIVE_TO_SCOPE = "established-relative-to-scope"
    ESTABLISHED_RELATIVE_TO_HISTORY = "established-relative-to-history"
    ESTABLISHED_RELATIVE_TO_FORMATION_SCOPE = "established-relative-to-formation-scope"
    ESTABLISHED_RELATIVE_TO_LEDGER = "established-relative-to-ledger"
    ESTABLISHED_RELATIVE_TO_NETWORK = "established-relative-to-network"
    ESTABLISHED_RELATIVE_TO_EMPIRICAL_BRIDGE = "established-relative-to-empirical-bridge"
    ASSUMED = "assumed"
    REFUTED = "refuted"
    OPEN = "open"
    NOT_ESTABLISHED = "not-established"
    NOT_CLAIMED = "not-claimed"


class PositiveProvenance(str, Enum):
    SUPPLIED_PRESENTATION = "supplied-presentation"
    DOCTRINE_REPLAY = "doctrine-replay"
    EXECUTABLE_REPLAY = "executable-replay"
    FORMALLY_DERIVED = "formally-derived"
    SUPPLIED_HYPOTHESIS = "supplied-hypothesis"
    ORACLE_DEPENDENT = "oracle-dependent"
    HISTORICAL_REPLAY = "historical-replay"
    EMPIRICAL_BRIDGE = "empirical-bridge"


class MetaAuditDecision(str, Enum):
    SCHEMA_CONFORMANT = "schema-conformant"


class MetaOntologicalStatus(str, Enum):
    NOT_CLAIMED = "not-claimed"


class ResourceBound(str, Enum):
    PREMISE_COUNT = "premise-count"
    ASSUMPTION_COUNT = "assumption-count"
    FIELD_COUNT = "field-count"
    SCHEMA_COUNT = "schema-count"


class CastAttackOutcome(str, Enum):
    REJECTED = "rejected"


@dataclass(frozen=True)
class StatusProvenancePair:
    status: EvidenceStatus
    provenance: PositiveProvenance


@dataclass(frozen=True)
class KindStatusDomain:
    kind: JudgmentKind
    allowed_statuses: tuple[EvidenceStatus, ...]
    positive_pairs: tuple[StatusProvenancePair, ...]
    domain_digest: str


@dataclass(frozen=True)
class PremiseSignature:
    premise_name: str
    artifact_kind: str
    required_evidence_fields: tuple[str, ...]
    required_indices: tuple[str, ...]


@dataclass(frozen=True)
class PromotionRule:
    rule_id: str
    statement_digest: str
    premise_signatures: tuple[PremiseSignature, ...]
    output_kind: JudgmentKind
    output_status: EvidenceStatus
    output_provenance: PositiveProvenance
    output_indices: tuple[str, ...]
    forbidden_source_types: tuple[str, ...]
    forbidden_conclusion_fields: tuple[str, ...]
    assumption_policy_id: str
    permanent_nonclaims: tuple[str, ...]
    rule_digest: str


@dataclass(frozen=True)
class PremiseProjectionRule:
    projection_id: str
    source_rule_id: str
    premise_name: str
    projection_digest: str


@dataclass(frozen=True)
class IndexProjectionRule:
    projection_id: str
    kind: JudgmentKind
    input_indices: tuple[str, ...]
    hidden_index: str
    retained_indices: tuple[str, ...]
    projection_digest: str


@dataclass(frozen=True)
class SchemaTarget:
    schema_id: str
    exact_fields: tuple[str, ...]
    forbidden_positive_fields: tuple[str, ...]
    schema_digest: str


@dataclass(frozen=True)
class PromotionRegistry:
    version: str
    domains: tuple[KindStatusDomain, ...]
    rules: tuple[PromotionRule, ...]
    premise_projections: tuple[PremiseProjectionRule, ...]
    index_projections: tuple[IndexProjectionRule, ...]
    schema_targets: tuple[SchemaTarget, ...]
    registry_digest: str


@dataclass(frozen=True)
class IndexBinding:
    name: str
    value_digest: str


@dataclass(frozen=True)
class EvidenceField:
    name: str
    evidence_digest: str


@dataclass(frozen=True)
class PremiseArtifact:
    premise_name: str
    artifact_kind: str
    artifact_digest: str
    indices: tuple[IndexBinding, ...]
    evidence_fields: tuple[EvidenceField, ...]


@dataclass(frozen=True)
class AssumptionNode:
    assumption_id: str
    claim_id: str
    depends_on: tuple[str, ...]
    evidence_digest: str


@dataclass(frozen=True)
class ClaimDescriptor:
    claim_id: str
    kind: JudgmentKind
    status: EvidenceStatus
    provenance: PositiveProvenance | None
    indices: tuple[IndexBinding, ...]
    descriptor_digest: str


@dataclass(frozen=True)
class PromotionAuditRequest:
    version: str
    rule_id: str
    premises: tuple[PremiseArtifact, ...]
    assumptions: tuple[AssumptionNode, ...]
    conclusion: ClaimDescriptor
    request_digest: str


@dataclass(frozen=True)
class PromotionAuditPolicy:
    version: str
    max_premises: int
    max_assumptions: int
    max_fields: int
    max_schemas: int
    policy_digest: str


@dataclass(frozen=True)
class PromotionSchemaAudit:
    registry_digest: str
    rule_digest: str
    request_digest: str
    policy_digest: str
    conclusion: ClaimDescriptor
    premise_artifacts: tuple[PremiseArtifact, ...]
    assumption_closure: tuple[str, ...]
    nonclaims: tuple[str, ...]
    decision: MetaAuditDecision
    audit_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED
    scope: str = "promotion-schema-meta-validation-only"


@dataclass(frozen=True)
class PromotionResourceLimit:
    operation: str
    request_digest: str
    failed_bound: ResourceBound
    required_value: int
    allowed_value: int
    policy_digest: str
    refusal_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


PromotionAuditResult: TypeAlias = PromotionSchemaAudit | PromotionResourceLimit


@dataclass(frozen=True)
class PremiseProjection:
    projection_rule_digest: str
    source_audit_digest: str
    artifact: PremiseArtifact
    projection_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


@dataclass(frozen=True)
class IndexProjection:
    projection_rule_digest: str
    source_descriptor: ClaimDescriptor
    retained_indices: tuple[IndexBinding, ...]
    hidden_binding: IndexBinding
    existential: bool
    projection_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


@dataclass(frozen=True)
class SchemaAuditRow:
    schema_id: str
    exact_match: bool
    forbidden_fields_absent: bool
    row_digest: str


@dataclass(frozen=True)
class SchemaAuditReport:
    registry_digest: str
    policy_digest: str
    rows: tuple[SchemaAuditRow, ...]
    scope: str
    nonclaims: tuple[str, ...]
    report_digest: str
    decision: MetaAuditDecision
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED


@dataclass(frozen=True)
class CastAttack:
    attack_id: str
    weaker_kind: JudgmentKind
    stronger_kind: JudgmentKind
    reason: str
    attack_digest: str


@dataclass(frozen=True)
class CastAttackRow:
    attack: CastAttack
    outcome: CastAttackOutcome
    matching_rule_count: int
    row_digest: str


@dataclass(frozen=True)
class CastAttackMatrixReport:
    registry_digest: str
    rows: tuple[CastAttackRow, ...]
    report_digest: str
    ontological_establishment: MetaOntologicalStatus = MetaOntologicalStatus.NOT_CLAIMED

"""Resource/provenance DTOs for P1-A2 preflight and refusal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .observer_morphism_types import ObserverSourceBinding
from .observer_relation_types import (
    LawStatus, ObserverRelationJudgment, ObserverRelationScope,
    RelationEvaluationSource, TranslationInput,
)


class RelationOperation(str, Enum):
    """Typed operation marker for resource refusal."""

    JUDGE = "observer-relation-judgment"


class RelationResultStatus(str, Enum):
    """Typed refusal run status."""

    RESOURCE_LIMIT = "resource-limit"


@dataclass(frozen=True)
class RelationResourcePolicy:
    """Versioned and digest-bound work policy."""

    version: str
    max_cost: int
    max_encoded_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class RelationResourceLimit:
    """Typed refusal emitted before any semantic observation."""

    operation: RelationOperation
    status: RelationResultStatus
    policy_version: str
    policy_digest: str
    doctrine_fingerprint: str
    observer_source_digest: str
    stage_source_digest: str
    scope_digest: str
    required_cost: int
    allowed_cost: int
    required_encoded_bytes: int
    allowed_encoded_bytes: int
    observer_independent_identity: LawStatus
    universal_refinement: LawStatus
    nonclaims: tuple[str, ...]
    refusal_digest: str


ObserverRelationResult: TypeAlias = ObserverRelationJudgment | RelationResourceLimit


@dataclass(frozen=True)
class RelationRequest:
    """Validated request envelope used by preflight and runtime."""

    binding: ObserverSourceBinding
    source: RelationEvaluationSource
    scope: ObserverRelationScope
    forward: TranslationInput | None
    reverse: TranslationInput | None
    policy: RelationResourcePolicy

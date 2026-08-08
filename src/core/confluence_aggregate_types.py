"""Closed DTOs for P1-C2 declared finite confluence aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

from .confluence_types import (
    AlignmentPoint, ConfluenceObstruction, ConfluenceStatus, DirectEchoTransport,
    ForkJoinPlan, TransportMode, TransportResponseRow,
)

C2_NONCLAIMS = (
    "exhaustive-generated-path-coverage", "termination", "newman-lemma",
    "church-rosser", "unbounded-confluence", "object-formation",
    "absolute-identity", "absolute-existence", "all-depth-family",
    "completed-carrier", "novelty", "r8-promotion", "layer-promotion",
    "sage-promotion",
)


class RequirementKind(str, Enum):
    LOCAL = "local-critical-fork"
    GLOBAL = "global-declared-history-pair"


class LocalFiniteStatus(str, Enum):
    CONFLUENT = "local-finite-confluent"
    REFUTED = "refuted"
    OPEN = "open"


class GlobalDeclaredFiniteStatus(str, Enum):
    CONFLUENT = "global-declared-finite-confluent"
    REFUTED = "refuted"
    OPEN = "open"


class AggregateCoverageStatus(str, Enum):
    COMPLETE = "complete"


class AggregateResultStatus(str, Enum):
    RESOURCE_LIMIT = "resource-limit"


class AggregateFailedBound(str, Enum):
    CANONICAL_BYTES = "canonical-bytes"
    TOTAL_CHECKS = "total-checks"


@dataclass(frozen=True)
class IdentityHistory:
    version: str
    history_id: str
    stage_id: str
    stage_commitment: str
    history_digest: str


@dataclass(frozen=True)
class DeclaredHistory:
    version: str
    history_id: str
    path_id: str
    path_commitment: str
    start_stage_id: str
    end_stage_id: str
    history_digest: str


HistoryRef: TypeAlias = IdentityHistory | DeclaredHistory


@dataclass(frozen=True)
class LocalCriticalForkRequirement:
    requirement_id: str
    plan: ForkJoinPlan
    transport: DirectEchoTransport
    requirement_digest: str


@dataclass(frozen=True)
class GlobalPathPairRequirement:
    requirement_id: str
    left: HistoryRef
    right: HistoryRef
    alignment: tuple[AlignmentPoint, ...]
    transport: DirectEchoTransport
    requirement_digest: str


RequirementKey: TypeAlias = tuple[RequirementKind, str, str]


@dataclass(frozen=True)
class ConfluenceAggregatePolicy:
    version: str
    max_checks: int
    max_bytes: int
    policy_digest: str


@dataclass(frozen=True)
class FiniteConfluenceCatalogSource:
    doctrine_fingerprint: str
    diagram_digest: str
    local_requirements: tuple[LocalCriticalForkRequirement, ...]
    global_requirements: tuple[GlobalPathPairRequirement, ...]
    expected_local_keys: tuple[RequirementKey, ...]
    expected_global_keys: tuple[RequirementKey, ...]
    policy: ConfluenceAggregatePolicy
    catalog_digest: str
    version: str = "p1-c2-v1"
    scope: str = "declared-finite-catalog-not-generated-path-universe"


@dataclass(frozen=True)
class GlobalHistory2CellArtifact:
    doctrine_fingerprint: str
    diagram_digest: str
    requirement_digest: str
    left_history_digest: str
    right_history_digest: str
    left_stage_commitments: tuple[str, ...]
    right_stage_commitments: tuple[str, ...]
    alignment: tuple[AlignmentPoint, ...]
    required_observer_ids: tuple[str, ...]
    mode: TransportMode
    transport_digest: str
    response_rows: tuple[TransportResponseRow, ...]
    left_trace_digest: str
    right_trace_digest: str
    trace_digest: str
    first_obstruction: ConfluenceObstruction | None
    charged_checks: int
    status: ConfluenceStatus
    artifact_digest: str
    scope: str = "global-declared-finite-history-2-cell"


@dataclass(frozen=True)
class ConfluenceRequirementRow:
    key: RequirementKey
    plan_digest: str | None
    left_history_digest: str | None
    right_history_digest: str | None
    transport_digest: str
    local_judgment_digest: str | None
    global_history_cell_digest: str | None
    first_obstruction: ConfluenceObstruction | None
    charged_checks: int
    status: ConfluenceStatus
    row_digest: str


@dataclass(frozen=True)
class FiniteConfluenceAggregate:
    doctrine_fingerprint: str
    diagram_digest: str
    catalog_digest: str
    policy_digest: str
    run_digest: str
    expected_local_keys: tuple[RequirementKey, ...]
    expected_global_keys: tuple[RequirementKey, ...]
    rows: tuple[ConfluenceRequirementRow, ...]
    local_status: LocalFiniteStatus
    global_status: GlobalDeclaredFiniteStatus
    coverage: AggregateCoverageStatus
    first_obstruction: ConfluenceObstruction | None
    total_charge: int
    nonclaims: tuple[str, ...]
    aggregate_digest: str


@dataclass(frozen=True)
class ConfluenceAggregateResourceLimit:
    status: AggregateResultStatus
    doctrine_fingerprint: str
    diagram_digest: str
    catalog_digest: str
    policy_digest: str
    run_digest: str
    failed_bound: AggregateFailedBound
    required_value: int
    allowed_value: int
    nonclaims: tuple[str, ...]
    refusal_digest: str


FiniteConfluenceResult: TypeAlias = (
    FiniteConfluenceAggregate | ConfluenceAggregateResourceLimit
)

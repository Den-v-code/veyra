"""Closed DTOs for bounded semantic boundary-dynamics pressure in P3-OG."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    SemanticAblationReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    SemanticTickReceipt,
)
from .prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
    TransitionKind,
)


class BoundaryMaintenanceStatus(str, Enum):
    WITNESSED = "witnessed-live-boundary-over-declared-continuation-catalog"
    REFUTED = "refuted-live-boundary-over-declared-continuation-catalog"


class InternalRemovalStatus(str, Enum):
    WITNESSED = "witnessed-native-internal-boundary-removal"
    REFUTED = "refuted-native-internal-boundary-removal"


@dataclass(frozen=True)
class P3OGSemanticBoundaryDynamicsPlan:
    """Selection-free catalog/component contract for bounded boundary pressure."""

    version: str
    semantic_formation_bridge_contract_digest: str
    semantic_ablation_contract_digest: str
    component_id: str
    continuation_rule_id: str
    continuation_lengths: tuple[int, ...]
    max_steps: int
    plan_digest: str


@dataclass(frozen=True)
class P3OGSemanticBoundaryDynamicsEvidence:
    """Maintenance and internal-removal replay from one exact first-closure q0."""

    version: str
    plan_digest: str
    semantic_formation_bridge_evidence_digest: str
    q0: P3OGSemanticConfiguration
    maintenance_configurations: tuple[P3OGSemanticConfiguration, ...]
    maintenance_ticks: tuple[SemanticTickReceipt, ...]
    every_catalog_boundary_alive: bool
    maintenance_component_exercised: bool
    maintenance_status: BoundaryMaintenanceStatus
    maintenance_reason: str
    ablated_q0: P3OGSemanticConfiguration
    ablation_receipt: SemanticAblationReceipt
    removal_configurations: tuple[P3OGSemanticConfiguration, ...]
    removal_ticks: tuple[SemanticTickReceipt, ...]
    removal_step: int | None
    removal_before: P3OGSemanticConfiguration | None
    removal_after: P3OGSemanticConfiguration | None
    removal_tick: SemanticTickReceipt | None
    removal_signal_control: MaintenanceControlState | None
    removal_signal_credit: int | None
    removal_transition_kind: TransitionKind | None
    internal_removal_witnessed: bool
    removal_status: InternalRemovalStatus
    removal_reason: str
    promotions: int
    nonclaims: tuple[str, ...]
    evidence_digest: str


P3OG_SEMANTIC_BOUNDARY_DYNAMICS_NONCLAIMS = (
    "universal-def-og-005-theorem",
    "all-possible-continuation-catalogs",
    "removal-without-prior-typed-ablation",
    "full-def-og-006-discharge",
    "same-historical-token",
    "full-def-og-007-or-def-og-008-discharge",
    "criterion-blind-historical-selection",
    "consumed-one-shot-capability",
    "birth-core-or-historical-token",
    "endogenous-observer-role",
    "doctrine-admission",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)

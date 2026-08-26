"""Bounded maintenance/removal pressure over the P3-OG semantic carrier."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import P3OGAutonomousTickSource
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationBinding,
    P3OGNativeFormationContract,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_runtime import (
    semantic_ablate_maintenance,
    validate_semantic_ablation_contract,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    P3OGSemanticAblationContract,
    SemanticAblationReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_boundary_dynamics_codec import (
    semantic_boundary_dynamics_digest,
)
from .prime_power_observer_genesis_p3og_semantic_boundary_dynamics_types import (
    BoundaryMaintenanceStatus,
    InternalRemovalStatus,
    P3OGSemanticBoundaryDynamicsEvidence,
    P3OGSemanticBoundaryDynamicsPlan,
    P3OG_SEMANTIC_BOUNDARY_DYNAMICS_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    semantic_alive,
    semantic_tick,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticOperationMode,
    SemanticTickReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_runtime import (
    validate_p3og_semantic_formation_bridge_evidence,
    validate_semantic_formation_bridge_contract,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    MaintenanceControlState,
    P3OGSource,
    TransitionKind,
)

PLAN_VERSION = "p3og-semantic-boundary-dynamics-plan-v1"
EVIDENCE_VERSION = "p3og-semantic-boundary-dynamics-evidence-v1"
CONTINUATION_RULE_ID = "q-sem-prefix-catalog-one-through-maintenance-credit-v1"


def p3og_semantic_boundary_dynamics_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
) -> P3OGSemanticBoundaryDynamicsPlan:
    """Commit the finite continuation catalog and maintenance component before selection."""
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    ) = validate_semantic_formation_bridge_contract(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    )
    source, autonomous_source, semantic_contract, ablation_contract = (
        validate_semantic_ablation_contract(
            source,
            autonomous_source,
            semantic_contract,
            ablation_contract,
        )
    )
    max_steps = source.maintenance_credit
    continuation_lengths = tuple(range(1, max_steps + 1))
    fields = (
        PLAN_VERSION,
        bridge_contract.contract_digest,
        ablation_contract.contract_digest,
        ablation_contract.component_id,
        CONTINUATION_RULE_ID,
        continuation_lengths,
        max_steps,
    )
    return P3OGSemanticBoundaryDynamicsPlan(
        *fields,
        semantic_boundary_dynamics_digest("semantic-boundary-dynamics-plan", *fields),
    )


def _preflight_plan(plan: P3OGSemanticBoundaryDynamicsPlan) -> None:
    try:
        values = (
            plan.version,
            plan.semantic_formation_bridge_contract_digest,
            plan.semantic_ablation_contract_digest,
            plan.component_id,
            plan.continuation_rule_id,
            plan.continuation_lengths,
            plan.max_steps,
            plan.plan_digest,
        )
    except AttributeError as exc:
        raise ValueError("p3og-semantic-boundary-dynamics-plan-fields") from exc
    if (
        any(type(value) is not str for value in values[:5])
        or type(values[5]) is not tuple
        or type(values[6]) is not int
        or type(values[7]) is not str
        or not 1 <= values[6] <= 64
        or len(values[5]) != values[6]
        or len(values[5]) > 64
        or any(type(item) is not int or not 1 <= item <= 64 for item in values[5])
    ):
        raise ValueError("p3og-semantic-boundary-dynamics-plan-shape")


def validate_semantic_boundary_dynamics_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    plan: P3OGSemanticBoundaryDynamicsPlan,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGNativeFormationContract,
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticAblationContract,
    P3OGSemanticBoundaryDynamicsPlan,
]:
    if type(plan) is not P3OGSemanticBoundaryDynamicsPlan:
        raise ValueError("p3og-semantic-boundary-dynamics-plan-type")
    _preflight_plan(plan)
    try:
        expected = p3og_semantic_boundary_dynamics_plan(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            ablation_contract,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-boundary-dynamics-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-boundary-dynamics-plan-drift")
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    ) = validate_semantic_formation_bridge_contract(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
    )
    source, autonomous_source, semantic_contract, ablation_contract = (
        validate_semantic_ablation_contract(
            source,
            autonomous_source,
            semantic_contract,
            ablation_contract,
        )
    )
    return (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        ablation_contract,
        replace(expected),
    )


def build_p3og_semantic_boundary_dynamics_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    plan: P3OGSemanticBoundaryDynamicsPlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
) -> P3OGSemanticBoundaryDynamicsEvidence:
    """Replay bounded maintenance and native post-ablation boundary removal."""
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        ablation_contract,
        plan,
    ) = validate_semantic_boundary_dynamics_plan(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        ablation_contract,
        plan,
    )
    bridge_evidence = validate_p3og_semantic_formation_bridge_evidence(
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        binding,
        formation_source,
        formation_evidence,
        bridge_evidence,
    )
    try:
        seed = source.seeds[binding.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-semantic-boundary-dynamics-selection") from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != binding.selected_seed_digest:
        raise ValueError("p3og-semantic-boundary-dynamics-selected-seed")

    q0 = bridge_evidence.final_configuration
    if not compare_digest(canonical_bytes(q0), canonical_bytes(bridge_evidence.q_seed)):
        raise ValueError("p3og-semantic-boundary-dynamics-not-at-first-closure")

    maintenance_configurations: list[P3OGSemanticConfiguration] = [q0]
    maintenance_ticks: list[SemanticTickReceipt] = []
    current = q0
    for _ in plan.continuation_lengths:
        after, receipt = semantic_tick(
            source,
            autonomous_source,
            semantic_contract,
            seed,
            current,
        )
        maintenance_ticks.append(receipt)
        maintenance_configurations.append(after)
        current = after
    every_catalog_boundary_alive = all(
        semantic_alive(source, seed, configuration)
        for configuration in maintenance_configurations
    )
    maintenance_component_exercised = any(
        before.maintenance_control is MaintenanceControlState.ACTIVE
        and tick.selected_kind is TransitionKind.MAINTAIN
        and after.boundary is BoundaryState.ALIVE
        for before, tick, after in zip(
            maintenance_configurations[:-1],
            maintenance_ticks,
            maintenance_configurations[1:],
            strict=True,
        )
    )
    maintenance_witnessed = every_catalog_boundary_alive and maintenance_component_exercised
    maintenance_status = (
        BoundaryMaintenanceStatus.WITNESSED
        if maintenance_witnessed
        else BoundaryMaintenanceStatus.REFUTED
    )
    maintenance_reason = (
        "named-maintenance-component-exercised-and-all-declared-prefixes-stay-live"
        if maintenance_witnessed
        else "declared-prefix-catalog-does-not-witness-active-boundary-maintenance"
    )

    ablated_q0, ablation_receipt = semantic_ablate_maintenance(
        source,
        autonomous_source,
        semantic_contract,
        ablation_contract,
        seed,
        q0,
    )
    removal_configurations: list[P3OGSemanticConfiguration] = [ablated_q0]
    removal_ticks: list[SemanticTickReceipt] = []
    removal_step: int | None = None
    removal_before: P3OGSemanticConfiguration | None = None
    removal_after: P3OGSemanticConfiguration | None = None
    removal_tick: SemanticTickReceipt | None = None
    current = ablated_q0
    for step in plan.continuation_lengths:
        before = current
        after, receipt = semantic_tick(
            source,
            autonomous_source,
            semantic_contract,
            seed,
            before,
        )
        removal_ticks.append(receipt)
        removal_configurations.append(after)
        if before.boundary is BoundaryState.ALIVE and after.boundary is BoundaryState.REMOVED:
            removal_step = step
            removal_before = before
            removal_after = after
            removal_tick = receipt
            break
        current = after

    internal_removal_witnessed = (
        removal_tick is not None
        and removal_before is not None
        and removal_after is not None
        and removal_tick.mode is SemanticOperationMode.NATIVE_QUOTIENT
        and removal_before.maintenance_control is MaintenanceControlState.DISABLED
        and removal_before.boundary is BoundaryState.ALIVE
        and removal_after.boundary is BoundaryState.REMOVED
    )
    removal_status = (
        InternalRemovalStatus.WITNESSED
        if internal_removal_witnessed
        else InternalRemovalStatus.REFUTED
    )
    removal_reason = (
        "typed-maintenance-ablation-followed-by-native-state-driven-boundary-removal"
        if internal_removal_witnessed
        else "declared-post-ablation-prefix-catalog-does-not-reach-native-removal"
    )
    removal_signal_control = (
        removal_before.maintenance_control if removal_before is not None else None
    )
    removal_signal_credit = (
        removal_before.maintenance_credit if removal_before is not None else None
    )
    removal_transition_kind = removal_tick.selected_kind if removal_tick is not None else None

    fields = (
        EVIDENCE_VERSION,
        plan.plan_digest,
        bridge_evidence.evidence_digest,
        q0,
        tuple(maintenance_configurations),
        tuple(maintenance_ticks),
        every_catalog_boundary_alive,
        maintenance_component_exercised,
        maintenance_status,
        maintenance_reason,
        ablated_q0,
        ablation_receipt,
        tuple(removal_configurations),
        tuple(removal_ticks),
        removal_step,
        removal_before,
        removal_after,
        removal_tick,
        removal_signal_control,
        removal_signal_credit,
        removal_transition_kind,
        internal_removal_witnessed,
        removal_status,
        removal_reason,
        0,
        P3OG_SEMANTIC_BOUNDARY_DYNAMICS_NONCLAIMS,
    )
    return P3OGSemanticBoundaryDynamicsEvidence(
        *fields,
        semantic_boundary_dynamics_digest("semantic-boundary-dynamics-evidence", *fields),
    )


def _preflight_evidence(evidence: P3OGSemanticBoundaryDynamicsEvidence) -> None:
    try:
        q0 = evidence.q0
        maintenance_configurations = evidence.maintenance_configurations
        maintenance_ticks = evidence.maintenance_ticks
        ablated_q0 = evidence.ablated_q0
        ablation_receipt = evidence.ablation_receipt
        removal_configurations = evidence.removal_configurations
        removal_ticks = evidence.removal_ticks
        removal_step = evidence.removal_step
        removal_before = evidence.removal_before
        removal_after = evidence.removal_after
        removal_tick = evidence.removal_tick
        removal_signal_control = evidence.removal_signal_control
        removal_signal_credit = evidence.removal_signal_credit
        removal_transition_kind = evidence.removal_transition_kind
        scalar_flags = (
            evidence.every_catalog_boundary_alive,
            evidence.maintenance_component_exercised,
            evidence.internal_removal_witnessed,
        )
        maintenance_status = evidence.maintenance_status
        removal_status = evidence.removal_status
        strings = (evidence.maintenance_reason, evidence.removal_reason)
        promotions = evidence.promotions
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-semantic-boundary-dynamics-evidence-fields") from exc
    if (
        type(q0) is not P3OGSemanticConfiguration
        or type(ablated_q0) is not P3OGSemanticConfiguration
        or type(ablation_receipt) is not SemanticAblationReceipt
        or type(maintenance_configurations) is not tuple
        or type(maintenance_ticks) is not tuple
        or type(removal_configurations) is not tuple
        or type(removal_ticks) is not tuple
        or len(maintenance_configurations) > 65
        or len(maintenance_ticks) > 64
        or len(maintenance_configurations) != len(maintenance_ticks) + 1
        or len(removal_configurations) > 65
        or len(removal_ticks) > 64
        or len(removal_configurations) != len(removal_ticks) + 1
        or any(type(flag) is not bool for flag in scalar_flags)
        or type(maintenance_status) is not BoundaryMaintenanceStatus
        or type(removal_status) is not InternalRemovalStatus
        or any(type(value) is not str for value in strings)
        or type(promotions) is not int
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-semantic-boundary-dynamics-evidence-shape")
    for configuration in maintenance_configurations + removal_configurations:
        if type(configuration) is not P3OGSemanticConfiguration:
            raise ValueError("p3og-semantic-boundary-dynamics-configuration-type")
    for tick in maintenance_ticks + removal_ticks:
        if type(tick) is not SemanticTickReceipt:
            raise ValueError("p3og-semantic-boundary-dynamics-tick-type")
    if removal_step is not None and (type(removal_step) is not int or not 1 <= removal_step <= 64):
        raise ValueError("p3og-semantic-boundary-dynamics-removal-step")
    optional_pairs = (
        (removal_before, P3OGSemanticConfiguration),
        (removal_after, P3OGSemanticConfiguration),
        (removal_tick, SemanticTickReceipt),
        (removal_signal_control, MaintenanceControlState),
        (removal_transition_kind, TransitionKind),
    )
    if any(value is not None and type(value) is not cls for value, cls in optional_pairs):
        raise ValueError("p3og-semantic-boundary-dynamics-removal-option-type")
    if removal_signal_credit is not None and (
        type(removal_signal_credit) is not int or not 1 <= removal_signal_credit <= 64
    ):
        raise ValueError("p3og-semantic-boundary-dynamics-removal-credit")


def validate_p3og_semantic_boundary_dynamics_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    plan: P3OGSemanticBoundaryDynamicsPlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    evidence: P3OGSemanticBoundaryDynamicsEvidence,
) -> P3OGSemanticBoundaryDynamicsEvidence:
    """Freshly rebuild the complete maintenance/removal witness."""
    if type(evidence) is not P3OGSemanticBoundaryDynamicsEvidence:
        raise ValueError("p3og-semantic-boundary-dynamics-evidence-type")
    _preflight_evidence(evidence)
    try:
        expected = build_p3og_semantic_boundary_dynamics_evidence(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            ablation_contract,
            plan,
            binding,
            formation_source,
            formation_evidence,
            bridge_evidence,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-boundary-dynamics-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-boundary-dynamics-evidence-drift")
    return replace(expected)

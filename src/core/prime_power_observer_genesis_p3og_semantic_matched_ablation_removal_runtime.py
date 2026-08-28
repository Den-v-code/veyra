"""Matched maintenance ablation and removal dependence for current P3-OG."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_arithmetic_input_types import (
    P3OGArithmeticInputSource,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_runtime import (
    semantic_ablate_maintenance,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    P3OGSemanticAblationContract,
    SemanticAblationReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    semantic_alive,
    semantic_tick,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticTickReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
)
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_types import (
    P3OGSemanticInterventionPlan,
)
from .prime_power_observer_genesis_p3og_semantic_matched_ablation_removal_codec import (
    semantic_matched_ablation_removal_digest,
)
from .prime_power_observer_genesis_p3og_semantic_matched_ablation_removal_types import (
    P3OGSemanticMatchedAblationRemovalEvidence,
    P3OG_SEMANTIC_MATCHED_ABLATION_REMOVAL_NONCLAIMS,
    SemanticMatchedAblationRemovalStatus,
)
from .prime_power_observer_genesis_p3og_semantic_residue_phase_effect_runtime import (
    validate_p3og_semantic_residue_phase_effect_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_residue_phase_effect_types import (
    P3OGSemanticResiduePhaseEffectEvidence,
    SemanticResiduePhaseEffectStatus,
)
from .prime_power_observer_genesis_p3og_semantic_retained_difference_runtime import (
    validate_p3og_semantic_retained_difference_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_retained_difference_types import (
    P3OGSemanticRetainedDifferenceEvidence,
    SemanticRetainedDifferenceStatus,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import (
    MaintenanceControlState,
    P3OGSource,
)

EVIDENCE_VERSION = "p3og-semantic-matched-ablation-removal-evidence-v1"


def _matched_except_component(
    before: P3OGSemanticConfiguration,
    after: P3OGSemanticConfiguration,
) -> bool:
    return (
        before.run_id == after.run_id
        and before.seed_digest == after.seed_digest
        and before.boundary is after.boundary
        and before.phase == after.phase
        and before.retained_residue == after.retained_residue
        and before.maintenance_credit == after.maintenance_credit
        and before.maintenance_control is MaintenanceControlState.ACTIVE
        and after.maintenance_control is MaintenanceControlState.DISABLED
    )


def build_p3og_semantic_matched_ablation_removal_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
    arithmetic_source: P3OGArithmeticInputSource,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    retained_evidence: P3OGSemanticRetainedDifferenceEvidence,
    phase_effect_evidence: P3OGSemanticResiduePhaseEffectEvidence,
) -> P3OGSemanticMatchedAblationRemovalEvidence:
    """Ablate the exact component and replay the same declared continuation."""
    retained_evidence = validate_p3og_semantic_retained_difference_evidence(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        ablation_contract,
        intervention_plan,
        arithmetic_source,
        formation_source,
        formation_evidence,
        bridge_evidence,
        retained_evidence,
    )
    phase_effect_evidence = validate_p3og_semantic_residue_phase_effect_evidence(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        ablation_contract,
        intervention_plan,
        arithmetic_source,
        formation_source,
        formation_evidence,
        bridge_evidence,
        retained_evidence,
        phase_effect_evidence,
    )
    if len(intervention_plan.continuation_catalog) != 1:
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-continuation-catalog",
        )
    continuation = intervention_plan.continuation_catalog[0]
    if (
        retained_evidence.continuation_spec_digest != continuation.spec_digest
        or retained_evidence.continuation_steps != continuation.steps
        or continuation.steps < 1
    ):
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-continuation-drift",
        )

    try:
        seed = source.seeds[formation_source.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-selection",
        ) from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != retained_evidence.selected_seed_digest:
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-selected-seed",
        )

    left_before = retained_evidence.left_coupled
    right_before = retained_evidence.right_coupled
    left_ablated, left_ablation = semantic_ablate_maintenance(
        source,
        autonomous_source,
        semantic_contract,
        ablation_contract,
        seed,
        left_before,
    )
    right_ablated, right_ablation = semantic_ablate_maintenance(
        source,
        autonomous_source,
        semantic_contract,
        ablation_contract,
        seed,
        right_before,
    )
    matched_initials = (
        _matched_except_component(left_before, left_ablated)
        and _matched_except_component(right_before, right_ablated)
    )
    arithmetic_inputs_bound = (
        retained_evidence.left_coupling.input_value == arithmetic_source.left_input
        and retained_evidence.right_coupling.input_value
        == arithmetic_source.right_input
        and left_before.retained_residue == arithmetic_source.left_residue
        and right_before.retained_residue == arithmetic_source.right_residue
    )
    direct_reads_preserved = (
        left_ablation.read_before == left_ablation.read_after
        and right_ablation.read_before == right_ablation.read_after
    )

    left = left_ablated
    right = right_ablated
    left_configurations: list[P3OGSemanticConfiguration] = [left]
    right_configurations: list[P3OGSemanticConfiguration] = [right]
    left_ticks: list[SemanticTickReceipt] = []
    right_ticks: list[SemanticTickReceipt] = []
    for _ in range(continuation.steps):
        left, left_tick = semantic_tick(
            source,
            autonomous_source,
            semantic_contract,
            seed,
            left,
        )
        right, right_tick = semantic_tick(
            source,
            autonomous_source,
            semantic_contract,
            seed,
            right,
        )
        left_configurations.append(left)
        right_configurations.append(right)
        left_ticks.append(left_tick)
        right_ticks.append(right_tick)

    unablated_boundaries_alive = (
        retained_evidence.status is SemanticRetainedDifferenceStatus.WITNESSED
        and retained_evidence.every_step_boundary_alive
        and semantic_alive(
            source,
            seed,
            retained_evidence.left_configurations[-1],
        )
        and semantic_alive(
            source,
            seed,
            retained_evidence.right_configurations[-1],
        )
    )
    ablated_boundaries_removed = (
        not semantic_alive(source, seed, left_configurations[-1])
        and not semantic_alive(source, seed, right_configurations[-1])
    )
    ablated_residues_cleared = (
        left_configurations[-1].retained_residue is None
        and right_configurations[-1].retained_residue is None
    )
    claimed_ability_destroyed = (
        phase_effect_evidence.status is SemanticResiduePhaseEffectStatus.WITNESSED
        and ablated_boundaries_removed
        and ablated_residues_cleared
        and left_configurations[-1].phase == right_configurations[-1].phase
    )
    witnessed = (
        matched_initials
        and arithmetic_inputs_bound
        and direct_reads_preserved
        and unablated_boundaries_alive
        and ablated_boundaries_removed
        and ablated_residues_cleared
        and claimed_ability_destroyed
    )
    status = (
        SemanticMatchedAblationRemovalStatus.WITNESSED
        if witnessed
        else SemanticMatchedAblationRemovalStatus.REFUTED
    )
    reason = (
        "typed-maintenance-ablation-removes-boundary-and-retained-phase-ability"
        if witnessed
        else "matched-ablation-does-not-destroy-declared-retained-phase-ability"
    )
    fields = (
        EVIDENCE_VERSION,
        intervention_plan.plan_digest,
        intervention_plan.semantic_scope_digest,
        ablation_contract.contract_digest,
        retained_evidence.evidence_digest,
        phase_effect_evidence.evidence_digest,
        seed.seed_digest,
        ablation_contract.component_id,
        continuation.entry_id,
        continuation.spec_digest,
        continuation.steps,
        arithmetic_source.left_input,
        arithmetic_source.right_input,
        left_ablated,
        right_ablated,
        left_ablation,
        right_ablation,
        tuple(left_configurations),
        tuple(right_configurations),
        tuple(left_ticks),
        tuple(right_ticks),
        matched_initials,
        arithmetic_inputs_bound,
        direct_reads_preserved,
        unablated_boundaries_alive,
        ablated_boundaries_removed,
        ablated_residues_cleared,
        claimed_ability_destroyed,
        status,
        reason,
        0,
        P3OG_SEMANTIC_MATCHED_ABLATION_REMOVAL_NONCLAIMS,
    )
    return P3OGSemanticMatchedAblationRemovalEvidence(
        *fields,
        semantic_matched_ablation_removal_digest(
            "semantic-matched-ablation-removal-evidence",
            *fields,
        ),
    )


def _preflight_evidence(
    evidence: P3OGSemanticMatchedAblationRemovalEvidence,
) -> None:
    try:
        left_configurations = evidence.left_ablated_configurations
        right_configurations = evidence.right_ablated_configurations
        left_ticks = evidence.left_ablated_ticks
        right_ticks = evidence.right_ablated_ticks
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-evidence-fields",
        ) from exc
    if (
        type(evidence.left_ablated_initial) is not P3OGSemanticConfiguration
        or type(evidence.right_ablated_initial) is not P3OGSemanticConfiguration
        or type(evidence.left_ablation) is not SemanticAblationReceipt
        or type(evidence.right_ablation) is not SemanticAblationReceipt
        or type(left_configurations) is not tuple
        or type(right_configurations) is not tuple
        or type(left_ticks) is not tuple
        or type(right_ticks) is not tuple
        or type(evidence.continuation_steps) is not int
        or not 1 <= evidence.continuation_steps <= 4096
        or len(left_ticks) != evidence.continuation_steps
        or len(right_ticks) != evidence.continuation_steps
        or len(left_configurations) != len(left_ticks) + 1
        or len(right_configurations) != len(right_ticks) + 1
        or type(evidence.matched_initials_except_component) is not bool
        or type(evidence.arithmetic_inputs_bound) is not bool
        or type(evidence.direct_reads_preserved) is not bool
        or type(evidence.unablated_boundaries_alive) is not bool
        or type(evidence.ablated_boundaries_removed) is not bool
        or type(evidence.ablated_residues_cleared) is not bool
        or type(evidence.claimed_ability_destroyed) is not bool
        or type(evidence.status) is not SemanticMatchedAblationRemovalStatus
        or type(evidence.reason) is not str
        or type(evidence.promotions) is not int
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-evidence-shape",
        )
    for configuration in left_configurations + right_configurations:
        if type(configuration) is not P3OGSemanticConfiguration:
            raise ValueError(
                "p3og-semantic-matched-ablation-removal-configuration-type",
            )
    for tick in left_ticks + right_ticks:
        if type(tick) is not SemanticTickReceipt:
            raise ValueError(
                "p3og-semantic-matched-ablation-removal-tick-type",
            )


def validate_p3og_semantic_matched_ablation_removal_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
    arithmetic_source: P3OGArithmeticInputSource,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    retained_evidence: P3OGSemanticRetainedDifferenceEvidence,
    phase_effect_evidence: P3OGSemanticResiduePhaseEffectEvidence,
    evidence: P3OGSemanticMatchedAblationRemovalEvidence,
) -> P3OGSemanticMatchedAblationRemovalEvidence:
    """Freshly rebuild one matched removal witness and reject any drift."""
    if type(evidence) is not P3OGSemanticMatchedAblationRemovalEvidence:
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-evidence-type",
        )
    _preflight_evidence(evidence)
    try:
        expected = build_p3og_semantic_matched_ablation_removal_evidence(
            source,
            autonomous_source,
            semantic_contract,
            bridge_contract,
            ablation_contract,
            intervention_plan,
            arithmetic_source,
            formation_source,
            formation_evidence,
            bridge_evidence,
            retained_evidence,
            phase_effect_evidence,
        )
        equal = compare_digest(
            evidence_bytes(evidence),
            evidence_bytes(expected),
        )
    except (
        AttributeError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-evidence-malformed",
        ) from exc
    if not equal:
        raise ValueError(
            "p3og-semantic-matched-ablation-removal-evidence-drift",
        )
    return replace(expected)

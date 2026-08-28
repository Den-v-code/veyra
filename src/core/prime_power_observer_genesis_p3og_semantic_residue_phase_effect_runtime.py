"""Current retained-residue functional sensitivity in the existing P3-OG machine."""

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
from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    P3OGSemanticAblationContract,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfigurationContract,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
)
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_types import (
    P3OGSemanticInterventionPlan,
)
from .prime_power_observer_genesis_p3og_semantic_residue_phase_effect_codec import (
    semantic_residue_phase_effect_digest,
)
from .prime_power_observer_genesis_p3og_semantic_residue_phase_effect_types import (
    P3OGSemanticResiduePhaseEffectEvidence,
    P3OG_SEMANTIC_RESIDUE_PHASE_EFFECT_NONCLAIMS,
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
from .prime_power_observer_genesis_p3og_types import P3OGSource, TransitionKind

EVIDENCE_VERSION = "p3og-semantic-residue-phase-effect-evidence-v1"
COMPARISON_STEP = 1


def _matched_except_residue(
    left,
    right,
) -> bool:
    return (
        left.run_id == right.run_id
        and left.seed_digest == right.seed_digest
        and left.boundary is right.boundary
        and left.maintenance_control is right.maintenance_control
        and left.phase == right.phase
        and left.maintenance_credit == right.maintenance_credit
    )


def build_p3og_semantic_residue_phase_effect_evidence(
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
) -> P3OGSemanticResiduePhaseEffectEvidence:
    """Bind the first later ADVANCE outcome to the earlier retained residue."""
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
    if (
        len(retained_evidence.left_ticks) < COMPARISON_STEP
        or len(retained_evidence.right_ticks) < COMPARISON_STEP
        or len(retained_evidence.left_configurations) <= COMPARISON_STEP
        or len(retained_evidence.right_configurations) <= COMPARISON_STEP
    ):
        raise ValueError("p3og-semantic-residue-phase-effect-missing-later-step")

    try:
        seed = source.seeds[formation_source.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-semantic-residue-phase-effect-selection") from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != retained_evidence.selected_seed_digest:
        raise ValueError("p3og-semantic-residue-phase-effect-selected-seed")

    left_before = retained_evidence.left_configurations[0]
    right_before = retained_evidence.right_configurations[0]
    left_after = retained_evidence.left_configurations[COMPARISON_STEP]
    right_after = retained_evidence.right_configurations[COMPARISON_STEP]
    left_tick = retained_evidence.left_ticks[0]
    right_tick = retained_evidence.right_ticks[0]

    left_residue = left_before.retained_residue
    right_residue = right_before.retained_residue
    if type(left_residue) is not int or type(right_residue) is not int:
        raise ValueError("p3og-semantic-residue-phase-effect-residue")

    equal_coupling_response = (
        retained_evidence.left_coupling.response
        == retained_evidence.right_coupling.response
    )
    residues_distinct = left_residue != right_residue
    before_matched = _matched_except_residue(left_before, right_before)
    same_advance_kind = (
        left_tick.selected_kind is TransitionKind.ADVANCE
        and right_tick.selected_kind is TransitionKind.ADVANCE
    )
    phase_diverged = left_after.phase != right_after.phase

    period = len(seed.cycle) - 1
    expected_left_phase = (left_before.phase + 1 + left_residue) % period
    expected_right_phase = (right_before.phase + 1 + right_residue) % period
    transition_law_bound = (
        left_tick.before_configuration_digest == left_before.configuration_digest
        and right_tick.before_configuration_digest
        == right_before.configuration_digest
        and left_tick.after_configuration_digest == left_after.configuration_digest
        and right_tick.after_configuration_digest == right_after.configuration_digest
        and left_after.phase == expected_left_phase
        and right_after.phase == expected_right_phase
    )

    witnessed = (
        retained_evidence.status is SemanticRetainedDifferenceStatus.WITNESSED
        and equal_coupling_response
        and residues_distinct
        and before_matched
        and same_advance_kind
        and phase_diverged
        and transition_law_bound
    )
    status = (
        SemanticResiduePhaseEffectStatus.WITNESSED
        if witnessed
        else SemanticResiduePhaseEffectStatus.REFUTED
    )
    reason = (
        "equal-response-f0-f1-residues-change-first-later-advance-phase"
        if witnessed
        else "declared-retained-pair-does-not-show-first-later-advance-phase-effect"
    )
    fields = (
        EVIDENCE_VERSION,
        retained_evidence.evidence_digest,
        seed.seed_digest,
        COMPARISON_STEP,
        retained_evidence.left_coupling.response,
        retained_evidence.right_coupling.response,
        equal_coupling_response,
        left_residue,
        right_residue,
        residues_distinct,
        left_tick.selected_kind,
        right_tick.selected_kind,
        same_advance_kind,
        left_before.phase,
        right_before.phase,
        before_matched,
        left_after.phase,
        right_after.phase,
        phase_diverged,
        transition_law_bound,
        status,
        reason,
        0,
        P3OG_SEMANTIC_RESIDUE_PHASE_EFFECT_NONCLAIMS,
    )
    return P3OGSemanticResiduePhaseEffectEvidence(
        *fields,
        semantic_residue_phase_effect_digest(
            "semantic-residue-phase-effect-evidence",
            *fields,
        ),
    )


def _preflight_evidence(
    evidence: P3OGSemanticResiduePhaseEffectEvidence,
) -> None:
    try:
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-semantic-residue-phase-effect-evidence-fields") from exc
    if (
        type(evidence.comparison_step) is not int
        or evidence.comparison_step != COMPARISON_STEP
        or type(evidence.equal_coupling_response) is not bool
        or type(evidence.left_residue) is not int
        or type(evidence.right_residue) is not int
        or type(evidence.residues_distinct) is not bool
        or type(evidence.left_selected_kind) is not TransitionKind
        or type(evidence.right_selected_kind) is not TransitionKind
        or type(evidence.same_advance_kind) is not bool
        or type(evidence.left_before_phase) is not int
        or type(evidence.right_before_phase) is not int
        or type(evidence.before_matched_except_residue) is not bool
        or type(evidence.left_after_phase) is not int
        or type(evidence.right_after_phase) is not int
        or type(evidence.phase_diverged) is not bool
        or type(evidence.transition_law_bound) is not bool
        or type(evidence.status) is not SemanticResiduePhaseEffectStatus
        or type(evidence.reason) is not str
        or type(evidence.promotions) is not int
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-semantic-residue-phase-effect-evidence-shape")


def validate_p3og_semantic_residue_phase_effect_evidence(
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
    evidence: P3OGSemanticResiduePhaseEffectEvidence,
) -> P3OGSemanticResiduePhaseEffectEvidence:
    """Freshly rebuild one phase-effect witness and reject any drift."""
    if type(evidence) is not P3OGSemanticResiduePhaseEffectEvidence:
        raise ValueError("p3og-semantic-residue-phase-effect-evidence-type")
    _preflight_evidence(evidence)
    try:
        expected = build_p3og_semantic_residue_phase_effect_evidence(
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
            "p3og-semantic-residue-phase-effect-evidence-malformed",
        ) from exc
    if not equal:
        raise ValueError("p3og-semantic-residue-phase-effect-evidence-drift")
    return replace(expected)

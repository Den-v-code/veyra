"""Admit the coherent semantic P3-OG candidate into the existing v6 DAG."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_arithmetic_input_runtime import (
    validate_p3og_arithmetic_input_source,
)
from .prime_power_observer_genesis_p3og_arithmetic_input_types import (
    P3OGArithmeticInputSource,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_formation_history import (
    build_p3og_formation_history_evidence,
)
from .prime_power_observer_genesis_p3og_formation_history_codec import (
    formation_history_digest,
)
from .prime_power_observer_genesis_p3og_formation_history_types import (
    FormationHistoryPostClosureBindings,
    P3OGFormationHistoryEvidence,
    P3OGFormationHistoryPlan,
)
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
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_runtime import (
    validate_p3og_semantic_formation_bridge_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
    SemanticFormationBridgeStatus,
)
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_types import (
    P3OGSemanticInterventionPlan,
)
from .prime_power_observer_genesis_p3og_semantic_matched_ablation_removal_runtime import (
    validate_p3og_semantic_matched_ablation_removal_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_matched_ablation_removal_types import (
    P3OGSemanticMatchedAblationRemovalEvidence,
    SemanticMatchedAblationRemovalStatus,
)
from .prime_power_observer_genesis_p3og_semantic_preselection_history_runtime import (
    validate_p3og_semantic_preselection_history_plan,
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
from .prime_power_observer_genesis_p3og_types import P3OGSource

CRITERION_RULE_ID = "bounded-thm-p3og-001-items-1-through-6-v1"


def _validated_bindings(
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
    removal_evidence: P3OGSemanticMatchedAblationRemovalEvidence,
) -> tuple[
    FormationHistoryPostClosureBindings,
    str,
    str,
]:
    """Freshly replay every admitted post-closure payload before history binding."""
    source, arithmetic_source = validate_p3og_arithmetic_input_source(
        source,
        arithmetic_source,
    )
    bridge_evidence = validate_p3og_semantic_formation_bridge_evidence(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        formation_source,
        formation_evidence,
        bridge_evidence,
    )
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
    removal_evidence = validate_p3og_semantic_matched_ablation_removal_evidence(
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
        removal_evidence,
    )
    if bridge_evidence.status is not SemanticFormationBridgeStatus.WITNESSED:
        raise ValueError("p3og-semantic-complete-history-bridge-not-witnessed")
    if retained_evidence.status is not SemanticRetainedDifferenceStatus.WITNESSED:
        raise ValueError("p3og-semantic-complete-history-retention-not-witnessed")
    if phase_effect_evidence.status is not SemanticResiduePhaseEffectStatus.WITNESSED:
        raise ValueError("p3og-semantic-complete-history-phase-not-witnessed")
    if removal_evidence.status is not SemanticMatchedAblationRemovalStatus.WITNESSED:
        raise ValueError("p3og-semantic-complete-history-removal-not-witnessed")

    coupling_digest = formation_history_digest(
        "semantic-complete-history-coupling-pair",
        retained_evidence.left_coupling.receipt_digest,
        retained_evidence.right_coupling.receipt_digest,
    )
    ablation_digest = formation_history_digest(
        "semantic-complete-history-ablation-pair",
        removal_evidence.left_ablation.receipt_digest,
        removal_evidence.right_ablation.receipt_digest,
    )
    bindings = FormationHistoryPostClosureBindings(
        bridge_evidence.evidence_digest,
        arithmetic_source.source_digest,
        coupling_digest,
        retained_evidence.evidence_digest,
        phase_effect_evidence.evidence_digest,
        ablation_digest,
        removal_evidence.evidence_digest,
    )
    criterion_digest = formation_history_digest(
        "semantic-complete-history-criterion",
        CRITERION_RULE_ID,
    )
    result_digest = formation_history_digest(
        "semantic-complete-history-result",
        bridge_evidence.evidence_digest,
        arithmetic_source.source_digest,
        retained_evidence.evidence_digest,
        phase_effect_evidence.evidence_digest,
        removal_evidence.evidence_digest,
    )
    return bindings, criterion_digest, result_digest


def build_p3og_semantic_complete_history_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGFormationHistoryPlan,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    retained_evidence: P3OGSemanticRetainedDifferenceEvidence,
    phase_effect_evidence: P3OGSemanticResiduePhaseEffectEvidence,
    removal_evidence: P3OGSemanticMatchedAblationRemovalEvidence,
) -> P3OGFormationHistoryEvidence:
    """Build one bounded noncircular DAG for the coherent current candidate."""
    validate_p3og_semantic_preselection_history_plan(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        ablation_contract,
        intervention_plan,
        formation_source.selection_source,
        formation_source.selection_before,
        plan,
    )
    bindings, criterion_digest, result_digest = _validated_bindings(
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
        removal_evidence,
    )
    return build_p3og_formation_history_evidence(
        source,
        autonomous_source,
        plan,
        formation_source,
        formation_evidence,
        criterion_digest,
        result_digest,
        bindings,
    )


def validate_p3og_semantic_complete_history_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGFormationHistoryPlan,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    retained_evidence: P3OGSemanticRetainedDifferenceEvidence,
    phase_effect_evidence: P3OGSemanticResiduePhaseEffectEvidence,
    removal_evidence: P3OGSemanticMatchedAblationRemovalEvidence,
    evidence: P3OGFormationHistoryEvidence,
) -> P3OGFormationHistoryEvidence:
    """Freshly rebuild the exact complete-history candidate and reject drift."""
    if type(evidence) is not P3OGFormationHistoryEvidence:
        raise ValueError("p3og-semantic-complete-history-evidence-type")
    try:
        expected = build_p3og_semantic_complete_history_evidence(
            source,
            autonomous_source,
            semantic_contract,
            bridge_contract,
            ablation_contract,
            intervention_plan,
            arithmetic_source,
            plan,
            formation_source,
            formation_evidence,
            bridge_evidence,
            retained_evidence,
            phase_effect_evidence,
            removal_evidence,
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
        raise ValueError("p3og-semantic-complete-history-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-complete-history-evidence-drift")
    return replace(expected)

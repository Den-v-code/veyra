"""Matched equal-response retained-residue causal-effect pressure for P3-OG."""

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
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationBinding,
    P3OGNativeFormationContract,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_runtime import (
    residue_aware_semantic_tick,
    validate_p3og_residue_aware_formation_compatibility_evidence,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_source import (
    validate_residue_aware_tick_source,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_types import (
    P3OGResidueAwareFormationCompatibilityEvidence,
    P3OGResidueAwareTickSource,
    ResidueAwareSemanticTickReceipt,
)
from .prime_power_observer_genesis_p3og_residue_causal_effect_codec import (
    residue_causal_effect_digest,
)
from .prime_power_observer_genesis_p3og_residue_causal_effect_types import (
    P3OGResidueCausalEffectEvidence,
    P3OGResidueCausalEffectPlan,
    P3OG_RESIDUE_CAUSAL_EFFECT_NONCLAIMS,
    ResidueCausalEffectStatus,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    semantic_couple,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticCouplingReceipt,
    SemanticOperationMode,
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
    P3OGSource,
    TransitionKind,
)

PLAN_VERSION = "p3og-residue-causal-effect-plan-v1"
EVIDENCE_VERSION = "p3og-residue-causal-effect-evidence-v1"
BEFORE_MATCH_RULE_ID = "same-q-sem-fields-except-retained-residue-and-digest-v1"
TICK_MATCH_RULE_ID = "same-residue-aware-native-transition-kind-v1"
EFFECT_RULE_ID = "equal-response-distinct-residue-same-advance-divergent-phase-v1"
EFFECT_COORDINATE = "phase"


def p3og_residue_causal_effect_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
) -> P3OGResidueCausalEffectPlan:
    """Commit one matched causal-sensitivity criterion before candidate selection."""
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
    source, autonomous_source, semantic_contract, residue_aware_source = (
        validate_residue_aware_tick_source(
            source,
            autonomous_source,
            semantic_contract,
            residue_aware_source,
        )
    )
    source, arithmetic_source = validate_p3og_arithmetic_input_source(
        source,
        arithmetic_source,
    )
    fields = (
        PLAN_VERSION,
        bridge_contract.contract_digest,
        arithmetic_source.source_digest,
        residue_aware_source.source_digest,
        BEFORE_MATCH_RULE_ID,
        TICK_MATCH_RULE_ID,
        EFFECT_RULE_ID,
        EFFECT_COORDINATE,
    )
    return P3OGResidueCausalEffectPlan(
        *fields,
        residue_causal_effect_digest("residue-causal-effect-plan", *fields),
    )


def _preflight_plan(plan: P3OGResidueCausalEffectPlan) -> None:
    try:
        values = (
            plan.version,
            plan.semantic_formation_bridge_contract_digest,
            plan.arithmetic_input_source_digest,
            plan.residue_aware_source_digest,
            plan.before_match_rule_id,
            plan.tick_match_rule_id,
            plan.effect_rule_id,
            plan.effect_coordinate,
            plan.plan_digest,
        )
    except AttributeError as exc:
        raise ValueError("p3og-residue-causal-effect-plan-fields") from exc
    if any(type(value) is not str or not value for value in values):
        raise ValueError("p3og-residue-causal-effect-plan-shape")


def validate_p3og_residue_causal_effect_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGResidueCausalEffectPlan,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGResidueAwareTickSource,
    P3OGNativeFormationContract,
    P3OGSemanticFormationBridgeContract,
    P3OGArithmeticInputSource,
    P3OGResidueCausalEffectPlan,
]:
    if type(plan) is not P3OGResidueCausalEffectPlan:
        raise ValueError("p3og-residue-causal-effect-plan-type")
    _preflight_plan(plan)
    try:
        expected = p3og_residue_causal_effect_plan(
            source,
            autonomous_source,
            semantic_contract,
            residue_aware_source,
            formation_contract,
            bridge_contract,
            arithmetic_source,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-residue-causal-effect-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-residue-causal-effect-plan-drift")
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
    source, autonomous_source, semantic_contract, residue_aware_source = (
        validate_residue_aware_tick_source(
            source,
            autonomous_source,
            semantic_contract,
            residue_aware_source,
        )
    )
    source, arithmetic_source = validate_p3og_arithmetic_input_source(
        source,
        arithmetic_source,
    )
    return (
        source,
        autonomous_source,
        semantic_contract,
        residue_aware_source,
        formation_contract,
        bridge_contract,
        arithmetic_source,
        replace(expected),
    )


def _before_matched_except_residue(
    left: P3OGSemanticConfiguration,
    right: P3OGSemanticConfiguration,
) -> bool:
    left_values = (
        left.run_id,
        left.seed_digest,
        left.boundary,
        left.maintenance_control,
        left.phase,
        left.maintenance_credit,
    )
    right_values = (
        right.run_id,
        right.seed_digest,
        right.boundary,
        right.maintenance_control,
        right.phase,
        right.maintenance_credit,
    )
    return left_values == right_values


def _after_matched_except_phase_and_residue(
    left: P3OGSemanticConfiguration,
    right: P3OGSemanticConfiguration,
) -> bool:
    left_values = (
        left.run_id,
        left.seed_digest,
        left.boundary,
        left.maintenance_control,
        left.maintenance_credit,
    )
    right_values = (
        right.run_id,
        right.seed_digest,
        right.boundary,
        right.maintenance_control,
        right.maintenance_credit,
    )
    return left_values == right_values


def build_p3og_residue_causal_effect_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGResidueCausalEffectPlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    compatibility_evidence: P3OGResidueAwareFormationCompatibilityEvidence,
) -> P3OGResidueCausalEffectEvidence:
    """Replay one equal-response matched pair and test residue-sensitive phase evolution."""
    (
        source,
        autonomous_source,
        semantic_contract,
        residue_aware_source,
        formation_contract,
        bridge_contract,
        arithmetic_source,
        plan,
    ) = validate_p3og_residue_causal_effect_plan(
        source,
        autonomous_source,
        semantic_contract,
        residue_aware_source,
        formation_contract,
        bridge_contract,
        arithmetic_source,
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
    compatibility_evidence = validate_p3og_residue_aware_formation_compatibility_evidence(
        source,
        autonomous_source,
        semantic_contract,
        residue_aware_source,
        formation_contract,
        bridge_contract,
        binding,
        formation_source,
        formation_evidence,
        bridge_evidence,
        compatibility_evidence,
    )
    try:
        seed = source.seeds[binding.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-residue-causal-effect-selection") from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != binding.selected_seed_digest:
        raise ValueError("p3og-residue-causal-effect-selected-seed")

    q0 = bridge_evidence.final_configuration
    if not compare_digest(canonical_bytes(q0), canonical_bytes(bridge_evidence.q_seed)):
        raise ValueError("p3og-residue-causal-effect-not-at-first-closure")
    if compatibility_evidence.final_configuration.configuration_digest != q0.configuration_digest:
        raise ValueError("p3og-residue-causal-effect-compatibility-final-drift")

    left, left_coupling = semantic_couple(
        source,
        autonomous_source,
        semantic_contract,
        seed,
        q0,
        arithmetic_source.left_input,
    )
    right, right_coupling = semantic_couple(
        source,
        autonomous_source,
        semantic_contract,
        seed,
        q0,
        arithmetic_source.right_input,
    )
    if (
        left.retained_residue != arithmetic_source.left_residue
        or right.retained_residue != arithmetic_source.right_residue
    ):
        raise ValueError("p3og-residue-causal-effect-arithmetic-residue-drift")

    before_matched = _before_matched_except_residue(left, right)
    equal_response = left_coupling.response == right_coupling.response
    residues_distinct = left.retained_residue != right.retained_residue

    left_after, left_tick = residue_aware_semantic_tick(
        source,
        autonomous_source,
        semantic_contract,
        residue_aware_source,
        seed,
        left,
    )
    right_after, right_tick = residue_aware_semantic_tick(
        source,
        autonomous_source,
        semantic_contract,
        residue_aware_source,
        seed,
        right,
    )
    same_selected_kind = left_tick.selected_kind is right_tick.selected_kind
    same_tick_mode = left_tick.mode is right_tick.mode
    selected_advance = same_selected_kind and left_tick.selected_kind is TransitionKind.ADVANCE
    phase_diverged = left_after.phase != right_after.phase
    after_matched = _after_matched_except_phase_and_residue(left_after, right_after)

    witnessed = (
        before_matched
        and equal_response
        and residues_distinct
        and left.boundary is BoundaryState.ALIVE
        and right.boundary is BoundaryState.ALIVE
        and same_selected_kind
        and same_tick_mode
        and left_tick.mode is SemanticOperationMode.NATIVE_QUOTIENT
        and selected_advance
        and phase_diverged
        and after_matched
        and left_after.boundary is BoundaryState.ALIVE
        and right_after.boundary is BoundaryState.ALIVE
    )
    status = (
        ResidueCausalEffectStatus.WITNESSED
        if witnessed
        else ResidueCausalEffectStatus.REFUTED
    )
    reason = (
        "equal-response-matched-residue-pair-same-advance-diverges-in-phase"
        if witnessed
        else "matched-residue-pair-does-not-satisfy-declared-phase-effect-criterion"
    )
    fields = (
        EVIDENCE_VERSION,
        plan.plan_digest,
        bridge_evidence.evidence_digest,
        compatibility_evidence.evidence_digest,
        q0,
        left,
        right,
        left_coupling,
        right_coupling,
        before_matched,
        equal_response,
        residues_distinct,
        left_tick,
        right_tick,
        left_after,
        right_after,
        same_selected_kind,
        same_tick_mode,
        selected_advance,
        phase_diverged,
        after_matched,
        status,
        reason,
        0,
        P3OG_RESIDUE_CAUSAL_EFFECT_NONCLAIMS,
    )
    return P3OGResidueCausalEffectEvidence(
        *fields,
        residue_causal_effect_digest("residue-causal-effect-evidence", *fields),
    )


def _preflight_evidence(evidence: P3OGResidueCausalEffectEvidence) -> None:
    try:
        configurations = (
            evidence.q0,
            evidence.left_coupled,
            evidence.right_coupled,
            evidence.left_after,
            evidence.right_after,
        )
        couplings = (evidence.left_coupling, evidence.right_coupling)
        ticks = (evidence.left_tick, evidence.right_tick)
        booleans = (
            evidence.before_matched_except_residue,
            evidence.equal_coupling_response,
            evidence.residues_distinct,
            evidence.same_selected_kind,
            evidence.same_tick_mode,
            evidence.selected_advance,
            evidence.phase_diverged,
            evidence.after_matched_except_phase_and_residue,
        )
        status = evidence.status
        reason = evidence.reason
        promotions = evidence.promotions
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-residue-causal-effect-evidence-fields") from exc
    if (
        any(type(configuration) is not P3OGSemanticConfiguration for configuration in configurations)
        or any(type(coupling) is not SemanticCouplingReceipt for coupling in couplings)
        or any(type(tick) is not ResidueAwareSemanticTickReceipt for tick in ticks)
        or any(type(value) is not bool for value in booleans)
        or type(status) is not ResidueCausalEffectStatus
        or type(reason) is not str
        or type(promotions) is not int
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-residue-causal-effect-evidence-shape")


def validate_p3og_residue_causal_effect_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGResidueCausalEffectPlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    compatibility_evidence: P3OGResidueAwareFormationCompatibilityEvidence,
    evidence: P3OGResidueCausalEffectEvidence,
) -> P3OGResidueCausalEffectEvidence:
    """Freshly rebuild the matched causal-effect evidence and reject any drift."""
    if type(evidence) is not P3OGResidueCausalEffectEvidence:
        raise ValueError("p3og-residue-causal-effect-evidence-type")
    _preflight_evidence(evidence)
    try:
        expected = build_p3og_residue_causal_effect_evidence(
            source,
            autonomous_source,
            semantic_contract,
            residue_aware_source,
            formation_contract,
            bridge_contract,
            arithmetic_source,
            plan,
            binding,
            formation_source,
            formation_evidence,
            bridge_evidence,
            compatibility_evidence,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-residue-causal-effect-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-residue-causal-effect-evidence-drift")
    return replace(expected)

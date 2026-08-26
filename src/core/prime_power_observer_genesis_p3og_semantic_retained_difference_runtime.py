"""Exact semantic retained-difference replay from P3-N2 F0/F1 inputs."""

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
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    semantic_alive,
    semantic_couple,
    semantic_tick,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticCouplingReceipt,
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
from .prime_power_observer_genesis_p3og_semantic_retained_difference_codec import (
    semantic_retained_difference_digest,
)
from .prime_power_observer_genesis_p3og_semantic_retained_difference_types import (
    P3OGSemanticRetainedDifferenceEvidence,
    P3OGSemanticRetainedDifferencePlan,
    P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS,
    SemanticRetainedDifferenceStatus,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import P3OGSource

PLAN_VERSION = "p3og-semantic-retained-difference-plan-v1"
EVIDENCE_VERSION = "p3og-semantic-retained-difference-evidence-v1"
CONTINUATION_RULE_ID = "same-q-sem-tick-all-prefixes-through-maintenance-credit-v1"


def p3og_semantic_retained_difference_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
) -> P3OGSemanticRetainedDifferencePlan:
    """Commit one finite common-continuation prefix catalog before selection."""
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
    source, arithmetic_source = validate_p3og_arithmetic_input_source(
        source,
        arithmetic_source,
    )
    max_steps = source.maintenance_credit
    continuation_lengths = tuple(range(1, max_steps + 1))
    fields = (
        PLAN_VERSION,
        bridge_contract.contract_digest,
        arithmetic_source.source_digest,
        CONTINUATION_RULE_ID,
        continuation_lengths,
        max_steps,
    )
    return P3OGSemanticRetainedDifferencePlan(
        *fields,
        semantic_retained_difference_digest("semantic-retained-difference-plan", *fields),
    )


def _preflight_plan(plan: P3OGSemanticRetainedDifferencePlan) -> None:
    try:
        version = plan.version
        bridge_digest = plan.semantic_formation_bridge_contract_digest
        arithmetic_digest = plan.arithmetic_input_source_digest
        rule_id = plan.continuation_rule_id
        lengths = plan.continuation_lengths
        max_steps = plan.max_steps
        plan_digest = plan.plan_digest
    except AttributeError as exc:
        raise ValueError("p3og-semantic-retained-difference-plan-fields") from exc
    if (
        type(version) is not str
        or type(bridge_digest) is not str
        or type(arithmetic_digest) is not str
        or type(rule_id) is not str
        or type(lengths) is not tuple
        or type(max_steps) is not int
        or type(plan_digest) is not str
        or len(lengths) > 64
        or max_steps < 1
        or max_steps > 64
        or len(lengths) != max_steps
        or any(type(item) is not int or item < 1 or item > 64 for item in lengths)
    ):
        raise ValueError("p3og-semantic-retained-difference-plan-shape")


def validate_semantic_retained_difference_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGSemanticRetainedDifferencePlan,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGNativeFormationContract,
    P3OGSemanticFormationBridgeContract,
    P3OGArithmeticInputSource,
    P3OGSemanticRetainedDifferencePlan,
]:
    if type(plan) is not P3OGSemanticRetainedDifferencePlan:
        raise ValueError("p3og-semantic-retained-difference-plan-type")
    _preflight_plan(plan)
    try:
        expected = p3og_semantic_retained_difference_plan(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            arithmetic_source,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-retained-difference-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-retained-difference-plan-drift")
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
    source, arithmetic_source = validate_p3og_arithmetic_input_source(
        source,
        arithmetic_source,
    )
    return (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        arithmetic_source,
        replace(expected),
    )


def build_p3og_semantic_retained_difference_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGSemanticRetainedDifferencePlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
) -> P3OGSemanticRetainedDifferenceEvidence:
    """Couple F0/F1 at one exact q0 and replay the same autonomous tick catalog."""
    (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        bridge_contract,
        arithmetic_source,
        plan,
    ) = validate_semantic_retained_difference_plan(
        source,
        autonomous_source,
        semantic_contract,
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
    try:
        seed = source.seeds[binding.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-semantic-retained-difference-selection") from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != binding.selected_seed_digest:
        raise ValueError("p3og-semantic-retained-difference-selected-seed")

    q0 = bridge_evidence.final_configuration
    if not compare_digest(canonical_bytes(q0), canonical_bytes(bridge_evidence.q_seed)):
        raise ValueError("p3og-semantic-retained-difference-not-at-first-closure")

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
        raise ValueError("p3og-semantic-retained-difference-arithmetic-residue-drift")

    initial_residues_distinct = left.retained_residue != right.retained_residue
    left_configurations: list[P3OGSemanticConfiguration] = [left]
    right_configurations: list[P3OGSemanticConfiguration] = [right]
    left_ticks: list[SemanticTickReceipt] = []
    right_ticks: list[SemanticTickReceipt] = []

    for _ in plan.continuation_lengths:
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

    paired = tuple(zip(left_configurations, right_configurations, strict=True))
    every_prefix_residues_distinct = all(
        left_state.retained_residue != right_state.retained_residue
        for left_state, right_state in paired
    )
    every_prefix_boundary_alive = all(
        semantic_alive(source, seed, left_state)
        and semantic_alive(source, seed, right_state)
        for left_state, right_state in paired
    )
    witnessed = (
        initial_residues_distinct
        and every_prefix_residues_distinct
        and every_prefix_boundary_alive
    )
    status = (
        SemanticRetainedDifferenceStatus.WITNESSED
        if witnessed
        else SemanticRetainedDifferenceStatus.REFUTED
    )
    reason = (
        "f0-f1-residues-remain-distinct-and-live-over-declared-prefix-catalog"
        if witnessed
        else "declared-prefix-catalog-does-not-preserve-live-retained-difference"
    )
    fields = (
        EVIDENCE_VERSION,
        plan.plan_digest,
        bridge_evidence.evidence_digest,
        q0,
        left_configurations[0],
        right_configurations[0],
        left_coupling,
        right_coupling,
        tuple(left_configurations),
        tuple(right_configurations),
        tuple(left_ticks),
        tuple(right_ticks),
        initial_residues_distinct,
        every_prefix_residues_distinct,
        every_prefix_boundary_alive,
        status,
        reason,
        0,
        P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS,
    )
    return P3OGSemanticRetainedDifferenceEvidence(
        *fields,
        semantic_retained_difference_digest(
            "semantic-retained-difference-evidence",
            *fields,
        ),
    )


def _preflight_evidence(evidence: P3OGSemanticRetainedDifferenceEvidence) -> None:
    try:
        q0 = evidence.q0
        left_coupled = evidence.left_coupled
        right_coupled = evidence.right_coupled
        left_configurations = evidence.left_configurations
        right_configurations = evidence.right_configurations
        left_ticks = evidence.left_ticks
        right_ticks = evidence.right_ticks
        initial_distinct = evidence.initial_residues_distinct
        prefix_distinct = evidence.every_prefix_residues_distinct
        prefix_alive = evidence.every_prefix_boundary_alive
        status = evidence.status
        reason = evidence.reason
        promotions = evidence.promotions
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-semantic-retained-difference-evidence-fields") from exc
    if (
        type(q0) is not P3OGSemanticConfiguration
        or type(left_coupled) is not P3OGSemanticConfiguration
        or type(right_coupled) is not P3OGSemanticConfiguration
        or type(left_configurations) is not tuple
        or type(right_configurations) is not tuple
        or type(left_ticks) is not tuple
        or type(right_ticks) is not tuple
        or len(left_configurations) > 65
        or len(right_configurations) > 65
        or len(left_ticks) > 64
        or len(right_ticks) > 64
        or len(left_configurations) != len(left_ticks) + 1
        or len(right_configurations) != len(right_ticks) + 1
        or len(left_configurations) != len(right_configurations)
        or type(initial_distinct) is not bool
        or type(prefix_distinct) is not bool
        or type(prefix_alive) is not bool
        or type(status) is not SemanticRetainedDifferenceStatus
        or type(reason) is not str
        or type(promotions) is not int
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-semantic-retained-difference-evidence-shape")
    for configuration in left_configurations + right_configurations:
        if type(configuration) is not P3OGSemanticConfiguration:
            raise ValueError("p3og-semantic-retained-difference-configuration-type")
    for tick in left_ticks + right_ticks:
        if type(tick) is not SemanticTickReceipt:
            raise ValueError("p3og-semantic-retained-difference-tick-type")
    if (
        type(evidence.left_coupling) is not SemanticCouplingReceipt
        or type(evidence.right_coupling) is not SemanticCouplingReceipt
    ):
        raise ValueError("p3og-semantic-retained-difference-coupling-type")


def validate_p3og_semantic_retained_difference_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    arithmetic_source: P3OGArithmeticInputSource,
    plan: P3OGSemanticRetainedDifferencePlan,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    evidence: P3OGSemanticRetainedDifferenceEvidence,
) -> P3OGSemanticRetainedDifferenceEvidence:
    """Freshly rebuild the complete retained-difference witness and reject drift."""
    if type(evidence) is not P3OGSemanticRetainedDifferenceEvidence:
        raise ValueError("p3og-semantic-retained-difference-evidence-type")
    _preflight_evidence(evidence)
    try:
        expected = build_p3og_semantic_retained_difference_evidence(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            arithmetic_source,
            plan,
            binding,
            formation_source,
            formation_evidence,
            bridge_evidence,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-retained-difference-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-retained-difference-evidence-drift")
    return replace(expected)

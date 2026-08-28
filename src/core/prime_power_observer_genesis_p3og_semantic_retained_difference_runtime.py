"""Current retained-difference replay from P3-N2 F0/F1 into Q_sem."""

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
from .prime_power_observer_genesis_p3og_codec import (
    canonical_bytes,
    evidence_bytes,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_runtime import (
    validate_semantic_ablation_contract,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    P3OGSemanticAblationContract,
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
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_runtime import (
    validate_p3og_semantic_intervention_plan,
)
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_types import (
    P3OGSemanticInterventionPlan,
)
from .prime_power_observer_genesis_p3og_semantic_retained_difference_codec import (
    semantic_retained_difference_digest,
)
from .prime_power_observer_genesis_p3og_semantic_retained_difference_types import (
    P3OGSemanticRetainedDifferenceEvidence,
    P3OG_SEMANTIC_RETAINED_DIFFERENCE_NONCLAIMS,
    SemanticRetainedDifferenceStatus,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import P3OGSource

EVIDENCE_VERSION = "p3og-semantic-retained-difference-evidence-v2"


def build_p3og_semantic_retained_difference_evidence(
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
) -> P3OGSemanticRetainedDifferenceEvidence:
    """Couple exact F0/F1 at first closure and replay one committed continuation."""
    (
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
    ) = validate_semantic_formation_bridge_contract(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
    )
    _, _, _, ablation_contract = validate_semantic_ablation_contract(
        source,
        autonomous_source,
        semantic_contract,
        ablation_contract,
    )
    intervention_plan = validate_p3og_semantic_intervention_plan(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        ablation_contract,
        intervention_plan,
    )
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
    if len(intervention_plan.continuation_catalog) != 1:
        raise ValueError(
            "p3og-semantic-retained-difference-continuation-catalog",
        )
    continuation = intervention_plan.continuation_catalog[0]
    if (
        continuation.steps < 1
        or continuation.tick_rule_id != semantic_contract.tick_rule_id
    ):
        raise ValueError(
            "p3og-semantic-retained-difference-continuation-contract",
        )

    try:
        seed = source.seeds[formation_source.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-semantic-retained-difference-selection") from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != formation_source.selected_seed_digest:
        raise ValueError("p3og-semantic-retained-difference-selected-seed")

    q0 = bridge_evidence.final_configuration
    if not compare_digest(
        canonical_bytes(q0),
        canonical_bytes(bridge_evidence.q_seed),
    ):
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
        raise ValueError(
            "p3og-semantic-retained-difference-arithmetic-residue-drift",
        )

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

    paired = tuple(
        zip(left_configurations, right_configurations, strict=True),
    )
    initial_residues_distinct = (
        left_configurations[0].retained_residue
        != right_configurations[0].retained_residue
    )
    every_step_residues_distinct = all(
        left_state.retained_residue != right_state.retained_residue
        for left_state, right_state in paired
    )
    every_step_boundary_alive = all(
        semantic_alive(source, seed, left_state)
        and semantic_alive(source, seed, right_state)
        for left_state, right_state in paired
    )
    witnessed = (
        initial_residues_distinct
        and every_step_residues_distinct
        and every_step_boundary_alive
    )
    status = (
        SemanticRetainedDifferenceStatus.WITNESSED
        if witnessed
        else SemanticRetainedDifferenceStatus.REFUTED
    )
    reason = (
        "p3n2-f0-f1-residues-remain-distinct-over-declared-continuation"
        if witnessed
        else "declared-continuation-does-not-preserve-live-residue-difference"
    )
    fields = (
        EVIDENCE_VERSION,
        intervention_plan.plan_digest,
        arithmetic_source.source_digest,
        bridge_evidence.evidence_digest,
        seed.seed_digest,
        continuation.entry_id,
        continuation.spec_digest,
        continuation.steps,
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
        every_step_residues_distinct,
        every_step_boundary_alive,
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


def _preflight_evidence(
    evidence: P3OGSemanticRetainedDifferenceEvidence,
) -> None:
    try:
        left_configurations = evidence.left_configurations
        right_configurations = evidence.right_configurations
        left_ticks = evidence.left_ticks
        right_ticks = evidence.right_ticks
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError(
            "p3og-semantic-retained-difference-evidence-fields",
        ) from exc
    if (
        type(evidence.q0) is not P3OGSemanticConfiguration
        or type(evidence.left_coupled) is not P3OGSemanticConfiguration
        or type(evidence.right_coupled) is not P3OGSemanticConfiguration
        or type(evidence.left_coupling) is not SemanticCouplingReceipt
        or type(evidence.right_coupling) is not SemanticCouplingReceipt
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
        or len(left_configurations) != len(right_configurations)
        or type(evidence.initial_residues_distinct) is not bool
        or type(evidence.every_step_residues_distinct) is not bool
        or type(evidence.every_step_boundary_alive) is not bool
        or type(evidence.status) is not SemanticRetainedDifferenceStatus
        or type(evidence.reason) is not str
        or type(evidence.promotions) is not int
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-semantic-retained-difference-evidence-shape")
    for configuration in left_configurations + right_configurations:
        if type(configuration) is not P3OGSemanticConfiguration:
            raise ValueError(
                "p3og-semantic-retained-difference-configuration-type",
            )
    for tick in left_ticks + right_ticks:
        if type(tick) is not SemanticTickReceipt:
            raise ValueError("p3og-semantic-retained-difference-tick-type")


def validate_p3og_semantic_retained_difference_evidence(
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
    evidence: P3OGSemanticRetainedDifferenceEvidence,
) -> P3OGSemanticRetainedDifferenceEvidence:
    """Freshly rebuild the exact retained-difference witness and reject drift."""
    if type(evidence) is not P3OGSemanticRetainedDifferenceEvidence:
        raise ValueError("p3og-semantic-retained-difference-evidence-type")
    _preflight_evidence(evidence)
    try:
        expected = build_p3og_semantic_retained_difference_evidence(
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
            "p3og-semantic-retained-difference-evidence-malformed",
        ) from exc
    if not equal:
        raise ValueError("p3og-semantic-retained-difference-evidence-drift")
    return replace(expected)

"""Bind exact semantic commitments into the existing blind formation-history cut."""

from __future__ import annotations

from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_formation_history import (
    p3og_formation_history_plan,
    p3og_formation_history_precommitment,
    validate_formation_history_plan,
)
from .prime_power_observer_genesis_p3og_formation_history_types import (
    FormationHistoryPrecommitment,
    P3OGFormationHistoryPlan,
)
from .prime_power_observer_genesis_p3og_one_shot_selection_types import (
    P3OGOneShotSelectionSource,
    P3OGSelectionCapability,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_runtime import (
    validate_semantic_ablation_contract,
)
from .prime_power_observer_genesis_p3og_semantic_ablation_types import (
    P3OGSemanticAblationContract,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    validate_semantic_configuration_contract,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfigurationContract,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_runtime import (
    validate_semantic_formation_bridge_contract,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
)
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_runtime import (
    validate_p3og_semantic_intervention_plan,
)
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_types import (
    P3OGSemanticInterventionPlan,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

SEMANTIC_CONFIGURATION_COMMITMENT_ID = "semantic-configuration-contract"
SEMANTIC_FORMATION_BRIDGE_COMMITMENT_ID = "semantic-formation-bridge-contract"
SEMANTIC_ABLATION_COMMITMENT_ID = "semantic-ablation-contract"
SEMANTIC_INTERVENTION_PLAN_COMMITMENT_ID = "semantic-intervention-plan"

P3OG_SEMANTIC_PRESELECTION_HISTORY_NONCLAIMS = (
    "semantic-commitments-in-strict-past-do-not-authenticate-external-chronology",
    "semantic-commitments-are-not-information-sources-of-blind-selection",
    "selection-free-contracts-do-not-prove-selection-source-completeness",
    "post-formation-ablation-cut-not-yet-executed",
    "matched-continuation-not-yet-executed",
    "comparison-cut-not-yet-observed",
    "full-def-og-006-discharge",
    "full-def-og-007-discharge",
    "full-def-og-008-discharge",
    "full-def-og-009-discharge",
    "same-historical-token",
    "doctrine-admission",
    "endogenous-observer-role",
    "birth-core-or-historical-token",
    "n0-or-hap-lift",
    "historical-actualization",
    "formal-theorem-or-certificate",
    "promotion",
)


def semantic_preselection_commitments(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
) -> tuple[FormationHistoryPrecommitment, ...]:
    """Canonical four selection-free semantic commitments for history v6."""
    source, autonomous_source, semantic_contract = (
        validate_semantic_configuration_contract(
            source,
            autonomous_source,
            semantic_contract,
        )
    )
    _, _, _, bridge_contract = validate_semantic_formation_bridge_contract(
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
    semantic = p3og_formation_history_precommitment(
        SEMANTIC_CONFIGURATION_COMMITMENT_ID,
        semantic_contract.contract_digest,
        ("source", "autonomous-law"),
    )
    bridge = p3og_formation_history_precommitment(
        SEMANTIC_FORMATION_BRIDGE_COMMITMENT_ID,
        bridge_contract.contract_digest,
        (
            "source",
            "autonomous-law",
            SEMANTIC_CONFIGURATION_COMMITMENT_ID,
        ),
    )
    ablation = p3og_formation_history_precommitment(
        SEMANTIC_ABLATION_COMMITMENT_ID,
        ablation_contract.contract_digest,
        (
            "source",
            "autonomous-law",
            SEMANTIC_CONFIGURATION_COMMITMENT_ID,
        ),
    )
    intervention = p3og_formation_history_precommitment(
        SEMANTIC_INTERVENTION_PLAN_COMMITMENT_ID,
        intervention_plan.plan_digest,
        (
            "source",
            "autonomous-law",
            SEMANTIC_CONFIGURATION_COMMITMENT_ID,
            SEMANTIC_FORMATION_BRIDGE_COMMITMENT_ID,
            SEMANTIC_ABLATION_COMMITMENT_ID,
        ),
    )
    return semantic, bridge, ablation, intervention


def validate_p3og_semantic_preselection_commitments(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
    commitments: tuple[FormationHistoryPrecommitment, ...],
) -> tuple[FormationHistoryPrecommitment, ...]:
    """Require the exact canonical semantic commitment tuple."""
    if (
        type(commitments) is not tuple
        or any(
            type(item) is not FormationHistoryPrecommitment
            for item in commitments
        )
    ):
        raise ValueError("p3og-semantic-preselection-commitments-shape")
    expected = semantic_preselection_commitments(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        ablation_contract,
        intervention_plan,
    )
    try:
        equal = compare_digest(
            canonical_bytes(commitments),
            canonical_bytes(expected),
        )
    except (
        AttributeError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "p3og-semantic-preselection-commitments-malformed"
        ) from exc
    if not equal:
        raise ValueError("p3og-semantic-preselection-commitments-drift")
    return expected


def p3og_semantic_preselection_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
    selection_source: P3OGOneShotSelectionSource,
    available_capability: P3OGSelectionCapability,
) -> P3OGFormationHistoryPlan:
    """Build the existing history plan with exact semantic commitments."""
    commitments = semantic_preselection_commitments(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        ablation_contract,
        intervention_plan,
    )
    return p3og_formation_history_plan(
        source,
        autonomous_source,
        selection_source,
        available_capability,
        commitments,
    )


def validate_p3og_semantic_preselection_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    intervention_plan: P3OGSemanticInterventionPlan,
    selection_source: P3OGOneShotSelectionSource,
    available_capability: P3OGSelectionCapability,
    plan: P3OGFormationHistoryPlan,
) -> P3OGFormationHistoryPlan:
    """Freshly validate generic history plus the exact semantic preselection cut."""
    _, _, plan = validate_formation_history_plan(
        source,
        autonomous_source,
        selection_source,
        available_capability,
        plan,
    )
    validate_p3og_semantic_preselection_commitments(
        source,
        autonomous_source,
        semantic_contract,
        bridge_contract,
        ablation_contract,
        intervention_plan,
        plan.preselection_commitments,
    )
    return plan

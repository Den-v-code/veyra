"""Selection-free semantic intervention plan for bounded P3-OG."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
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
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_codec import (
    semantic_intervention_plan_digest,
)
from .prime_power_observer_genesis_p3og_semantic_intervention_plan_types import (
    P3OGSemanticComparisonCut,
    P3OGSemanticContinuationSpec,
    P3OGSemanticInterventionPlan,
    P3OG_SEMANTIC_INTERVENTION_PLAN_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

PLAN_VERSION = "p3og-semantic-intervention-plan-v1"
CONTINUATION_ENTRY_ID = "maintenance-credit-horizon"
COMPARISON_CUT_ID = "post-continuation-observation-cut"
OBSERVATION_RULE_ID = "same-semantic-coupling-after-continuation-v1"
OBSERVATION_INPUT = 0
CODE_IDENTITY_RULE_ID = "same-source-and-semantic-contracts-on-both-branches-v1"
ARITHMETIC_INPUT_MATCH_RULE_ID = "same-precommitted-observation-input-v1"
EXTERNAL_SCHEDULE_MATCH_RULE_ID = "same-continuation-catalog-on-both-branches-v1"
SCOPE_MATCH_RULE_ID = "same-semantic-scope-digest-on-both-branches-v1"
MAX_CONTINUATIONS = 8
MAX_COMPARISON_CUTS = 8


def _continuation_spec(
    semantic_contract: P3OGSemanticConfigurationContract,
    steps: int,
) -> P3OGSemanticContinuationSpec:
    if type(steps) is not int or not 1 <= steps <= semantic_contract.max_transition_count:
        raise ValueError("p3og-semantic-intervention-continuation-steps")
    schedule_digest = semantic_intervention_plan_digest(
        "semantic-intervention-schedule",
        semantic_contract.tick_rule_id,
        steps,
    )
    fields = (
        CONTINUATION_ENTRY_ID,
        semantic_contract.tick_rule_id,
        steps,
        schedule_digest,
    )
    return P3OGSemanticContinuationSpec(
        *fields,
        semantic_intervention_plan_digest(
            "semantic-intervention-continuation-spec",
            *fields,
        ),
    )


def _comparison_cut(
    continuation: P3OGSemanticContinuationSpec,
) -> P3OGSemanticComparisonCut:
    fields = (
        COMPARISON_CUT_ID,
        continuation.entry_id,
        OBSERVATION_RULE_ID,
        OBSERVATION_INPUT,
    )
    return P3OGSemanticComparisonCut(
        *fields,
        semantic_intervention_plan_digest(
            "semantic-intervention-comparison-cut",
            *fields,
        ),
    )


def p3og_semantic_intervention_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
) -> P3OGSemanticInterventionPlan:
    """Commit matched continuation/ablation/cut grammar without selecting a candidate."""
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
    continuation = _continuation_spec(
        semantic_contract,
        source.maintenance_credit,
    )
    continuation_catalog = (continuation,)
    continuation_catalog_digest = semantic_intervention_plan_digest(
        "semantic-intervention-continuation-catalog",
        continuation_catalog,
    )
    cut = _comparison_cut(continuation)
    comparison_cuts = (cut,)
    comparison_cut_catalog_digest = semantic_intervention_plan_digest(
        "semantic-intervention-comparison-cut-catalog",
        comparison_cuts,
    )
    semantic_scope_digest = semantic_intervention_plan_digest(
        "semantic-intervention-scope",
        source.source_digest,
        autonomous_source.source_digest,
        semantic_contract.contract_digest,
        bridge_contract.contract_digest,
        ablation_contract.contract_digest,
        ablation_contract.component_id,
        continuation_catalog_digest,
        comparison_cut_catalog_digest,
        CODE_IDENTITY_RULE_ID,
        ARITHMETIC_INPUT_MATCH_RULE_ID,
        EXTERNAL_SCHEDULE_MATCH_RULE_ID,
        SCOPE_MATCH_RULE_ID,
    )
    fields = (
        PLAN_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        semantic_contract.contract_digest,
        bridge_contract.contract_digest,
        ablation_contract.contract_digest,
        ablation_contract.component_id,
        continuation_catalog,
        continuation_catalog_digest,
        comparison_cuts,
        comparison_cut_catalog_digest,
        CODE_IDENTITY_RULE_ID,
        ARITHMETIC_INPUT_MATCH_RULE_ID,
        EXTERNAL_SCHEDULE_MATCH_RULE_ID,
        SCOPE_MATCH_RULE_ID,
        semantic_scope_digest,
        MAX_CONTINUATIONS,
        MAX_COMPARISON_CUTS,
        P3OG_SEMANTIC_INTERVENTION_PLAN_NONCLAIMS,
    )
    return P3OGSemanticInterventionPlan(
        *fields,
        semantic_intervention_plan_digest(
            "semantic-intervention-plan",
            *fields,
        ),
    )


def _preflight_plan(plan: P3OGSemanticInterventionPlan) -> None:
    try:
        continuations = plan.continuation_catalog
        cuts = plan.comparison_cuts
        nonclaims = plan.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-semantic-intervention-plan-fields") from exc
    if (
        type(continuations) is not tuple
        or not 1 <= len(continuations) <= MAX_CONTINUATIONS
        or type(cuts) is not tuple
        or not 1 <= len(cuts) <= MAX_COMPARISON_CUTS
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-semantic-intervention-plan-shape")
    if any(type(item) is not P3OGSemanticContinuationSpec for item in continuations):
        raise ValueError("p3og-semantic-intervention-continuation-type")
    if any(type(item) is not P3OGSemanticComparisonCut for item in cuts):
        raise ValueError("p3og-semantic-intervention-comparison-cut-type")


def validate_p3og_semantic_intervention_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    ablation_contract: P3OGSemanticAblationContract,
    plan: P3OGSemanticInterventionPlan,
) -> P3OGSemanticInterventionPlan:
    """Freshly rebuild the complete selection-free intervention grammar."""
    if type(plan) is not P3OGSemanticInterventionPlan:
        raise ValueError("p3og-semantic-intervention-plan-type")
    _preflight_plan(plan)
    try:
        expected = p3og_semantic_intervention_plan(
            source,
            autonomous_source,
            semantic_contract,
            bridge_contract,
            ablation_contract,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-intervention-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-intervention-plan-drift")
    return replace(expected)

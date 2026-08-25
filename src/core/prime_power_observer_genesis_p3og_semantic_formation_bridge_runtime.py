"""Exact replay bridge from Native Formation v2 into the finite Q_sem carrier."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes
from .prime_power_observer_genesis_p3og_native_formation_runtime import (
    _native_formation_tick_validated,
)
from .prime_power_observer_genesis_p3og_native_formation_source import (
    validate_legacy_source_against_contract_binding,
    validate_native_formation_contract,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    NativeFormationBoundary,
    NativeFormationStatus,
    P3OGNativeFormationBinding,
    P3OGNativeFormationContract,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_native_formation_validation import (
    validate_p3og_native_formation_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    semantic_configuration_from_native,
    semantic_q_seed,
    semantic_tick,
    validate_semantic_configuration_contract,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticTickReceipt,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_codec import (
    semantic_formation_bridge_digest,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
    P3OG_SEMANTIC_FORMATION_BRIDGE_NONCLAIMS,
    SemanticFormationBridgeStatus,
    SemanticFormationBridgeStep,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

CONTRACT_VERSION = "p3og-semantic-formation-bridge-contract-v1"
EVIDENCE_VERSION = "p3og-semantic-formation-bridge-evidence-v1"
BRIDGE_RULE_ID = "fresh-native-formation-replay-equals-q-sem-tick-v1"
CLOSURE_RULE_ID = "genuine-departure-then-first-q-sem-seed-return-v1"


def p3og_semantic_formation_bridge_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
) -> P3OGSemanticFormationBridgeContract:
    """Commit the exact pre-selection relation between formation and Q_sem."""
    source, autonomous_source, semantic_contract = (
        validate_semantic_configuration_contract(
            source,
            autonomous_source,
            semantic_contract,
        )
    )
    source, autonomous_source, formation_contract = validate_native_formation_contract(
        source,
        autonomous_source,
        formation_contract,
    )
    fields = (
        CONTRACT_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        semantic_contract.contract_digest,
        formation_contract.contract_digest,
        BRIDGE_RULE_ID,
        CLOSURE_RULE_ID,
    )
    return P3OGSemanticFormationBridgeContract(
        *fields,
        semantic_formation_bridge_digest(
            "semantic-formation-bridge-contract",
            *fields,
        ),
    )


def validate_semantic_formation_bridge_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
) -> tuple[
    P3OGSource,
    P3OGAutonomousTickSource,
    P3OGSemanticConfigurationContract,
    P3OGNativeFormationContract,
    P3OGSemanticFormationBridgeContract,
]:
    """Freshly reconstruct the complete selection-free bridge contract."""
    if type(bridge_contract) is not P3OGSemanticFormationBridgeContract:
        raise ValueError("p3og-semantic-formation-bridge-contract-type")
    try:
        expected = p3og_semantic_formation_bridge_contract(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
        )
        equal = compare_digest(
            canonical_bytes(bridge_contract),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError(
            "p3og-semantic-formation-bridge-contract-malformed",
        ) from exc
    if not equal:
        raise ValueError("p3og-semantic-formation-bridge-contract-drift")
    source, autonomous_source, semantic_contract = (
        validate_semantic_configuration_contract(
            source,
            autonomous_source,
            semantic_contract,
        )
    )
    source, autonomous_source, formation_contract = validate_native_formation_contract(
        source,
        autonomous_source,
        formation_contract,
    )
    return (
        source,
        autonomous_source,
        semantic_contract,
        formation_contract,
        replace(expected),
    )


def _same_configuration(
    left: P3OGSemanticConfiguration,
    right: P3OGSemanticConfiguration,
) -> bool:
    return compare_digest(canonical_bytes(left), canonical_bytes(right))


def build_p3og_semantic_formation_bridge_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
) -> P3OGSemanticFormationBridgeEvidence:
    """Replay one witnessed formation and prove its genealogy lives in Q_sem."""
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
    formation_contract, binding, formation_source = (
        validate_legacy_source_against_contract_binding(
            source,
            autonomous_source,
            formation_contract,
            binding,
            formation_source,
        )
    )
    formation_evidence = validate_p3og_native_formation_evidence(
        source,
        autonomous_source,
        formation_source,
        formation_evidence,
    )
    if formation_evidence.status is not NativeFormationStatus.WITNESSED:
        raise ValueError(
            "p3og-semantic-formation-bridge-requires-witnessed-formation",
        )
    if (
        formation_evidence.first_closure_step is None
        or formation_evidence.initial_state.boundary is not NativeFormationBoundary.UNFORMED
        or formation_evidence.final_state.boundary is not NativeFormationBoundary.ALIVE
    ):
        raise ValueError("p3og-semantic-formation-bridge-formation-shape")

    try:
        seed = source.seeds[binding.selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-semantic-formation-bridge-selection") from exc
    if seed.seed_digest != binding.selected_seed_digest:
        raise ValueError("p3og-semantic-formation-bridge-selected-seed")

    q_seed = semantic_q_seed(source, seed)
    initial_configuration = semantic_configuration_from_native(
        source,
        seed,
        formation_evidence.initial_state.native_state,
    )
    if not _same_configuration(initial_configuration, q_seed):
        raise ValueError("p3og-semantic-formation-bridge-initial-not-q-seed")

    state = formation_evidence.initial_state
    departed = False
    departure_step: int | None = None
    closure_step: int | None = None
    steps: list[SemanticFormationBridgeStep] = []

    for index, expected_formation_tick in enumerate(
        formation_evidence.ticks,
        start=1,
    ):
        before_configuration = semantic_configuration_from_native(
            source,
            seed,
            state.native_state,
        )
        semantic_after, semantic_receipt = semantic_tick(
            source,
            autonomous_source,
            semantic_contract,
            seed,
            before_configuration,
        )
        next_state, replayed_formation_tick = _native_formation_tick_validated(
            source,
            autonomous_source,
            formation_source,
            state,
        )
        if not compare_digest(
            canonical_bytes(replayed_formation_tick),
            canonical_bytes(expected_formation_tick),
        ):
            raise ValueError("p3og-semantic-formation-bridge-native-replay-drift")
        projected_after = semantic_configuration_from_native(
            source,
            seed,
            next_state.native_state,
        )
        if not _same_configuration(semantic_after, projected_after):
            raise ValueError("p3og-semantic-formation-bridge-quotient-drift")
        if (
            semantic_receipt.selected_kind
            is not replayed_formation_tick.autonomous_tick.selected_kind
        ):
            raise ValueError("p3og-semantic-formation-bridge-kind-drift")

        prior_departed = departed
        at_seed = _same_configuration(projected_after, q_seed)
        if not departed and not at_seed:
            departed = True
            departure_step = index
        closed_after = departed and at_seed
        if closed_after and closure_step is None:
            closure_step = index
        elif closed_after:
            raise ValueError("p3og-semantic-formation-bridge-multiple-closure")

        if next_state.departed is not departed:
            raise ValueError("p3og-semantic-formation-bridge-departure-drift")
        if replayed_formation_tick.became_departed is not (
            (not prior_departed) and departed
        ):
            raise ValueError(
                "p3og-semantic-formation-bridge-departure-receipt-drift",
            )
        if replayed_formation_tick.became_alive is not closed_after:
            raise ValueError("p3og-semantic-formation-bridge-closure-receipt-drift")
        if closed_after and index != len(formation_evidence.ticks):
            raise ValueError("p3og-semantic-formation-bridge-not-first-terminal-closure")

        step_fields = (
            index,
            replayed_formation_tick.receipt_digest,
            before_configuration.configuration_digest,
            semantic_receipt,
            projected_after.configuration_digest,
            departed,
            closed_after,
        )
        steps.append(
            SemanticFormationBridgeStep(
                *step_fields,
                semantic_formation_bridge_digest(
                    "semantic-formation-bridge-step",
                    *step_fields,
                ),
            ),
        )
        state = next_state

    if departure_step is None or closure_step is None:
        raise ValueError("p3og-semantic-formation-bridge-no-first-return")
    if closure_step != formation_evidence.first_closure_step:
        raise ValueError("p3og-semantic-formation-bridge-closure-step-drift")
    if closure_step != len(steps):
        raise ValueError("p3og-semantic-formation-bridge-closure-not-terminal")
    final_configuration = semantic_configuration_from_native(
        source,
        seed,
        state.native_state,
    )
    if not _same_configuration(final_configuration, q_seed):
        raise ValueError("p3og-semantic-formation-bridge-final-not-q-seed")
    if not _same_configuration(
        final_configuration,
        semantic_configuration_from_native(
            source,
            seed,
            formation_evidence.final_state.native_state,
        ),
    ):
        raise ValueError("p3og-semantic-formation-bridge-final-drift")

    captured = tuple(steps)
    genealogy = semantic_formation_bridge_digest(
        "semantic-formation-bridge-genealogy",
        bridge_contract.contract_digest,
        binding.binding_digest,
        formation_evidence.evidence_digest,
        q_seed,
        captured,
        final_configuration,
        departure_step,
        closure_step,
    )
    fields = (
        EVIDENCE_VERSION,
        bridge_contract.contract_digest,
        binding.binding_digest,
        formation_source.source_digest,
        formation_evidence.evidence_digest,
        binding.selected_seed_digest,
        q_seed,
        captured,
        final_configuration,
        departure_step,
        closure_step,
        SemanticFormationBridgeStatus.WITNESSED,
        "native-formation-is-first-return-in-q-sem",
        genealogy,
        0,
        P3OG_SEMANTIC_FORMATION_BRIDGE_NONCLAIMS,
    )
    return P3OGSemanticFormationBridgeEvidence(
        *fields,
        semantic_formation_bridge_digest(
            "semantic-formation-bridge-evidence",
            *fields,
        ),
    )


def _preflight_bridge_evidence(
    evidence: P3OGSemanticFormationBridgeEvidence,
) -> None:
    try:
        q_seed = evidence.q_seed
        steps = evidence.steps
        final_configuration = evidence.final_configuration
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError(
            "p3og-semantic-formation-bridge-evidence-fields",
        ) from exc
    if (
        type(q_seed) is not P3OGSemanticConfiguration
        or type(final_configuration) is not P3OGSemanticConfiguration
        or type(steps) is not tuple
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-semantic-formation-bridge-evidence-shape")
    for step in steps:
        if type(step) is not SemanticFormationBridgeStep:
            raise ValueError("p3og-semantic-formation-bridge-step-type")
        if type(step.semantic_tick) is not SemanticTickReceipt:
            raise ValueError("p3og-semantic-formation-bridge-semantic-tick-type")


def validate_p3og_semantic_formation_bridge_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    evidence: P3OGSemanticFormationBridgeEvidence,
) -> P3OGSemanticFormationBridgeEvidence:
    """Freshly rebuild the exact bridge and reject any replay drift."""
    if type(evidence) is not P3OGSemanticFormationBridgeEvidence:
        raise ValueError("p3og-semantic-formation-bridge-evidence-type")
    _preflight_bridge_evidence(evidence)
    try:
        expected = build_p3og_semantic_formation_bridge_evidence(
            source,
            autonomous_source,
            semantic_contract,
            formation_contract,
            bridge_contract,
            binding,
            formation_source,
            formation_evidence,
        )
        equal = compare_digest(
            evidence_bytes(evidence),
            evidence_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError(
            "p3og-semantic-formation-bridge-evidence-malformed",
        ) from exc
    if not equal:
        raise ValueError("p3og-semantic-formation-bridge-evidence-drift")
    return replace(expected)

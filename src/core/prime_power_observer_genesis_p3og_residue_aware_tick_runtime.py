"""Residue-aware semantic tick and exact compatibility with the v1 formation kernel."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    MaintenanceCreditClass,
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_machine_internal import _transition_validated
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationBinding,
    P3OGNativeFormationContract,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_codec import (
    residue_aware_tick_digest,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_source import (
    validate_residue_aware_tick_source,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_types import (
    P3OGResidueAwareFormationCompatibilityEvidence,
    P3OGResidueAwareTickSource,
    P3OG_RESIDUE_AWARE_TICK_NONCLAIMS,
    ResidueAwareFormationCompatibilityStatus,
    ResidueAwareSemanticTickReceipt,
    ResiduePresenceClass,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_runtime import (
    _representative_native_validated,
    _semantic_from_native_validated,
    _validate_semantic_configuration_validated,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticOperationMode,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_runtime import (
    validate_p3og_semantic_formation_bridge_evidence,
)
from .prime_power_observer_genesis_p3og_semantic_formation_bridge_types import (
    P3OGSemanticFormationBridgeContract,
    P3OGSemanticFormationBridgeEvidence,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    P3OGSource,
    PrimitiveModeSeed,
    TransitionKind,
)

EVIDENCE_VERSION = "p3og-residue-aware-formation-compatibility-evidence-v1"


def _credit_class(configuration: P3OGSemanticConfiguration) -> MaintenanceCreditClass:
    return (
        MaintenanceCreditClass.LOW
        if configuration.maintenance_credit == 1
        else MaintenanceCreditClass.HIGH
    )


def _residue_class(configuration: P3OGSemanticConfiguration) -> ResiduePresenceClass:
    return (
        ResiduePresenceClass.ABSENT
        if configuration.retained_residue is None
        else ResiduePresenceClass.PRESENT
    )


def _selected_kind(
    residue_aware_source: P3OGResidueAwareTickSource,
    configuration: P3OGSemanticConfiguration,
) -> tuple[ResiduePresenceClass, TransitionKind]:
    credit_class = _credit_class(configuration)
    residue_class = _residue_class(configuration)
    matches = tuple(
        rule
        for rule in residue_aware_source.rules
        if rule.maintenance_control is configuration.maintenance_control
        and rule.credit_class is credit_class
        and rule.residue_class is residue_class
    )
    if len(matches) != 1:
        raise ValueError("p3og-residue-aware-tick-rule-lookup")
    return residue_class, matches[0].transition_kind


def residue_aware_semantic_tick(
    source: P3OGSource,
    base_autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> tuple[P3OGSemanticConfiguration, ResidueAwareSemanticTickReceipt]:
    """Apply one total Q_sem tick selected by maintenance, credit, and residue presence."""
    source, _, _, residue_aware_source = validate_residue_aware_tick_source(
        source,
        base_autonomous_source,
        semantic_contract,
        residue_aware_source,
    )
    source, seed = validate_seed(source, seed)
    configuration = _validate_semantic_configuration_validated(source, seed, configuration)
    representative = _representative_native_validated(source, seed, configuration)

    if configuration.boundary is BoundaryState.ALIVE:
        residue_class, selected_kind = _selected_kind(residue_aware_source, configuration)
        after_native, native_receipt = _transition_validated(
            source,
            seed,
            representative,
            selected_kind,
        )
        mode = SemanticOperationMode.NATIVE_QUOTIENT
    else:
        residue_class = None
        selected_kind = TransitionKind.IDLE
        after_native, native_receipt = _transition_validated(
            source,
            seed,
            representative,
            selected_kind,
        )
        mode = SemanticOperationMode.REMOVED_TOTALIZATION

    after = _semantic_from_native_validated(after_native)
    fields = (
        mode,
        residue_class,
        selected_kind,
        configuration.configuration_digest,
        representative.state_digest,
        native_receipt.receipt_digest,
        after_native.state_digest,
        after.configuration_digest,
    )
    receipt = ResidueAwareSemanticTickReceipt(
        *fields,
        residue_aware_tick_digest("residue-aware-semantic-tick", *fields),
    )
    return after, receipt


def build_p3og_residue_aware_formation_compatibility_evidence(
    source: P3OGSource,
    base_autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
) -> P3OGResidueAwareFormationCompatibilityEvidence:
    """Freshly prove that the residue-aware law equals v1 on the entire formation genealogy."""
    source, base_autonomous_source, semantic_contract, residue_aware_source = (
        validate_residue_aware_tick_source(
            source,
            base_autonomous_source,
            semantic_contract,
            residue_aware_source,
        )
    )
    bridge_evidence = validate_p3og_semantic_formation_bridge_evidence(
        source,
        base_autonomous_source,
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
        raise ValueError("p3og-residue-aware-tick-selection") from exc
    source, seed = validate_seed(source, seed)
    if seed.seed_digest != binding.selected_seed_digest:
        raise ValueError("p3og-residue-aware-tick-selected-seed")

    current = bridge_evidence.q_seed
    ticks: list[ResidueAwareSemanticTickReceipt] = []
    all_steps_residue_absent = current.retained_residue is None
    for step in bridge_evidence.steps:
        if current.configuration_digest != step.before_configuration_digest:
            raise ValueError("p3og-residue-aware-tick-formation-before-drift")
        if current.retained_residue is not None:
            raise ValueError("p3og-residue-aware-tick-formation-residue-present")
        after, receipt = residue_aware_semantic_tick(
            source,
            base_autonomous_source,
            semantic_contract,
            residue_aware_source,
            seed,
            current,
        )
        if receipt.residue_class is not ResiduePresenceClass.ABSENT:
            raise ValueError("p3og-residue-aware-tick-formation-class-drift")
        if receipt.selected_kind is not step.semantic_tick.selected_kind:
            raise ValueError("p3og-residue-aware-tick-formation-kind-drift")
        if after.configuration_digest != step.after_configuration_digest:
            raise ValueError("p3og-residue-aware-tick-formation-after-drift")
        ticks.append(receipt)
        current = after
        all_steps_residue_absent = all_steps_residue_absent and current.retained_residue is None

    if current.configuration_digest != bridge_evidence.final_configuration.configuration_digest:
        raise ValueError("p3og-residue-aware-tick-formation-final-drift")
    if not all_steps_residue_absent:
        raise ValueError("p3og-residue-aware-tick-formation-not-absent")

    status = ResidueAwareFormationCompatibilityStatus.WITNESSED
    reason = "residue-aware-law-exactly-equals-v1-over-absent-residue-formation-genealogy"
    fields = (
        EVIDENCE_VERSION,
        residue_aware_source.source_digest,
        bridge_evidence.evidence_digest,
        seed.seed_digest,
        bridge_evidence.q_seed,
        tuple(ticks),
        current,
        all_steps_residue_absent,
        bridge_evidence.first_closure_step,
        status,
        reason,
        0,
        P3OG_RESIDUE_AWARE_TICK_NONCLAIMS,
    )
    return P3OGResidueAwareFormationCompatibilityEvidence(
        *fields,
        residue_aware_tick_digest(
            "residue-aware-formation-compatibility-evidence",
            *fields,
        ),
    )


def _preflight_compatibility(
    evidence: P3OGResidueAwareFormationCompatibilityEvidence,
) -> None:
    try:
        q_seed = evidence.q_seed
        ticks = evidence.ticks
        final_configuration = evidence.final_configuration
        all_absent = evidence.all_steps_residue_absent
        first_closure_step = evidence.first_closure_step
        status = evidence.status
        reason = evidence.reason
        promotions = evidence.promotions
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-residue-aware-tick-compatibility-fields") from exc
    if (
        type(q_seed) is not P3OGSemanticConfiguration
        or type(ticks) is not tuple
        or len(ticks) > 126
        or any(type(tick) is not ResidueAwareSemanticTickReceipt for tick in ticks)
        or type(final_configuration) is not P3OGSemanticConfiguration
        or type(all_absent) is not bool
        or type(first_closure_step) is not int
        or not 1 <= first_closure_step <= 126
        or type(status) is not ResidueAwareFormationCompatibilityStatus
        or type(reason) is not str
        or type(promotions) is not int
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-residue-aware-tick-compatibility-shape")


def validate_p3og_residue_aware_formation_compatibility_evidence(
    source: P3OGSource,
    base_autonomous_source: P3OGAutonomousTickSource,
    semantic_contract: P3OGSemanticConfigurationContract,
    residue_aware_source: P3OGResidueAwareTickSource,
    formation_contract: P3OGNativeFormationContract,
    bridge_contract: P3OGSemanticFormationBridgeContract,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    bridge_evidence: P3OGSemanticFormationBridgeEvidence,
    evidence: P3OGResidueAwareFormationCompatibilityEvidence,
) -> P3OGResidueAwareFormationCompatibilityEvidence:
    if type(evidence) is not P3OGResidueAwareFormationCompatibilityEvidence:
        raise ValueError("p3og-residue-aware-tick-compatibility-type")
    _preflight_compatibility(evidence)
    try:
        expected = build_p3og_residue_aware_formation_compatibility_evidence(
            source,
            base_autonomous_source,
            semantic_contract,
            residue_aware_source,
            formation_contract,
            bridge_contract,
            binding,
            formation_source,
            formation_evidence,
            bridge_evidence,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-residue-aware-tick-compatibility-malformed") from exc
    if not equal:
        raise ValueError("p3og-residue-aware-tick-compatibility-drift")
    return replace(expected)

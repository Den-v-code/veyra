"""Pre-selection contract and post-selection bindings for P3-OG native formation."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_source import (
    validate_autonomous_tick_source,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_formation_history_codec import (
    formation_history_digest,
)
from .prime_power_observer_genesis_p3og_native_formation_codec import (
    native_formation_digest,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationBinding,
    P3OGNativeFormationContract,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_source import (
    _deterministic_select_validated,
)
from .prime_power_observer_genesis_p3og_types import (
    DeterministicSelectionReceipt,
    P3OGSource,
)

CONTRACT_VERSION = "p3og-native-formation-contract-v1"
BINDING_VERSION = "p3og-native-formation-binding-v1"
SOURCE_VERSION = "p3og-native-formation-source-v2"
FORMATION_STATE_RULE_ID = "operational-q-plus-departure-memory-v1"
FORMATION_RULE_ID = "autonomous-first-return-derives-native-formation-v1"
RESOURCE_RULE_ID = "active-feedback-orbit-period-plus-credit-minus-one-v1"
MAX_FORMATION_TICKS = 126


def p3og_native_formation_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> P3OGNativeFormationContract:
    """Commit formation semantics/resource bounds without selection or outcome."""
    _, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    fields = (
        CONTRACT_VERSION,
        FORMATION_STATE_RULE_ID,
        FORMATION_RULE_ID,
        RESOURCE_RULE_ID,
        MAX_FORMATION_TICKS,
        autonomous_source.projection_rule_id,
        autonomous_source.closure_rule_id,
    )
    # Use the already-live history contract domain so the existing
    # FORMATION_CONTRACT_COMMIT event binds this exact DTO digest.
    contract_digest = formation_history_digest(
        "formation-contract",
        SOURCE_VERSION,
        FORMATION_STATE_RULE_ID,
        FORMATION_RULE_ID,
        RESOURCE_RULE_ID,
        MAX_FORMATION_TICKS,
        autonomous_source.projection_rule_id,
        autonomous_source.closure_rule_id,
    )
    return P3OGNativeFormationContract(*fields, contract_digest)


def validate_native_formation_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    contract: P3OGNativeFormationContract,
) -> tuple[P3OGSource, P3OGAutonomousTickSource, P3OGNativeFormationContract]:
    """Freshly reconstruct the exact pre-selection formation contract."""
    source, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    if type(contract) is not P3OGNativeFormationContract:
        raise ValueError("p3og-native-formation-contract-type")
    try:
        expected = p3og_native_formation_contract(source, autonomous_source)
        equal = compare_digest(canonical_bytes(contract), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-native-formation-contract-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-formation-contract-drift")
    return source, autonomous_source, replace(expected)


def p3og_native_formation_binding(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    contract: P3OGNativeFormationContract,
) -> P3OGNativeFormationBinding:
    """Bind a validated pre-selection contract to deterministic selection only."""
    source, autonomous_source, contract = validate_native_formation_contract(
        source, autonomous_source, contract,
    )
    selection = _deterministic_select_validated(source)
    fields = (
        BINDING_VERSION,
        contract.contract_digest,
        source.source_digest,
        autonomous_source.source_digest,
        selection,
        selection.selected_seed_digest,
    )
    return P3OGNativeFormationBinding(
        *fields,
        native_formation_digest("native-formation-binding", *fields),
    )


def validate_native_formation_binding(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    contract: P3OGNativeFormationContract,
    binding: P3OGNativeFormationBinding,
) -> tuple[
    P3OGSource, P3OGAutonomousTickSource,
    P3OGNativeFormationContract, P3OGNativeFormationBinding,
]:
    """Freshly reconstruct the exact post-selection formation binding."""
    source, autonomous_source, contract = validate_native_formation_contract(
        source, autonomous_source, contract,
    )
    if type(binding) is not P3OGNativeFormationBinding:
        raise ValueError("p3og-native-formation-binding-type")
    try:
        if type(binding.selection) is not DeterministicSelectionReceipt:
            raise ValueError("p3og-native-formation-binding-selection-type")
        expected = p3og_native_formation_binding(source, autonomous_source, contract)
        equal = compare_digest(canonical_bytes(binding), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-native-formation-binding-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-formation-binding-drift")
    return source, autonomous_source, replace(contract), replace(expected)


def validate_legacy_source_against_contract_binding(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    contract: P3OGNativeFormationContract,
    binding: P3OGNativeFormationBinding,
    formation_source: P3OGNativeFormationSource,
) -> tuple[P3OGNativeFormationContract, P3OGNativeFormationBinding, P3OGNativeFormationSource]:
    """Prove the legacy v2 source DTO is only the same post-selection binding."""
    source, autonomous_source, contract, binding = validate_native_formation_binding(
        source, autonomous_source, contract, binding,
    )
    _, _, formation_source = validate_native_formation_source(
        source, autonomous_source, formation_source,
    )
    if (
        formation_source.pressure_source_digest != binding.pressure_source_digest
        or formation_source.autonomous_source_digest != binding.autonomous_source_digest
        or formation_source.formation_state_rule_id != contract.formation_state_rule_id
        or formation_source.formation_rule_id != contract.formation_rule_id
        or formation_source.resource_rule_id != contract.resource_rule_id
        or formation_source.max_formation_ticks != contract.max_formation_ticks
        or formation_source.selection != binding.selection
        or formation_source.selected_seed_digest != binding.selected_seed_digest
    ):
        raise ValueError("p3og-native-formation-legacy-binding-drift")
    return replace(contract), replace(binding), replace(formation_source)


def p3og_native_formation_source(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> P3OGNativeFormationSource:
    """Legacy v2 post-selection binding kept for replay compatibility."""
    source, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    selection = _deterministic_select_validated(source)
    fields = (
        SOURCE_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        selection,
        selection.selected_seed_digest,
        FORMATION_STATE_RULE_ID,
        FORMATION_RULE_ID,
        RESOURCE_RULE_ID,
        MAX_FORMATION_TICKS,
    )
    return P3OGNativeFormationSource(
        *fields,
        native_formation_digest("native-formation-source", *fields),
    )


def validate_native_formation_source(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_source: P3OGNativeFormationSource,
) -> tuple[P3OGSource, P3OGAutonomousTickSource, P3OGNativeFormationSource]:
    """Freshly reconstruct the legacy v2 post-selection replay binding."""
    source, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    if type(formation_source) is not P3OGNativeFormationSource:
        raise ValueError("p3og-native-formation-source-type")
    try:
        # Fail closed before canonical traversal can inspect an attacker-supplied
        # dataclass-like nested selection value.
        if type(formation_source.selection) is not DeterministicSelectionReceipt:
            raise ValueError("p3og-native-formation-source-selection-type")
        expected = p3og_native_formation_source(source, autonomous_source)
        equal = compare_digest(
            canonical_bytes(formation_source),
            canonical_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-native-formation-source-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-formation-source-drift")
    return source, autonomous_source, replace(expected)

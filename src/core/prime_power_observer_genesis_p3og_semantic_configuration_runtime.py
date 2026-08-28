"""Finite semantic configuration quotient for the bounded P3-OG machine."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_runtime import (
    _autonomous_tick_validated,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_source import (
    validate_autonomous_tick_source,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import bounded_int, canonical_bytes
from .prime_power_observer_genesis_p3og_machine_internal import (
    MAX_TRANSITION_COUNT,
    _couple_validated,
    _initial_state_validated,
    _state,
    _transition_validated,
    _validate_state_validated,
)
from .prime_power_observer_genesis_p3og_source import validate_seed
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    CandidateMachineState,
    P3OGSource,
    PrimitiveModeSeed,
    TransitionKind,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_codec import (
    semantic_configuration_digest,
)
from .prime_power_observer_genesis_p3og_semantic_configuration_types import (
    P3OGSemanticConfiguration,
    P3OGSemanticConfigurationContract,
    SemanticCouplingReceipt,
    SemanticOperationMode,
    SemanticTickReceipt,
)

CONTRACT_VERSION = "p3og-semantic-configuration-contract-v1"
STATE_RULE_ID = "candidate-machine-minus-transition-count-and-state-digest-v1"
TICK_RULE_ID = "autonomous-live-plus-removed-idle-quotient-v1"
COUPLE_RULE_ID = "native-live-plus-removed-absorbing-totalization-v1"
READ_RULE_ID = "retained-residue-response-or-none-v1"
RESIDUE_RULE_ID = "retained-residue-projection-v1"
BOUNDARY_RULE_ID = "native-boundary-projection-v1"
ALIVE_RULE_ID = "boundary-equals-alive-v1"
REMOVED_TOTALIZATION_RULE_ID = "removed-absorbing-semantic-totalization-v1"
MAX_INPUT_BITS = 4096


def p3og_semantic_configuration_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> P3OGSemanticConfigurationContract:
    """Commit exact semantic-Q operations and resources before candidate selection."""
    source, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    fields = (
        CONTRACT_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        STATE_RULE_ID,
        TICK_RULE_ID,
        COUPLE_RULE_ID,
        READ_RULE_ID,
        RESIDUE_RULE_ID,
        BOUNDARY_RULE_ID,
        ALIVE_RULE_ID,
        REMOVED_TOTALIZATION_RULE_ID,
        MAX_INPUT_BITS,
        MAX_TRANSITION_COUNT,
    )
    return P3OGSemanticConfigurationContract(
        *fields,
        semantic_configuration_digest("semantic-configuration-contract", *fields),
    )


def validate_semantic_configuration_contract(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    contract: P3OGSemanticConfigurationContract,
) -> tuple[P3OGSource, P3OGAutonomousTickSource, P3OGSemanticConfigurationContract]:
    """Freshly reconstruct the exact selection-free semantic-Q contract."""
    source, autonomous_source = validate_autonomous_tick_source(source, autonomous_source)
    if type(contract) is not P3OGSemanticConfigurationContract:
        raise ValueError("p3og-semantic-configuration-contract-type")
    try:
        expected = p3og_semantic_configuration_contract(source, autonomous_source)
        equal = compare_digest(canonical_bytes(contract), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-configuration-contract-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-configuration-contract-drift")
    return source, autonomous_source, replace(expected)


def _semantic_from_native_validated(
    state: CandidateMachineState,
) -> P3OGSemanticConfiguration:
    """Project one trusted operational state by deleting only evidence monotonicity."""
    fields = (
        state.run_id,
        state.seed_digest,
        state.boundary,
        state.maintenance_control,
        state.phase,
        state.retained_residue,
        state.maintenance_credit,
    )
    return P3OGSemanticConfiguration(
        *fields,
        semantic_configuration_digest("semantic-configuration", *fields),
    )


def semantic_configuration_from_native(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    state: CandidateMachineState,
) -> P3OGSemanticConfiguration:
    """Project a validated native state into the finite semantic carrier."""
    source, seed = validate_seed(source, seed)
    state = _validate_state_validated(source, seed, state)
    return _semantic_from_native_validated(state)


def _representative_native_validated(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> CandidateMachineState:
    """Choose count=0 as a canonical operational representative of one semantic Q."""
    state = _state(
        configuration.run_id,
        configuration.seed_digest,
        configuration.boundary,
        configuration.maintenance_control,
        configuration.phase,
        configuration.retained_residue,
        configuration.maintenance_credit,
        0,
    )
    return _validate_state_validated(source, seed, state)


def _validate_semantic_configuration_validated(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> P3OGSemanticConfiguration:
    if type(configuration) is not P3OGSemanticConfiguration:
        raise ValueError("p3og-semantic-configuration-type")
    try:
        representative = _representative_native_validated(source, seed, configuration)
        expected = _semantic_from_native_validated(representative)
        equal = compare_digest(canonical_bytes(configuration), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-semantic-configuration-malformed") from exc
    if not equal:
        raise ValueError("p3og-semantic-configuration-drift")
    return replace(expected)


def validate_semantic_configuration(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> tuple[P3OGSource, PrimitiveModeSeed, P3OGSemanticConfiguration]:
    """Validate one semantic-Q value against its exact source member."""
    source, seed = validate_seed(source, seed)
    return source, seed, _validate_semantic_configuration_validated(
        source, seed, configuration,
    )


def semantic_q_seed(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
) -> P3OGSemanticConfiguration:
    """Return q_seed in the semantic carrier."""
    source, seed = validate_seed(source, seed)
    return _semantic_from_native_validated(_initial_state_validated(source, seed))


def semantic_tick(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    contract: P3OGSemanticConfigurationContract,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> tuple[P3OGSemanticConfiguration, SemanticTickReceipt]:
    """Apply one total deterministic Q_sem->Q_sem tick."""
    source, autonomous_source, contract = validate_semantic_configuration_contract(
        source, autonomous_source, contract,
    )
    source, seed = validate_seed(source, seed)
    configuration = _validate_semantic_configuration_validated(
        source, seed, configuration,
    )
    representative = _representative_native_validated(source, seed, configuration)
    if configuration.boundary is BoundaryState.ALIVE:
        after_native, native_receipt = _autonomous_tick_validated(
            source, autonomous_source, seed, representative,
        )
        selected_kind = native_receipt.selected_kind
        native_receipt_digest = native_receipt.receipt_digest
        mode = SemanticOperationMode.NATIVE_QUOTIENT
    else:
        # Existing private transition semantics already make REMOVED invariant
        # modulo transition_count/state_digest. IDLE is the canonical witness.
        selected_kind = TransitionKind.IDLE
        after_native, native_receipt = _transition_validated(
            source, seed, representative, selected_kind,
        )
        native_receipt_digest = native_receipt.receipt_digest
        mode = SemanticOperationMode.REMOVED_TOTALIZATION
    after = _semantic_from_native_validated(after_native)
    fields = (
        mode,
        selected_kind,
        configuration.configuration_digest,
        representative.state_digest,
        native_receipt_digest,
        after_native.state_digest,
        after.configuration_digest,
    )
    receipt = SemanticTickReceipt(
        *fields,
        semantic_configuration_digest("semantic-tick", *fields),
    )
    return after, receipt


def semantic_couple(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    contract: P3OGSemanticConfigurationContract,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
    input_value: int,
) -> tuple[P3OGSemanticConfiguration, SemanticCouplingReceipt]:
    """Apply total Q_sem x I -> Q_sem coupling, explicitly totalizing REMOVED."""
    source, _, contract = validate_semantic_configuration_contract(
        source, autonomous_source, contract,
    )
    source, seed = validate_seed(source, seed)
    configuration = _validate_semantic_configuration_validated(
        source, seed, configuration,
    )
    input_value = bounded_int(input_value, "p3og-semantic-coupling-input", MAX_INPUT_BITS)
    if configuration.boundary is BoundaryState.ALIVE:
        representative = _representative_native_validated(source, seed, configuration)
        after_native, native_receipt = _couple_validated(
            source, seed, representative, input_value,
        )
        after = _semantic_from_native_validated(after_native)
        mode = SemanticOperationMode.NATIVE_QUOTIENT
        native_before = representative.state_digest
        native_receipt_digest = native_receipt.receipt_digest
        native_after = after_native.state_digest
        response = native_receipt.response
    else:
        # Public/native coupling has no REMOVED operation. The semantic carrier
        # totalizes it as an absorbing fixed point and records that distinction.
        after = configuration
        mode = SemanticOperationMode.REMOVED_TOTALIZATION
        native_before = None
        native_receipt_digest = None
        native_after = None
        response = None
    fields = (
        mode,
        input_value,
        configuration.configuration_digest,
        native_before,
        native_receipt_digest,
        native_after,
        after.configuration_digest,
        response,
    )
    receipt = SemanticCouplingReceipt(
        *fields,
        semantic_configuration_digest("semantic-coupling", *fields),
    )
    return after, receipt


def semantic_read(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> int | None:
    """Read the same response determined by the retained residue, or None before coupling."""
    source, seed = validate_seed(source, seed)
    configuration = _validate_semantic_configuration_validated(
        source, seed, configuration,
    )
    if configuration.retained_residue is None:
        return None
    period = len(seed.cycle) - 1
    return seed.cycle[configuration.retained_residue % period]


def semantic_residue(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> int | None:
    """Return the native retained-residue projection."""
    source, seed = validate_seed(source, seed)
    return _validate_semantic_configuration_validated(
        source, seed, configuration,
    ).retained_residue


def semantic_boundary(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> BoundaryState:
    """Return the native boundary projection."""
    source, seed = validate_seed(source, seed)
    return _validate_semantic_configuration_validated(
        source, seed, configuration,
    ).boundary


def semantic_alive(
    source: P3OGSource,
    seed: PrimitiveModeSeed,
    configuration: P3OGSemanticConfiguration,
) -> bool:
    """Return whether the semantic configuration carries the live native boundary."""
    return semantic_boundary(source, seed, configuration) is BoundaryState.ALIVE


def semantic_state_space_size(source: P3OGSource, seed: PrimitiveModeSeed) -> int:
    """Return the exact finite carrier size for one fixed source/seed identity."""
    source, seed = validate_seed(source, seed)
    period = max(len(seed.cycle) - 1, 1)
    modulus = source.prime ** (source.depth + 1)
    live = 2 * period * source.maintenance_credit * (modulus + 1)
    removed = 2
    return live + removed

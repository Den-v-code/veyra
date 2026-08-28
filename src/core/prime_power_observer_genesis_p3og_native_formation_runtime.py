"""Native UNFORMED->ALIVE first-return pressure over autonomous P3-OG ticks."""

from __future__ import annotations

from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_runtime import (
    _autonomous_tick_validated,
    _configuration_projection,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_source import (
    validate_autonomous_tick_source,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_machine_internal import (
    _initial_state_validated,
    _validate_state_validated,
)
from .prime_power_observer_genesis_p3og_native_formation_codec import (
    native_formation_digest,
)
from .prime_power_observer_genesis_p3og_native_formation_source import (
    validate_native_formation_source,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    NativeFormationBoundary,
    NativeFormationState,
    NativeFormationStatus,
    NativeFormationTickReceipt,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
    P3OG_NATIVE_FORMATION_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_types import BoundaryState, P3OGSource

EVIDENCE_VERSION = "p3og-native-formation-evidence-v2"


def _projection_key(state) -> bytes:
    return canonical_bytes(_configuration_projection(state))


def _native_formation_state(
    source: P3OGSource,
    formation_source: P3OGNativeFormationSource,
    native_state,
    departed: bool,
    tick_count: int,
) -> NativeFormationState:
    """Build Q_form; its ALIVE boundary is derived, never caller-selected."""
    if type(departed) is not bool or type(tick_count) is not int or tick_count < 0:
        raise ValueError("p3og-native-formation-state-metadata")
    selection = formation_source.selection
    try:
        seed = source.seeds[selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-native-formation-selection") from exc
    native_state = _validate_state_validated(source, seed, native_state)
    if tick_count != native_state.transition_count:
        raise ValueError("p3og-native-formation-state-tick-count")
    initial = _initial_state_validated(source, seed)
    same_initial = compare_digest(_projection_key(native_state), _projection_key(initial))
    boundary = (
        NativeFormationBoundary.ALIVE
        if departed and same_initial and native_state.boundary is BoundaryState.ALIVE
        else NativeFormationBoundary.UNFORMED
    )
    run_id = native_formation_digest(
        "native-formation-run",
        formation_source.source_digest,
        formation_source.selected_seed_digest,
    )
    fields = (
        run_id,
        formation_source.source_digest,
        formation_source.selected_seed_digest,
        boundary,
        departed,
        native_state,
        tick_count,
    )
    return NativeFormationState(
        *fields,
        native_formation_digest("native-formation-state", *fields),
    )


def _native_formation_seed_state_validated(
    source: P3OGSource,
    formation_source: P3OGNativeFormationSource,
) -> NativeFormationState:
    selection = formation_source.selection
    seed = source.seeds[selection.selected_index]
    native_initial = _initial_state_validated(source, seed)
    return _native_formation_state(source, formation_source, native_initial, False, 0)


def _validate_native_formation_state(
    source: P3OGSource,
    formation_source: P3OGNativeFormationSource,
    state: NativeFormationState,
) -> NativeFormationState:
    if type(state) is not NativeFormationState:
        raise ValueError("p3og-native-formation-state-type")
    try:
        expected = _native_formation_state(
            source,
            formation_source,
            state.native_state,
            state.departed,
            state.tick_count,
        )
        equal = compare_digest(canonical_bytes(state), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-native-formation-state-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-formation-state-drift")
    return expected


def _native_formation_tick_validated(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_source: P3OGNativeFormationSource,
    state: NativeFormationState,
) -> tuple[NativeFormationState, NativeFormationTickReceipt]:
    """Advance Q_form by one source-defined autonomous operational tick."""
    state = _validate_native_formation_state(source, formation_source, state)
    if state.boundary is NativeFormationBoundary.ALIVE:
        raise ValueError("p3og-native-formation-already-closed")
    selection = formation_source.selection
    seed = source.seeds[selection.selected_index]
    if state.native_state.boundary is BoundaryState.REMOVED:
        raise ValueError("p3og-native-formation-native-removed")
    initial_native = _initial_state_validated(source, seed)
    after_native, autonomous_receipt = _autonomous_tick_validated(
        source,
        autonomous_source,
        seed,
        state.native_state,
    )
    after_key = _projection_key(after_native)
    initial_key = _projection_key(initial_native)
    became_departed = (not state.departed) and not compare_digest(after_key, initial_key)
    departed = state.departed or not compare_digest(after_key, initial_key)
    after = _native_formation_state(
        source,
        formation_source,
        after_native,
        departed,
        state.tick_count + 1,
    )
    became_alive = (
        state.boundary is NativeFormationBoundary.UNFORMED
        and after.boundary is NativeFormationBoundary.ALIVE
    )
    receipt_fields = (
        after.tick_count,
        state.state_digest,
        autonomous_receipt,
        after.state_digest,
        became_departed,
        became_alive,
    )
    receipt = NativeFormationTickReceipt(
        *receipt_fields,
        native_formation_digest("native-formation-tick", *receipt_fields),
    )
    return after, receipt


def run_p3og_native_formation(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_source: P3OGNativeFormationSource,
) -> P3OGNativeFormationEvidence:
    """Replay first native formation closure from exact outcome-free sources."""
    source, autonomous_source, formation_source = validate_native_formation_source(
        source,
        autonomous_source,
        formation_source,
    )
    return _run_p3og_native_formation_validated(source, autonomous_source, formation_source)


def _run_p3og_native_formation_validated(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_source: P3OGNativeFormationSource,
) -> P3OGNativeFormationEvidence:
    selection = formation_source.selection
    seed = source.seeds[selection.selected_index]
    initial = _native_formation_seed_state_validated(source, formation_source)
    state = initial
    ticks: list[NativeFormationTickReceipt] = []

    period = max(len(seed.cycle) - 1, 1)
    # For this exact v1 feedback grammar, maintenance control remains ACTIVE.
    # HIGH can only self-loop/phase-cycle/decrement toward LOW; once LOW, the
    # run can only remove, restore full credit, or phase-cycle at LOW. Therefore
    # any first return/refutation occurs within (credit - 1) + period ticks.
    # This is also safely below the shared codec's 256-item container ceiling
    # for the current source caps (63 + 64 - 1 = 126).
    state_space_bound = period + source.maintenance_credit - 1
    if state_space_bound > formation_source.max_formation_ticks:
        raise ValueError("p3og-native-formation-source-resource-bound")
    visited_after_departure: set[bytes] = set()
    status: NativeFormationStatus | None = None
    reason: str | None = None
    closure_step: int | None = None

    for step_index in range(1, state_space_bound + 1):
        before = state
        state, receipt = _native_formation_tick_validated(
            source,
            autonomous_source,
            formation_source,
            state,
        )
        ticks.append(receipt)

        if state.boundary is NativeFormationBoundary.ALIVE:
            status = NativeFormationStatus.WITNESSED
            reason = "least-native-formation-return-witnessed"
            closure_step = step_index
            break
        if state.native_state.boundary is BoundaryState.REMOVED:
            status = NativeFormationStatus.REFUTED
            reason = "native-boundary-removed-before-formation"
            break

        current_key = _projection_key(state.native_state)
        initial_key = _projection_key(initial.native_state)
        if not state.departed and compare_digest(current_key, initial_key):
            # A deterministic self-loop at the seed cannot later become a genuine departure.
            status = NativeFormationStatus.REFUTED
            reason = "native-formation-never-departs"
            break
        if state.departed:
            if current_key in visited_after_departure:
                status = NativeFormationStatus.REFUTED
                reason = "native-formation-entered-disjoint-cycle"
                break
            visited_after_departure.add(current_key)
        if before.tick_count + 1 != state.tick_count:
            raise ValueError("p3og-native-formation-tick-count")

    if status is None or reason is None:
        raise ValueError("p3og-native-formation-state-space-bound")

    captured = tuple(ticks)
    genealogy = native_formation_digest(
        "native-formation-genealogy",
        formation_source.source_digest,
        initial,
        captured,
        state,
    )
    fields = (
        EVIDENCE_VERSION,
        formation_source.source_digest,
        initial,
        captured,
        state,
        state_space_bound,
        closure_step,
        status,
        reason,
        genealogy,
        0,
        P3OG_NATIVE_FORMATION_NONCLAIMS,
    )
    return P3OGNativeFormationEvidence(
        *fields,
        native_formation_digest("native-formation-evidence", *fields),
    )

"""State-extensional autonomous transition replay for bounded P3-OG pressure."""

from __future__ import annotations

from dataclasses import fields
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_autonomous_tick_codec import (
    autonomous_tick_digest,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_source import (
    PROJECTION_EXCLUDED_FIELDS,
    validate_autonomous_tick_source,
)
from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    AutonomousTickReceipt,
    AutonomousTickStatus,
    MaintenanceCreditClass,
    P3OGAutonomousFirstClosureEvidence,
    P3OGAutonomousTickSource,
    P3OG_AUTONOMOUS_TICK_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_machine_internal import (
    _initial_state_validated,
    _transition_validated,
    _validate_state_validated,
)
from .prime_power_observer_genesis_p3og_source import (
    _deterministic_select_validated,
    validate_seed,
)
from .prime_power_observer_genesis_p3og_types import (
    BoundaryState,
    CandidateMachineState,
    P3OGSource,
    PrimitiveModeSeed,
    TransitionKind,
)

logger = logging.getLogger(__name__)
EVIDENCE_VERSION = "p3og-autonomous-first-closure-evidence-v1"
_PROJECTION_EXCLUSIONS = frozenset(PROJECTION_EXCLUDED_FIELDS)


def _configuration_projection(
    state: CandidateMachineState,
) -> tuple[tuple[str, object], ...]:
    """Project exact native configuration, excluding only evidence monotonicity."""
    if type(state) is not CandidateMachineState:
        raise ValueError("p3og-autonomous-tick-state-type")
    state_fields = fields(state)
    excluded = {
        field.name for field in state_fields if field.name in _PROJECTION_EXCLUSIONS
    }
    if excluded != _PROJECTION_EXCLUSIONS:
        raise ValueError("p3og-autonomous-tick-state-schema")
    return tuple(
        (field.name, getattr(state, field.name))
        for field in state_fields
        if field.name not in _PROJECTION_EXCLUSIONS
    )


def _same_projection(
    left: tuple[tuple[str, object], ...],
    right: tuple[tuple[str, object], ...],
) -> bool:
    """Compare typed native configurations without object equality dispatch."""
    return compare_digest(canonical_bytes(left), canonical_bytes(right))


def _credit_class(state: CandidateMachineState) -> MaintenanceCreditClass:
    """Classify one validated live state's maintenance credit exactly."""
    if state.boundary is BoundaryState.REMOVED or state.maintenance_credit < 1:
        raise ValueError("p3og-autonomous-tick-removed-state")
    return (
        MaintenanceCreditClass.LOW
        if state.maintenance_credit == 1
        else MaintenanceCreditClass.HIGH
    )


def _selected_kind(
    autonomous_source: P3OGAutonomousTickSource,
    state: CandidateMachineState,
) -> TransitionKind:
    """Derive the next native transition from current Q and committed code only."""
    credit_class = _credit_class(state)
    matches = tuple(
        rule.transition_kind
        for rule in autonomous_source.rules
        if rule.maintenance_control is state.maintenance_control
        and rule.credit_class is credit_class
    )
    if len(matches) != 1:
        raise ValueError("p3og-autonomous-tick-rule-resolution")
    return matches[0]


def autonomous_tick(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    seed: PrimitiveModeSeed,
    state: CandidateMachineState,
) -> tuple[CandidateMachineState, AutonomousTickReceipt]:
    """Apply one source-defined Q->Q tick with no caller-supplied transition kind."""
    logger.debug("p3og.autonomous_tick.tick entry")
    source, autonomous_source = validate_autonomous_tick_source(
        source,
        autonomous_source,
    )
    source, seed = validate_seed(source, seed)
    state = _validate_state_validated(source, seed, state)
    if state.boundary is BoundaryState.REMOVED:
        raise ValueError("p3og-boundary-removed")
    result = _autonomous_tick_validated(source, autonomous_source, seed, state)
    logger.debug(
        "p3og.autonomous_tick.tick exit kind=%s",
        result[1].selected_kind.value,
    )
    return result


def _autonomous_tick_validated(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    seed: PrimitiveModeSeed,
    state: CandidateMachineState,
) -> tuple[CandidateMachineState, AutonomousTickReceipt]:
    """Apply one already-source-validated state-feedback transition."""
    before_projection = _configuration_projection(state)
    selected_kind = _selected_kind(autonomous_source, state)
    after, transition = _transition_validated(source, seed, state, selected_kind)
    _validate_state_validated(source, seed, after)
    after_projection = _configuration_projection(after)
    before_projection_digest = autonomous_tick_digest(
        "state-projection",
        before_projection,
    )
    after_projection_digest = autonomous_tick_digest(
        "state-projection",
        after_projection,
    )
    receipt_fields = (
        selected_kind,
        state.state_digest,
        transition,
        after.state_digest,
        before_projection_digest,
        after_projection_digest,
    )
    receipt = AutonomousTickReceipt(
        *receipt_fields,
        autonomous_tick_digest("autonomous-tick", *receipt_fields),
    )
    return after, receipt


def run_p3og_autonomous_first_closure(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> P3OGAutonomousFirstClosureEvidence:
    """Replay the selected candidate until first return, removal, or a disjoint cycle."""
    logger.debug("p3og.autonomous_tick.run entry")
    source, autonomous_source = validate_autonomous_tick_source(
        source,
        autonomous_source,
    )
    result = _run_p3og_autonomous_first_closure_validated(
        source,
        autonomous_source,
    )
    logger.debug("p3og.autonomous_tick.run exit status=%s", result.status.value)
    return result


def _run_p3og_autonomous_first_closure_validated(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
) -> P3OGAutonomousFirstClosureEvidence:
    """Replay one deterministic selected Q->Q genealogy from its fresh entry."""
    selection = _deterministic_select_validated(source)
    try:
        seed = source.seeds[selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-autonomous-tick-selection") from exc
    if seed.seed_digest != selection.selected_seed_digest:
        raise ValueError("p3og-autonomous-tick-selected-seed")

    initial = _initial_state_validated(source, seed)
    _validate_state_validated(source, seed, initial)
    initial_projection = _configuration_projection(initial)
    initial_key = canonical_bytes(initial_projection)
    initial_projection_digest = autonomous_tick_digest(
        "state-projection",
        initial_projection,
    )

    period = max(len(seed.cycle) - 1, 1)
    state_space_bound = period * source.maintenance_credit + 1
    state = initial
    ticks: list[AutonomousTickReceipt] = []
    visited = {initial_key}
    departed = False
    closure_step: int | None = None
    status: AutonomousTickStatus | None = None
    reason: str | None = None

    for step_index in range(1, state_space_bound + 1):
        state, receipt = _autonomous_tick_validated(
            source,
            autonomous_source,
            seed,
            state,
        )
        ticks.append(receipt)

        if state.boundary is BoundaryState.REMOVED:
            status = AutonomousTickStatus.REFUTED
            reason = "autonomous-boundary-removed-before-closure"
            break

        projection = _configuration_projection(state)
        projection_key = canonical_bytes(projection)
        if _same_projection(projection, initial_projection):
            if departed:
                closure_step = step_index
                status = AutonomousTickStatus.WITNESSED
                reason = "least-autonomous-native-state-return-witnessed"
            else:
                status = AutonomousTickStatus.REFUTED
                reason = "autonomous-native-state-never-departs"
            break

        departed = True
        if projection_key in visited:
            status = AutonomousTickStatus.REFUTED
            reason = "autonomous-native-state-entered-disjoint-cycle"
            break
        visited.add(projection_key)

    if status is None or reason is None:
        raise ValueError("p3og-autonomous-tick-state-space-bound")

    captured = tuple(ticks)
    genealogy = autonomous_tick_digest(
        "autonomous-tick-genealogy",
        autonomous_source.source_digest,
        selection,
        initial_projection_digest,
        initial,
        captured,
        state,
    )
    evidence_fields = (
        EVIDENCE_VERSION,
        autonomous_source.source_digest,
        selection,
        seed.seed_digest,
        initial,
        captured,
        state,
        state_space_bound,
        closure_step,
        status,
        reason,
        genealogy,
        0,
        P3OG_AUTONOMOUS_TICK_NONCLAIMS,
    )
    return P3OGAutonomousFirstClosureEvidence(
        *evidence_fields,
        autonomous_tick_digest(
            "autonomous-first-closure-evidence",
            *evidence_fields,
        ),
    )

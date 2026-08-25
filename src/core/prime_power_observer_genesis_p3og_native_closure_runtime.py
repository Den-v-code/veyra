"""Fresh native-transition replay for bounded P3-OG first-closure pressure."""

from __future__ import annotations

from dataclasses import fields
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_codec import canonical_bytes
from .prime_power_observer_genesis_p3og_machine_internal import (
    _initial_state_validated,
    _transition_validated,
    _validate_state_validated,
)
from .prime_power_observer_genesis_p3og_native_closure_codec import (
    native_closure_digest,
)
from .prime_power_observer_genesis_p3og_native_closure_source import (
    PROJECTION_EXCLUDED_FIELDS,
    validate_native_closure_source,
)
from .prime_power_observer_genesis_p3og_native_closure_types import (
    NativeClosureStatus,
    NativeClosureStepReceipt,
    P3OGNativeClosureSource,
    P3OGNativeFirstClosureEvidence,
    P3OG_NATIVE_CLOSURE_NONCLAIMS,
)
from .prime_power_observer_genesis_p3og_types import (
    CandidateMachineState,
    P3OGSource,
)

logger = logging.getLogger(__name__)
EVIDENCE_VERSION = "p3og-native-first-closure-evidence-v1"
_CLOSURE_PROJECTION_EXCLUSIONS = frozenset(PROJECTION_EXCLUDED_FIELDS)


def _closure_projection(
    state: CandidateMachineState,
) -> tuple[tuple[str, object], ...]:
    """Project native configuration while excluding monotone evidence identity."""
    logger.debug("p3og.native_closure.projection entry")
    if type(state) is not CandidateMachineState:
        raise ValueError("p3og-native-closure-state-type")
    state_fields = fields(state)
    excluded = {
        field.name
        for field in state_fields
        if field.name in _CLOSURE_PROJECTION_EXCLUSIONS
    }
    if excluded != _CLOSURE_PROJECTION_EXCLUSIONS:
        raise ValueError("p3og-native-closure-state-schema")
    result = tuple(
        (field.name, getattr(state, field.name))
        for field in state_fields
        if field.name not in _CLOSURE_PROJECTION_EXCLUSIONS
    )
    logger.debug("p3og.native_closure.projection exit fields=%d", len(result))
    return result


def _same_projection(
    left: tuple[tuple[str, object], ...],
    right: tuple[tuple[str, object], ...],
) -> bool:
    """Compare typed projections without trusting object equality dispatch."""
    return compare_digest(canonical_bytes(left), canonical_bytes(right))


def run_p3og_native_first_closure(
    source: P3OGSource,
    closure_source: P3OGNativeClosureSource,
) -> P3OGNativeFirstClosureEvidence:
    """Replay the source-bound native transition to its first projected return."""
    logger.debug("p3og.native_closure.run entry")
    source, closure_source = validate_native_closure_source(source, closure_source)
    result = _run_p3og_native_first_closure_validated(source, closure_source)
    logger.debug("p3og.native_closure.run exit status=%s", result.status.value)
    return result


def _run_p3og_native_first_closure_validated(
    source: P3OGSource,
    closure_source: P3OGNativeClosureSource,
) -> P3OGNativeFirstClosureEvidence:
    """Replay one exact selected machine from its fresh operational entry."""
    selection = closure_source.selection
    try:
        seed = source.seeds[selection.selected_index]
    except (AttributeError, IndexError, TypeError) as exc:
        raise ValueError("p3og-native-closure-selection") from exc
    if seed.seed_digest != closure_source.selected_seed_digest:
        raise ValueError("p3og-native-closure-selected-seed")

    initial = _initial_state_validated(source, seed)
    _validate_state_validated(source, seed, initial)
    initial_projection = _closure_projection(initial)
    initial_projection_digest = native_closure_digest(
        "state-projection",
        initial_projection,
    )

    state = initial
    steps: list[NativeClosureStepReceipt] = []
    departed = False
    closure_step: int | None = None
    max_steps = closure_source.step_bound
    if max_steps != len(seed.cycle) - 1:
        raise ValueError("p3og-native-closure-step-bound")

    for step_index in range(1, max_steps + 1):
        before = state
        before_projection = _closure_projection(before)
        after, transition = _transition_validated(
            source,
            seed,
            before,
            closure_source.transition_kind,
        )
        _validate_state_validated(source, seed, after)
        after_projection = _closure_projection(after)
        before_projection_digest = native_closure_digest(
            "state-projection",
            before_projection,
        )
        after_projection_digest = native_closure_digest(
            "state-projection",
            after_projection,
        )
        became_departed = (
            not departed
            and not _same_projection(after_projection, initial_projection)
        )
        departed = departed or became_departed
        became_closed = departed and _same_projection(
            after_projection,
            initial_projection,
        )
        receipt_fields = (
            step_index,
            before.state_digest,
            transition,
            after.state_digest,
            before_projection_digest,
            after_projection_digest,
            became_departed,
            became_closed,
        )
        steps.append(
            NativeClosureStepReceipt(
                *receipt_fields,
                native_closure_digest("native-closure-step", *receipt_fields),
            ),
        )
        state = after
        if became_closed:
            closure_step = step_index
            break

    captured = tuple(steps)
    if closure_step is not None:
        status = NativeClosureStatus.WITNESSED
        reason = "least-native-state-return-witnessed"
    elif not departed:
        status = NativeClosureStatus.REFUTED
        reason = "native-state-never-departs"
    else:
        status = NativeClosureStatus.REFUTED
        reason = "native-state-return-not-witnessed-within-bound"

    genealogy = native_closure_digest(
        "native-closure-genealogy",
        closure_source.source_digest,
        initial_projection_digest,
        initial,
        captured,
        state,
    )
    evidence_fields = (
        EVIDENCE_VERSION,
        closure_source.source_digest,
        initial,
        captured,
        state,
        closure_step,
        status,
        reason,
        genealogy,
        0,
        P3OG_NATIVE_CLOSURE_NONCLAIMS,
    )
    return P3OGNativeFirstClosureEvidence(
        *evidence_fields,
        native_closure_digest(
            "native-first-closure-evidence",
            *evidence_fields,
        ),
    )

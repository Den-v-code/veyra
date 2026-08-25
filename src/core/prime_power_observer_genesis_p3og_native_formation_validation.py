"""Fresh replay validation for P3-OG native formation pressure v2."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    AutonomousTickReceipt,
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_native_formation_runtime import (
    _run_p3og_native_formation_validated,
)
from .prime_power_observer_genesis_p3og_native_formation_source import (
    MAX_FORMATION_TICKS,
    validate_native_formation_source,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    NativeFormationState,
    NativeFormationTickReceipt,
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_types import (
    CandidateMachineState,
    P3OGSource,
    TransitionReceipt,
)


def _preflight_evidence(evidence: P3OGNativeFormationEvidence) -> None:
    """Reject hostile nested shapes before deep canonical/evidence traversal."""
    try:
        ticks = evidence.ticks
        initial = evidence.initial_state
        final = evidence.final_state
        nonclaims = evidence.nonclaims
    except AttributeError as exc:
        raise ValueError("p3og-native-formation-evidence-fields") from exc
    if (
        type(initial) is not NativeFormationState
        or type(final) is not NativeFormationState
        or type(initial.native_state) is not CandidateMachineState
        or type(final.native_state) is not CandidateMachineState
        or type(ticks) is not tuple
        or len(ticks) > MAX_FORMATION_TICKS
        or type(nonclaims) is not tuple
        or any(type(item) is not str for item in nonclaims)
    ):
        raise ValueError("p3og-native-formation-evidence-shape")
    for tick in ticks:
        if type(tick) is not NativeFormationTickReceipt:
            raise ValueError("p3og-native-formation-evidence-tick-type")
        auto = tick.autonomous_tick
        if (
            type(auto) is not AutonomousTickReceipt
            or type(auto.transition) is not TransitionReceipt
        ):
            raise ValueError("p3og-native-formation-evidence-autonomous-tick-type")


def validate_p3og_native_formation_evidence(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_source: P3OGNativeFormationSource,
    evidence: P3OGNativeFormationEvidence,
) -> P3OGNativeFormationEvidence:
    """Freshly reconstruct exact Q_form genealogy and verdict."""
    source, autonomous_source, formation_source = validate_native_formation_source(
        source,
        autonomous_source,
        formation_source,
    )
    if type(evidence) is not P3OGNativeFormationEvidence:
        raise ValueError("p3og-native-formation-evidence-type")
    _preflight_evidence(evidence)
    try:
        expected = _run_p3og_native_formation_validated(
            source,
            autonomous_source,
            formation_source,
        )
        equal = compare_digest(evidence_bytes(evidence), evidence_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-native-formation-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-formation-evidence-drift")
    return replace(expected)

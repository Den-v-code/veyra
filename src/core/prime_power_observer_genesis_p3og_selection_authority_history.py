"""Bind one precommitted local one-shot authority to one typed formation history."""

from __future__ import annotations

from dataclasses import replace
from hmac import compare_digest
from pathlib import Path

from .prime_power_observer_genesis_p3og_autonomous_tick_types import (
    P3OGAutonomousTickSource,
)
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, digest
from .prime_power_observer_genesis_p3og_formation_history import (
    validate_formation_history_plan,
    validate_p3og_formation_history_evidence,
)
from .prime_power_observer_genesis_p3og_formation_history_types import (
    P3OGFormationHistoryEvidence,
    P3OGFormationHistoryPlan,
)
from .prime_power_observer_genesis_p3og_native_formation_types import (
    P3OGNativeFormationEvidence,
    P3OGNativeFormationSource,
)
from .prime_power_observer_genesis_p3og_one_shot_selection_types import (
    P3OGOneShotSelectionReceipt,
    P3OGOneShotSelectionSource,
    P3OGSelectionCapability,
)
from .prime_power_observer_genesis_p3og_selection_local_authority import (
    consume_p3og_selection_capability_locally,
    p3og_selection_local_authority_attempt_digest,
    p3og_selection_local_authority_reservation,
    read_p3og_selection_local_authority,
    validate_p3og_selection_local_authority,
    validate_p3og_selection_local_authority_receipt,
)
from .prime_power_observer_genesis_p3og_selection_local_authority_types import (
    P3OGSelectionLocalAuthorityEvidence,
    P3OGSelectionLocalAuthorityReceipt,
    P3OGSelectionLocalAuthorityState,
)
from .prime_power_observer_genesis_p3og_selection_authority_history_types import (
    P3OG_SELECTION_AUTHORITY_HISTORY_BOUNDARY,
    P3OG_SELECTION_AUTHORITY_HISTORY_NONCLAIMS,
    P3OGSelectionAuthorityHistoryBinding,
    P3OGSelectionAuthorityHistoryPlan,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource, PrimitiveModeSeed

PLAN_VERSION = "p3og-selection-authority-history-plan-v1"
BINDING_VERSION = "p3og-selection-authority-history-binding-v1"


def _plan_core(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_history_plan: P3OGFormationHistoryPlan,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    reserved: P3OGSelectionLocalAuthorityReceipt,
) -> P3OGSelectionAuthorityHistoryPlan:
    source, autonomous_source, formation_history_plan = validate_formation_history_plan(
        source,
        autonomous_source,
        selection_source,
        available,
        formation_history_plan,
    )
    if not validate_p3og_selection_local_authority_receipt(reserved):
        raise ValueError("p3og-selection-authority-history-reserved-receipt")
    if reserved.state is not P3OGSelectionLocalAuthorityState.RESERVED:
        raise ValueError("p3og-selection-authority-history-reserved-state")
    expected_reservation = p3og_selection_local_authority_reservation(
        source,
        selection_source,
        available,
        reserved.reservation.reservation_id,
    )
    if reserved.reservation != expected_reservation:
        raise ValueError("p3og-selection-authority-history-reservation-drift")
    fields = (
        PLAN_VERSION,
        source.source_digest,
        autonomous_source.source_digest,
        formation_history_plan.plan_digest,
        selection_source.source_digest,
        selection_source.source_closure.closure_digest,
        available.capability_digest,
        reserved.reservation.reservation_id,
        reserved.receipt_digest,
        reserved.capability_digest,
        P3OG_SELECTION_AUTHORITY_HISTORY_BOUNDARY,
    )
    return P3OGSelectionAuthorityHistoryPlan(
        *fields,
        digest("selection-authority-history-plan", *fields),
    )


def p3og_selection_authority_history_plan(
    directory: Path,
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_history_plan: P3OGFormationHistoryPlan,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    reserved: P3OGSelectionLocalAuthorityReceipt,
) -> P3OGSelectionAuthorityHistoryPlan:
    """Create the binding plan only while the exact local store is still RESERVED."""
    plan = _plan_core(
        source,
        autonomous_source,
        formation_history_plan,
        selection_source,
        available,
        reserved,
    )
    current = read_p3og_selection_local_authority(directory)
    if current.state is not P3OGSelectionLocalAuthorityState.RESERVED:
        raise ValueError("p3og-selection-authority-history-store-not-reserved")
    if current != reserved:
        raise ValueError("p3og-selection-authority-history-store-reservation-drift")
    return plan


def validate_p3og_selection_authority_history_plan(
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_history_plan: P3OGFormationHistoryPlan,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    reserved: P3OGSelectionLocalAuthorityReceipt,
    plan: P3OGSelectionAuthorityHistoryPlan,
) -> P3OGSelectionAuthorityHistoryPlan:
    """Replay the immutable plan; this does not authenticate when it was created."""
    if type(plan) is not P3OGSelectionAuthorityHistoryPlan:
        raise ValueError("p3og-selection-authority-history-plan-type")
    try:
        expected = _plan_core(
            source,
            autonomous_source,
            formation_history_plan,
            selection_source,
            available,
            reserved,
        )
        equal = compare_digest(canonical_bytes(plan), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-selection-authority-history-plan-malformed") from exc
    if not equal:
        raise ValueError("p3og-selection-authority-history-plan-drift")
    return replace(expected)


def consume_p3og_selection_for_authority_history_plan(
    directory: Path,
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_history_plan: P3OGFormationHistoryPlan,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    reserved: P3OGSelectionLocalAuthorityReceipt,
    plan: P3OGSelectionAuthorityHistoryPlan,
    capability_secret: bytes,
) -> tuple[
    PrimitiveModeSeed,
    P3OGSelectionCapability,
    P3OGOneShotSelectionReceipt,
    P3OGSelectionLocalAuthorityEvidence,
]:
    """Burn exactly the authority reserved for this exact preselection plan."""
    plan = validate_p3og_selection_authority_history_plan(
        source,
        autonomous_source,
        formation_history_plan,
        selection_source,
        available,
        reserved,
        plan,
    )
    return consume_p3og_selection_capability_locally(
        directory,
        source,
        selection_source,
        available,
        plan.authority_reservation_id,
        capability_secret,
        plan.plan_digest,
    )


def _history_cut_events(
    history: P3OGFormationHistoryEvidence,
    formation_source: P3OGNativeFormationSource,
) -> tuple[str, str, str, str]:
    table = {event.event_id: event for event in history.events}
    required = {
        "selection-source-closure": formation_source.selection_source.source_closure.closure_digest,
        "selection-capability-available": formation_source.selection_before.capability_digest,
        "selection-consume": formation_source.selection.receipt_digest,
        "selection-capability-consumed": formation_source.selection_after.capability_digest,
    }
    if any(name not in table or table[name].payload_digest != payload for name, payload in required.items()):
        raise ValueError("p3og-selection-authority-history-cut-drift")
    if not set(required).issubset(history.strict_past_event_ids):
        raise ValueError("p3og-selection-authority-history-cut-not-strict-past")
    return tuple(table[name].event_digest for name in required)  # type: ignore[return-value]


def _build_binding(
    directory: Path,
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_history_plan: P3OGFormationHistoryPlan,
    authority_history_plan: P3OGSelectionAuthorityHistoryPlan,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    criterion_payload_digest: str | None,
    later_result_payload_digest: str | None,
    history: P3OGFormationHistoryEvidence,
    authority: P3OGSelectionLocalAuthorityEvidence,
) -> P3OGSelectionAuthorityHistoryBinding:
    if type(authority) is not P3OGSelectionLocalAuthorityEvidence:
        raise ValueError("p3og-selection-authority-history-authority-type")
    history = validate_p3og_formation_history_evidence(
        source,
        autonomous_source,
        formation_history_plan,
        formation_source,
        formation_evidence,
        criterion_payload_digest,
        later_result_payload_digest,
        history,
    )
    authority_history_plan = validate_p3og_selection_authority_history_plan(
        source,
        autonomous_source,
        formation_history_plan,
        formation_source.selection_source,
        formation_source.selection_before,
        authority.reserved,
        authority_history_plan,
    )
    authority = validate_p3og_selection_local_authority(
        directory,
        source,
        formation_source.selection_source,
        formation_source.selection_before,
        formation_source.selection_after,
        formation_source.selection,
        authority,
    )
    expected_attempt = p3og_selection_local_authority_attempt_digest(
        authority.reserved.receipt_digest,
        authority_history_plan.plan_digest,
    )
    if not compare_digest(authority.claimed.attempt_digest, expected_attempt):
        raise ValueError("p3og-selection-authority-history-attempt-drift")
    closure_event, available_event, consume_event, consumed_event = _history_cut_events(
        history,
        formation_source,
    )
    # The event digests above are independently reconstructed.  The binding records
    # the consume event explicitly; adjacent cut identities remain committed via the
    # freshly replayed history ancestry and the source/capability fields below.
    _ = (closure_event, available_event, consumed_event)
    fields = (
        BINDING_VERSION,
        authority_history_plan.plan_digest,
        formation_history_plan.plan_digest,
        history.evidence_digest,
        history.ancestry_digest,
        history.formation_terminal_event_id,
        formation_source.source_digest,
        formation_source.selection_source.source_digest,
        formation_source.selection_source.source_closure.closure_digest,
        formation_source.selection_before.capability_digest,
        consume_event,
        formation_source.selection.receipt_digest,
        formation_source.selection_after.capability_digest,
        authority.reserved.receipt_digest,
        authority.claimed.receipt_digest,
        authority.claimed.attempt_digest,
        authority.terminal.receipt_digest,
        authority.evidence_digest,
        P3OG_SELECTION_AUTHORITY_HISTORY_BOUNDARY,
        0,
        P3OG_SELECTION_AUTHORITY_HISTORY_NONCLAIMS,
    )
    return P3OGSelectionAuthorityHistoryBinding(
        *fields,
        digest("selection-authority-history-binding", *fields),
    )


def build_p3og_selection_authority_history_binding(
    directory: Path,
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_history_plan: P3OGFormationHistoryPlan,
    authority_history_plan: P3OGSelectionAuthorityHistoryPlan,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    criterion_payload_digest: str | None,
    later_result_payload_digest: str | None,
    history: P3OGFormationHistoryEvidence,
    authority: P3OGSelectionLocalAuthorityEvidence,
) -> P3OGSelectionAuthorityHistoryBinding:
    """Build one store-backed identity binding without promoting the history."""
    return _build_binding(
        directory,
        source,
        autonomous_source,
        formation_history_plan,
        authority_history_plan,
        formation_source,
        formation_evidence,
        criterion_payload_digest,
        later_result_payload_digest,
        history,
        authority,
    )


def validate_p3og_selection_authority_history_binding(
    directory: Path,
    source: P3OGSource,
    autonomous_source: P3OGAutonomousTickSource,
    formation_history_plan: P3OGFormationHistoryPlan,
    authority_history_plan: P3OGSelectionAuthorityHistoryPlan,
    formation_source: P3OGNativeFormationSource,
    formation_evidence: P3OGNativeFormationEvidence,
    criterion_payload_digest: str | None,
    later_result_payload_digest: str | None,
    history: P3OGFormationHistoryEvidence,
    authority: P3OGSelectionLocalAuthorityEvidence,
    binding: P3OGSelectionAuthorityHistoryBinding,
) -> P3OGSelectionAuthorityHistoryBinding:
    """Freshly replay both lanes and require the same protected store terminal."""
    if type(binding) is not P3OGSelectionAuthorityHistoryBinding:
        raise ValueError("p3og-selection-authority-history-binding-type")
    try:
        expected = _build_binding(
            directory,
            source,
            autonomous_source,
            formation_history_plan,
            authority_history_plan,
            formation_source,
            formation_evidence,
            criterion_payload_digest,
            later_result_payload_digest,
            history,
            authority,
        )
        equal = compare_digest(canonical_bytes(binding), canonical_bytes(expected))
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-selection-authority-history-binding-malformed") from exc
    if not equal:
        raise ValueError("p3og-selection-authority-history-binding-drift")
    return replace(expected)


__all__ = (
    "P3OG_SELECTION_AUTHORITY_HISTORY_BOUNDARY",
    "P3OG_SELECTION_AUTHORITY_HISTORY_NONCLAIMS",
    "P3OGSelectionAuthorityHistoryBinding",
    "P3OGSelectionAuthorityHistoryPlan",
    "build_p3og_selection_authority_history_binding",
    "consume_p3og_selection_for_authority_history_plan",
    "p3og_selection_authority_history_plan",
    "validate_p3og_selection_authority_history_binding",
    "validate_p3og_selection_authority_history_plan",
)

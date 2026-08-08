"""Fail-closed validation for child-to-parent R14 budget snapshots."""
from __future__ import annotations

import logging

from .observer_synthesis_v2_budget import (
    MAX_LEDGER_INTEGER,
    NANOSECONDS_PER_SECOND,
    BudgetCutoffReason,
    BudgetLedgerSnapshot,
    BudgetValidationError,
    validate_budget_limits,
)

logger = logging.getLogger(__name__)


def verify_budget_ledger_snapshot(snapshot: object) -> bool:
    """Reject forged, negative, over-limit, or inconsistent exact snapshots."""
    logger.debug(
        "verify_budget_ledger_snapshot entry type=%s",
        type(snapshot).__name__,
    )
    if type(snapshot) is not BudgetLedgerSnapshot:
        logger.error("R14 budget snapshot rejected type=%s", type(snapshot).__name__)
        return False
    try:
        limits = validate_budget_limits(snapshot.limits)
    except BudgetValidationError:
        logger.error("R14 budget snapshot rejected limits")
        return False
    counters = (
        (snapshot.candidates, limits.candidate_limit),
        (snapshot.canonical_bytes, limits.canonical_bytes_limit),
        (snapshot.evaluations, limits.evaluation_limit),
        (
            snapshot.transcript_output_bytes,
            limits.transcript_output_bytes_limit,
        ),
    )
    if any(
        type(value) is not int or value < 0 or value > limit
        for value, limit in counters
    ):
        logger.error("R14 budget snapshot rejected counters")
        return False
    if (
        type(snapshot.elapsed_ns) is not int
        or snapshot.elapsed_ns < 0
        or snapshot.elapsed_ns > MAX_LEDGER_INTEGER
        or (snapshot.candidates == 0) != (snapshot.canonical_bytes == 0)
        or snapshot.canonical_bytes < snapshot.candidates
    ):
        logger.error("R14 budget snapshot rejected accounting")
        return False
    reason = snapshot.cutoff_reason
    if reason is not None and type(reason) is not BudgetCutoffReason:
        logger.error("R14 budget snapshot rejected cutoff type")
        return False
    if (
        reason is BudgetCutoffReason.CANDIDATES
        and snapshot.candidates != limits.candidate_limit
    ):
        logger.error("R14 budget snapshot rejected candidate cutoff state")
        return False
    wall_ns = limits.wall_seconds * NANOSECONDS_PER_SECOND
    result = (
        snapshot.elapsed_ns >= wall_ns
        if reason is BudgetCutoffReason.WALL_TIME
        else snapshot.elapsed_ns < wall_ns
    )
    logger.debug("verify_budget_ledger_snapshot exit result=%s", result)
    return result

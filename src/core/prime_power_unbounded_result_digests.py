"""Exact domain-separated digests for P3-N6 nonpositive results."""

from __future__ import annotations

import logging

from .prime_power_unbounded_common import digest
from .prime_power_unbounded_types import (
    N6FailedBound, N6FormalFailureKind, N6GoalID, N6Lane,
)

logger = logging.getLogger(__name__)


def counterexample_evidence_digest(
    goal: N6GoalID,
    subject_digest: str,
    input_digest: str,
    expected_digest: str,
    actual_digest: str,
    proof_id: N6GoalID,
    source_digest: str,
    ledger_digest: str,
) -> str:
    """Bind one mismatch proposition to subject, bytes and exact provenance."""
    logger.debug("counterexample_evidence_digest entry")
    result = digest("veyra.p3n6.counterexample.v1", (
        ("goal", goal.value.encode()), ("subject", subject_digest.encode()),
        ("input", input_digest.encode()),
        ("expected", expected_digest.encode()), ("actual", actual_digest.encode()),
        ("proof", proof_id.value.encode()), ("source", source_digest.encode()),
        ("ledger", ledger_digest.encode()),
    ))
    logger.debug("counterexample_evidence_digest exit")
    return result


def open_result_digest(
    lane: N6Lane, reason: str, goal: N6GoalID, request_digest: str
) -> str:
    """Bind an OPEN result to its lane, sole reason, goal and request."""
    logger.debug("open_result_digest entry")
    result = digest("veyra.p3n6.open.v1", (
        ("lane", lane.value.encode()), ("reason", reason.encode()),
        ("goal", goal.value.encode()), ("request", request_digest.encode()),
    ))
    logger.debug("open_result_digest exit")
    return result


def refutation_digest(
    lane: N6Lane, reason: str, evidence_digest: str, request_digest: str
) -> str:
    """Bind a refutation to lane, exact proposition evidence and request."""
    logger.debug("refutation_digest entry")
    result = digest("veyra.p3n6.refutation.v1", (
        ("lane", lane.value.encode()), ("reason", reason.encode()),
        ("evidence", evidence_digest.encode()),
        ("request", request_digest.encode()),
    ))
    logger.debug("refutation_digest exit")
    return result


def resource_refusal_digest(
    lane: N6Lane,
    bound: N6FailedBound,
    required: int,
    allowed: int,
    request_digest: str,
) -> str:
    """Bind a resource refusal to exact lane, exceeded bound and request."""
    logger.debug("resource_refusal_digest entry")
    result = digest("veyra.p3n6.resource-refusal.v1", (
        ("lane", lane.value.encode()), ("bound", bound.value.encode()),
        ("required", required.to_bytes(8, "big")),
        ("allowed", allowed.to_bytes(8, "big")),
        ("request", request_digest.encode()),
    ))
    logger.debug("resource_refusal_digest exit")
    return result


def formal_attempt_digest(
    lane: N6Lane,
    kind: N6FormalFailureKind,
    request_digest: str,
    source_digest: str,
    toolchain_id: str,
    policy_digest: str,
    output_digest: str,
    diagnostic_code: str,
    diagnostic_detail_digest: str,
) -> str:
    """Bind an operational attempt to every exact execution identity."""
    logger.debug("formal_attempt_digest entry")
    result = digest("veyra.p3n6.formal-attempt.v1", (
        ("lane", lane.value.encode()), ("kind", kind.value.encode()),
        ("request", request_digest.encode()), ("source", source_digest.encode()),
        ("toolchain", toolchain_id.encode()), ("policy", policy_digest.encode()),
        ("output", output_digest.encode()), ("code", diagnostic_code.encode()),
        ("detail", diagnostic_detail_digest.encode()),
    ))
    logger.debug("formal_attempt_digest exit")
    return result

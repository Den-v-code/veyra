"""Canonical deterministic transcript codec for R14.3b CEGIS."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_synthesis_v2_budget import BudgetLimits, BudgetLedgerSnapshot
from .observer_synthesis_v2_cegis_types import CegisEventV2, CegisTraceStepV2
from .proof_core_codec import canonical_json, digest_data

logger = logging.getLogger(__name__)

TRACE_SCHEMA = "veyra.observer-synthesis-v2.cegis-trace.r14.3b.v1"
LIMITS_SCHEMA = "veyra.observer-synthesis-v2.cegis-limits.r14.3b.v1"
TRAINING_SCHEMA = "veyra.observer-synthesis-v2.cegis-training.r14.3b.v1"


def limits_digest_v2(limits: BudgetLimits) -> str:
    """Bind only deterministic exact ceilings, never runtime clock state."""
    logger.debug("limits_digest_v2 entry")
    result = digest_data(
        {
            "candidate_limit": limits.candidate_limit,
            "canonical_bytes_limit": limits.canonical_bytes_limit,
            "evaluation_limit": limits.evaluation_limit,
            "process_as_bytes_limit": limits.process_as_bytes_limit,
            "schema": LIMITS_SCHEMA,
            "transcript_output_bytes_limit": limits.transcript_output_bytes_limit,
            "wall_seconds": limits.wall_seconds,
        },
        f"{LIMITS_SCHEMA}.binding",
    )
    logger.debug("limits_digest_v2 exit digest=%s", result[:12])
    return result


def training_digest_v2(case_digests: tuple[str, ...]) -> str:
    """Bind the exact ordered TRAIN obligations without reading other splits."""
    logger.debug("training_digest_v2 entry cases=%d", len(case_digests))
    result = digest_data(
        {"case_digests": list(case_digests), "schema": TRAINING_SCHEMA},
        f"{TRAINING_SCHEMA}.binding",
    )
    logger.debug("training_digest_v2 exit digest=%s", result[:12])
    return result


def trace_step_bytes_v2(
    sequence: int,
    event: CegisEventV2,
    candidate_ordinal: int,
    candidate_digest: str,
    counterexample_case_id: int | None,
    counterexample_case_digest: str | None,
    snapshot: BudgetLedgerSnapshot,
    limits_digest: str,
) -> bytes:
    """Encode one row without elapsed time, output counters, or cache state."""
    logger.debug(
        "trace_step_bytes_v2 entry sequence=%d event=%s",
        sequence,
        event.value,
    )
    result = canonical_json(
        {
            "candidate_digest": candidate_digest,
            "candidate_ordinal": candidate_ordinal,
            "charged_candidates": snapshot.candidates,
            "charged_canonical_bytes": snapshot.canonical_bytes,
            "charged_evaluations": snapshot.evaluations,
            "counterexample_case_digest": counterexample_case_digest,
            "counterexample_case_id": counterexample_case_id,
            "event": event.value,
            "limits_digest": limits_digest,
            "schema": TRACE_SCHEMA,
            "sequence": sequence,
        }
    ).encode("utf-8")
    logger.debug("trace_step_bytes_v2 exit bytes=%d", len(result))
    return result


def build_trace_step_v2(
    sequence: int,
    event: CegisEventV2,
    candidate_ordinal: int,
    candidate_digest: str,
    counterexample_case_id: int | None,
    counterexample_case_digest: str | None,
    snapshot: BudgetLedgerSnapshot,
    limits_digest: str,
    canonical: bytes,
) -> CegisTraceStepV2:
    """Construct a frozen row after its canonical bytes have been precharged."""
    logger.debug("build_trace_step_v2 entry sequence=%d", sequence)
    result = CegisTraceStepV2(
        sequence,
        event,
        candidate_ordinal,
        candidate_digest,
        counterexample_case_id,
        counterexample_case_digest,
        snapshot.candidates,
        snapshot.canonical_bytes,
        snapshot.evaluations,
        limits_digest,
        canonical,
        sha256(TRACE_SCHEMA.encode("ascii") + b"\0step\0" + canonical).hexdigest(),
    )
    logger.debug("build_trace_step_v2 exit digest=%s", result.step_digest[:12])
    return result


def trace_digest_v2(trace: tuple[CegisTraceStepV2, ...]) -> str:
    """Hash framed canonical rows; runtime timing and cache nonces are absent."""
    logger.debug("trace_digest_v2 entry steps=%d", len(trace))
    digest = sha256(TRACE_SCHEMA.encode("ascii") + b"\0transcript\0")
    for step in trace:
        digest.update(len(step.canonical).to_bytes(8, "big"))
        digest.update(step.canonical)
    result = digest.hexdigest()
    logger.debug("trace_digest_v2 exit digest=%s", result[:12])
    return result

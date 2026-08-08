"""Fixed stdlib-first child entry for the isolated R14.2b worker."""
from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.observer_synthesis_v2_cegis_types import ObserverCegisReportV2

logger = logging.getLogger(__name__)


def _read_exact(fd: int, size: int) -> bytes:
    logger.debug("_read_exact entry fd=%d size=%d", fd, size)
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = os.read(fd, remaining)
        if not chunk:
            raise ValueError("partial-worker-input")
        chunks.append(chunk)
        remaining -= len(chunk)
    result = b"".join(chunks)
    logger.debug("_read_exact exit bytes=%d", len(result))
    return result


def _write_all(fd: int, payload: bytes) -> None:
    logger.debug("_write_all entry fd=%d bytes=%d", fd, len(payload))
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("worker-result-write-failed")
        view = view[written:]
    logger.debug("_write_all exit")


def _report_data(report: "ObserverCegisReportV2") -> dict[str, object]:
    logger.debug("_report_data entry")
    winner = report.winner
    ledger = report.ledger
    if ledger is None:
        raise ValueError("missing-worker-ledger")
    result = {
        "active_case_ids": list(report.active_case_ids),
        "catalog_digest": report.catalog_digest,
        "detail": report.detail,
        "ledger": {
            "candidates": ledger.candidates,
            "canonical_bytes": ledger.canonical_bytes,
            "cutoff_reason": (
                None if ledger.cutoff_reason is None else ledger.cutoff_reason.value
            ),
            "evaluations": ledger.evaluations,
            "transcript_output_bytes": ledger.transcript_output_bytes,
        },
        "limits_digest": report.limits_digest,
        "status": report.status.value,
        "trace": [step.canonical.decode() for step in report.trace],
        "trace_digest": report.trace_digest,
        "training_digest": report.training_digest,
        "traversed_candidates": report.traversed_candidates,
        "winner": (
            None
            if winner is None
            else {
                "canonical": winner.canonical.decode(),
                "cost": winner.cost,
                "depth": winner.depth,
                "digest": winner.digest,
                "ordinal": winner.ordinal,
            }
        ),
    }
    logger.debug("_report_data exit")
    return result


def _run(control_fd: int, result_fd: int) -> int:
    logger.debug("_run entry")
    if _read_exact(control_fd, 1) != b"G":
        raise ValueError("worker-go-missing")
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    from src.core.observer_synthesis_v2_budget import (
        BudgetLedger,
        BudgetLimitExceeded,
    )
    from src.core.observer_synthesis_v2_cegis import fit_observer_cegis_v2
    from src.core.observer_synthesis_v2_corpus import DEFAULT_CASES
    from src.core.observer_synthesis_v2_grammar import enumerate_observer_grammar_v2
    from src.core.observer_synthesis_v2_types import SynthesisStatus
    from src.core.observer_synthesis_v2_worker_codec import (
        FRAME_BYTES,
        MAX_WORKER_FRAME_BYTES,
        frame_bytes_v2,
        request_from_bytes_v2,
        result_payload_v2,
    )
    from src.core.observer_synthesis_v2_worker_validation import (
        validate_worker_request_v2,
    )

    size = int.from_bytes(_read_exact(0, FRAME_BYTES), "big")
    if size <= 0 or size > MAX_WORKER_FRAME_BYTES:
        raise ValueError("invalid-worker-request-size")
    raw = _read_exact(0, size)
    try:
        request = validate_worker_request_v2(request_from_bytes_v2(raw))
    except (TypeError, UnicodeError, ValueError):
        payload = result_payload_v2(
            SynthesisStatus.INVALID,
            "invalid-worker-request",
            None,
        )
    else:
        ledger = BudgetLedger(request.limits)
        try:
            catalog = enumerate_observer_grammar_v2(ledger=ledger)
        except BudgetLimitExceeded as exc:
            payload = result_payload_v2(
                SynthesisStatus.INCOMPLETE,
                exc.reason.value,
                None,
            )
        else:
            report = fit_observer_cegis_v2(
                catalog,
                DEFAULT_CASES[:2],
                request.limits,
                precharged_ledger=ledger,
            )
            complete = report.status in {
                SynthesisStatus.FOUND,
                SynthesisStatus.EXHAUSTED,
            }
            payload = result_payload_v2(
                report.status,
                report.detail,
                _report_data(report) if complete else None,
            )
    _write_all(result_fd, frame_bytes_v2(payload))
    logger.debug("_run exit")
    return 0


def main() -> int:
    logger.debug("main entry argc=%d", len(sys.argv))
    if len(sys.argv) != 3:
        logger.error("main invalid argv")
        return 64
    try:
        control_fd = int(sys.argv[1])
        result_fd = int(sys.argv[2])
        result = _run(control_fd, result_fd)
    except (OSError, TypeError, ValueError):
        logger.error("main controlled failure", exc_info=True)
        return 65
    logger.debug("main exit=%d", result)
    return result


if __name__ == "__main__":
    raise SystemExit(main())

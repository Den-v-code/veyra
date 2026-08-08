"""Stdlib-first fixed entry for one isolated R14.5 receipt child."""
from __future__ import annotations

import logging
import os
import sys

logger = logging.getLogger(__name__)


def _read_exact(fd: int, size: int) -> bytes:
    logger.debug("_read_exact entry fd=%d size=%d", fd, size)
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = os.read(fd, remaining)
        if not chunk:
            raise ValueError("partial-receipt-input")
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
            raise OSError("receipt-result-write-failed")
        view = view[written:]
    logger.debug("_write_all exit")


def _run(control_fd: int, result_fd: int) -> int:
    logger.debug("_run entry")
    if _read_exact(control_fd, 1) != b"G":
        raise ValueError("receipt-go-missing")
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    from src.core.observer_synthesis_v2_budget import BudgetLimitExceeded
    from src.core.observer_synthesis_v2_receipt_worker_execution import (
        build_precharged_receipt_bytes_v2,
    )
    from src.core.observer_synthesis_v2_receipt_worker_codec import (
        receipt_request_digest_v2,
        receipt_request_from_bytes_v2,
        receipt_result_payload_v2,
    )
    from src.core.observer_synthesis_v2_receipt_worker_validation import (
        validate_receipt_request_v2,
    )
    from src.core.observer_synthesis_v2_types import SynthesisStatus
    from src.core.observer_synthesis_v2_worker_codec import (
        FRAME_BYTES,
        MAX_WORKER_FRAME_BYTES,
        frame_bytes_v2,
    )

    size = int.from_bytes(_read_exact(0, FRAME_BYTES), "big")
    if size <= 0 or size > MAX_WORKER_FRAME_BYTES:
        raise ValueError("invalid-receipt-request-size")
    raw = _read_exact(0, size)
    try:
        validated = validate_receipt_request_v2(receipt_request_from_bytes_v2(raw))
    except (RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("invalid-receipt-request") from exc
    request = validated.request
    request_digest = receipt_request_digest_v2(request)
    try:
        bundle_bytes = build_precharged_receipt_bytes_v2(
            validated.trial,
            request.limits,
        )
    except BudgetLimitExceeded as exc:
        status = SynthesisStatus.INCOMPLETE
        detail = exc.reason.value
        bundle_bytes = None
    except MemoryError:
        status = SynthesisStatus.INCOMPLETE
        detail = "process-address-space-limit"
        bundle_bytes = None
    except (AttributeError, RuntimeError, TypeError, UnicodeError, ValueError):
        logger.error("_run receipt replay invalid", exc_info=True)
        status = SynthesisStatus.INVALID
        detail = "invalid-receipt"
        bundle_bytes = None
    else:
        status = SynthesisStatus.FOUND
        detail = "receipt-complete"
    payload = receipt_result_payload_v2(
        status,
        detail,
        request_digest,
        request.limits_digest,
        bundle_bytes,
    )
    _write_all(result_fd, frame_bytes_v2(payload))
    logger.debug("_run exit status=%s", status.value)
    return 0


def main() -> int:
    logger.debug("main entry argc=%d", len(sys.argv))
    if len(sys.argv) != 3:
        logger.error("main invalid argv")
        return 64
    try:
        result = _run(int(sys.argv[1]), int(sys.argv[2]))
    except (OSError, RecursionError, TypeError, UnicodeError, ValueError):
        logger.error("main controlled failure", exc_info=True)
        return 65
    logger.debug("main exit=%d", result)
    return result


if __name__ == "__main__":
    raise SystemExit(main())

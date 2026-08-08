"""Parent adapter for the fixed isolated R14.2b CEGIS worker."""
from __future__ import annotations

from hashlib import sha256
import logging
import os
import subprocess
import time

from .observer_synthesis_v2_types import SynthesisStatus
from .observer_synthesis_v2_worker_codec import (
    FRAME_BYTES,
    MAX_WORKER_FRAME_BYTES,
    frame_bytes_v2,
    request_bytes_v2,
)
from .observer_synthesis_v2_worker_runtime import (
    FixedWorkerKindV2,
    apply_verified_limits_v2,
    run_fixed_child_v2,
    unframe_exact_result_v2,
)
from .observer_synthesis_v2_worker_types import (
    WORKER_RESULT_SCHEMA,
    ObserverWorkerResultV2,
)
from .observer_synthesis_v2_worker_validation import (
    parse_result_payload_v2,
    validate_worker_request_v2,
)
from .proof_core_codec import canonical_json

logger = logging.getLogger(__name__)

_apply_limits = apply_verified_limits_v2


def _terminal(
    status: SynthesisStatus,
    detail: str,
    report: bytes | None = None,
) -> ObserverWorkerResultV2:
    logger.debug("_terminal entry status=%s detail=%s", status.value, detail)
    digest = None if report is None else sha256(
        WORKER_RESULT_SCHEMA.encode() + b"\0report\0" + report
    ).hexdigest()
    result = ObserverWorkerResultV2(
        WORKER_RESULT_SCHEMA,
        status,
        detail,
        report,
        digest,
    )
    logger.debug("_terminal exit")
    return result


def _unframe_result(raw: bytes) -> bytes:
    logger.debug("_unframe_result entry bytes=%d", len(raw))
    result = unframe_exact_result_v2(raw, FRAME_BYTES, MAX_WORKER_FRAME_BYTES)
    logger.debug("_unframe_result exit bytes=%d", len(result))
    return result


def run_observer_cegis_worker_v2(
    request: object,
) -> ObserverWorkerResultV2:
    """Run the exact worker only after verified race-free process limits."""
    logger.debug("run_observer_cegis_worker_v2 entry")
    try:
        valid = validate_worker_request_v2(request)
        request_frame = frame_bytes_v2(request_bytes_v2(valid))
    except (TypeError, UnicodeError, ValueError):
        return _terminal(SynthesisStatus.INVALID, "invalid-worker-request")
    outcome = run_fixed_child_v2(
        FixedWorkerKindV2.CEGIS,
        request_frame,
        valid.limits,
        popen=subprocess.Popen,
        pipe=os.pipe,
        write=os.write,
        clock=time.monotonic_ns,
        apply_limits=_apply_limits,
    )
    state_details = {
        "limit-bootstrap": "worker-limit-bootstrap",
        "pipe-bootstrap": "worker-pipe-bootstrap",
        "wall": "worker-wall",
        "output": "worker-output",
        "child": "worker-child",
        "runtime": "worker-runtime",
        "cancelled": "worker-cancelled",
    }
    if outcome.state == "invalid":
        return _terminal(SynthesisStatus.INVALID, "invalid-worker-result")
    if outcome.state != "ok":
        return _terminal(SynthesisStatus.INCOMPLETE, state_details[outcome.state])
    try:
        payload = _unframe_result(outcome.framed_result)
        status, detail, report = parse_result_payload_v2(payload, valid)
        if status in {SynthesisStatus.FOUND, SynthesisStatus.EXHAUSTED}:
            return _terminal(status, detail, canonical_json(report).encode())
        return _terminal(status, detail)
    except (EOFError, OSError, subprocess.SubprocessError):
        return _terminal(SynthesisStatus.INCOMPLETE, "worker-runtime")
    except (TypeError, UnicodeError, ValueError):
        return _terminal(SynthesisStatus.INVALID, "invalid-worker-result")

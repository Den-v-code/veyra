"""Deadline-aware GO and stdin transport for fixed R14 children."""
from __future__ import annotations

import logging
import os
import selectors
import subprocess
from typing import Callable

logger = logging.getLogger(__name__)

WRITE_CHUNK_MAX = 64 * 1024


def send_go_and_request_v2(
    proc: subprocess.Popen[bytes],
    control_fd: int,
    request_frame: bytes,
    deadline_ns: int,
    clock: Callable[[], int],
    go_write: Callable[[int, bytes], int],
) -> str:
    """Release a limited child, then stream its request without blocking."""
    logger.debug(
        "send_go_and_request_v2 entry pid=%d bytes=%d",
        proc.pid,
        len(request_frame),
    )
    if proc.stdin is None:
        logger.error("send_go_and_request_v2 missing stdin")
        return "runtime"
    if clock() >= deadline_ns:
        return "wall"
    if go_write(control_fd, b"G") != 1:
        logger.error("send_go_and_request_v2 partial GO")
        return "runtime"
    stdin_fd = proc.stdin.fileno()
    os.set_blocking(stdin_fd, False)
    selector = selectors.DefaultSelector()
    selector.register(stdin_fd, selectors.EVENT_WRITE)
    offset = 0
    try:
        while offset < len(request_frame):
            remaining_ns = deadline_ns - clock()
            if remaining_ns <= 0:
                logger.warning("send_go_and_request_v2 cutoff=wall")
                return "wall"
            events = selector.select(remaining_ns / 1_000_000_000)
            if not events:
                logger.warning("send_go_and_request_v2 cutoff=wall")
                return "wall"
            try:
                written = os.write(
                    stdin_fd,
                    request_frame[offset : offset + WRITE_CHUNK_MAX],
                )
            except BlockingIOError:
                continue
            if written <= 0:
                logger.error("send_go_and_request_v2 request write failed")
                return "runtime"
            offset += written
    finally:
        selector.close()
    proc.stdin.close()
    logger.debug("send_go_and_request_v2 exit bytes=%d", offset)
    return "ok"

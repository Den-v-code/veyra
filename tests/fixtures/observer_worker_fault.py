"""Stdlib-only fault child used to verify the R14.2b parent supervisor."""
from __future__ import annotations

import logging
import os
import resource
import signal
import sys
import time

logger = logging.getLogger(__name__)
EXPECTED_AS = 512 * 1024 * 1024


def _read_go(fd: int) -> None:
    logger.debug("_read_go entry fd=%d", fd)
    if os.read(fd, 1) != b"G":
        raise RuntimeError("missing-go")
    logger.debug("_read_go exit")


def _write_all(fd: int, payload: bytes) -> None:
    logger.debug("_write_all entry bytes=%d", len(payload))
    view = memoryview(payload)
    while view:
        view = view[os.write(fd, view):]
    logger.debug("_write_all exit")


def main() -> int:
    logger.debug("fault child main entry")
    control_fd = int(sys.argv[1])
    result_fd = int(sys.argv[2])
    mode = os.environ["VEYRA_WORKER_FAULT_MODE"]
    _read_go(control_fd)
    if mode == "as-check":
        exact = (
            resource.getrlimit(resource.RLIMIT_AS) == (EXPECTED_AS, EXPECTED_AS)
            and resource.getrlimit(resource.RLIMIT_CORE) == (0, 0)
        )
        if exact:
            os.kill(os.getpid(), signal.SIGKILL)
        logger.error("fault child AS limits mismatch")
        return 70
    if mode == "allocation":
        logger.debug("fault child allocation pressure entry")
        try:
            bytearray(EXPECTED_AS + 64 * 1024 * 1024)
        except MemoryError:
            logger.info("fault child allocation pressure blocked")
            return 73
        logger.error("fault child allocation unexpectedly succeeded")
        return 71
    if mode == "signal":
        os.kill(os.getpid(), signal.SIGKILL)
    if mode == "hang-group":
        child = os.fork()
        if child == 0:
            time.sleep(30)
            os._exit(0)
        time.sleep(30)
    if mode in {"success-fork", "ignore-term-group"}:
        child = os.fork()
        if child == 0:
            for fd in range(256):
                try:
                    os.close(fd)
                except OSError:
                    pass
            if mode == "ignore-term-group":
                signal.signal(signal.SIGTERM, signal.SIG_IGN)
            time.sleep(30)
            os._exit(0)
        if mode == "ignore-term-group":
            time.sleep(30)
        _write_all(result_fd, (2).to_bytes(8, "big") + b"{}")
        return 0
    if mode == "partial":
        _write_all(result_fd, b"\0" * 7)
        return 0
    if mode == "multiple":
        frame = (2).to_bytes(8, "big") + b"{}"
        _write_all(result_fd, frame + frame)
        return 0
    logger.error("fault child invalid mode=%s", mode)
    return 72


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run Veyra Sage doctest examples with visible progress."""

from __future__ import annotations

import doctest
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import veyra_sage.examples as examples

logger = logging.getLogger("veyra.sage_doctest")


def stage(index: int, total: int, message: str) -> None:
    """Print visible progress stage."""
    logger.debug("stage entry index=%d total=%d message=%s", index, total, message)
    print(f"[{index}/{total}] {message}")
    logger.debug("stage exit")


def main() -> int:
    """Run doctests for Sage examples."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    logger.debug("main entry")
    stage(1, 2, "Loading veyra_sage.examples")
    stage(2, 2, "Running doctests")
    result = doctest.testmod(examples, verbose=False)
    print(f"[done] attempted={result.attempted} failed={result.failed}")
    logger.debug("main exit attempted=%d failed=%d", result.attempted, result.failed)
    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

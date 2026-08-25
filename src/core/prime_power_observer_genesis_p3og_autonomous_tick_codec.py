"""Domain-separated digests for bounded P3-OG autonomous-tick pressure."""

from __future__ import annotations

from hashlib import sha256
import logging
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

logger = logging.getLogger(__name__)
AUTONOMOUS_TICK_DOMAIN = b"veyra-p3og-autonomous-tick-v1\0"
_AUTONOMOUS_EVIDENCE_LABELS = frozenset(
    {"autonomous-tick-genealogy", "autonomous-first-closure-evidence"},
)


def autonomous_tick_digest(label: str, *values: Any) -> str:
    """Digest typed values under the isolated autonomous-tick domain."""
    logger.debug(
        "p3og.autonomous_tick.digest entry label=%s values=%d",
        label,
        len(values),
    )
    try:
        label = bounded_text(label, "p3og-autonomous-tick-digest-label")
        encoder = (
            evidence_bytes
            if label in _AUTONOMOUS_EVIDENCE_LABELS
            else canonical_bytes
        )
        encoded = encoder(*values)
        result = sha256(
            AUTONOMOUS_TICK_DOMAIN + label.encode("ascii") + b"\0" + encoded,
        ).hexdigest()
    except (TypeError, UnicodeError, ValueError):
        logger.error("p3og.autonomous_tick.digest error")
        raise
    logger.debug(
        "p3og.autonomous_tick.digest exit label=%s digest=%s",
        label,
        result[:12],
    )
    return result

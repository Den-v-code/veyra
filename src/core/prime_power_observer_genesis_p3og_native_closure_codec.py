"""Domain-separated digests for bounded P3-OG native-state closure pressure."""

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
NATIVE_CLOSURE_DOMAIN = b"veyra-p3og-native-closure-v1\0"
_NATIVE_CLOSURE_EVIDENCE_LABELS = frozenset(
    {"native-closure-genealogy", "native-first-closure-evidence"},
)


def native_closure_digest(label: str, *values: Any) -> str:
    """Digest typed values under the isolated native-closure domain."""
    logger.debug(
        "p3og.native_closure.digest entry label=%s values=%d",
        label,
        len(values),
    )
    try:
        label = bounded_text(label, "p3og-native-closure-digest-label")
        encoder = (
            evidence_bytes
            if label in _NATIVE_CLOSURE_EVIDENCE_LABELS
            else canonical_bytes
        )
        encoded = encoder(*values)
        result = sha256(
            NATIVE_CLOSURE_DOMAIN + label.encode("ascii") + b"\0" + encoded,
        ).hexdigest()
    except (TypeError, UnicodeError, ValueError):
        logger.error("p3og.native_closure.digest error")
        raise
    logger.debug(
        "p3og.native_closure.digest exit label=%s digest=%s",
        label,
        result[:12],
    )
    return result

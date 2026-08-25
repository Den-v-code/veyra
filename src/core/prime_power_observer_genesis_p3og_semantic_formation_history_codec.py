"""Domain-separated digests for semantic P3-OG formation-history v3."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

DOMAIN = b"veyra-p3og-semantic-formation-history-v3\0"
_EVIDENCE = frozenset({
    "semantic-formation-history-ancestry",
    "semantic-formation-history-evidence",
})


def semantic_formation_history_digest(label: str, *values: Any) -> str:
    """Hash one v3 history value under its isolated domain."""
    label = bounded_text(label, "p3og-semantic-formation-history-digest-label")
    encoder = evidence_bytes if label in _EVIDENCE else canonical_bytes
    encoded = encoder(*values)
    return sha256(DOMAIN + label.encode("ascii") + b"\0" + encoded).hexdigest()

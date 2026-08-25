"""Domain-separated digests for the P3-OG semantic-formation bridge."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

DOMAIN = b"veyra-p3og-semantic-formation-bridge-v1\0"
_EVIDENCE = frozenset({
    "semantic-formation-bridge-genealogy",
    "semantic-formation-bridge-evidence",
})


def semantic_formation_bridge_digest(label: str, *values: Any) -> str:
    """Hash one bridge value under its isolated semantic domain."""
    label = bounded_text(label, "p3og-semantic-formation-bridge-digest-label")
    encoder = evidence_bytes if label in _EVIDENCE else canonical_bytes
    encoded = encoder(*values)
    return sha256(DOMAIN + label.encode("ascii") + b"\0" + encoded).hexdigest()

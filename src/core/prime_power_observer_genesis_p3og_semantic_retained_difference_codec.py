"""Domain-separated digests for semantic retained-difference P3-OG evidence."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

DOMAIN = b"veyra-p3og-semantic-retained-difference-v1\0"
_EVIDENCE_LABELS = frozenset({"semantic-retained-difference-evidence"})


def semantic_retained_difference_digest(label: str, *values: Any) -> str:
    """Hash one retained-difference value under its isolated domain."""
    label = bounded_text(label, "p3og-semantic-retained-difference-digest-label")
    encoder = evidence_bytes if label in _EVIDENCE_LABELS else canonical_bytes
    return sha256(DOMAIN + label.encode("ascii") + b"\0" + encoder(*values)).hexdigest()

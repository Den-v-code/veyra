"""Domain-separated digests for bounded P3-OG formation-history pressure."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

DOMAIN = b"veyra-p3og-formation-history-v1\0"
_EVIDENCE = frozenset({"formation-history-ancestry", "formation-history-evidence"})


def formation_history_digest(label: str, *values: Any) -> str:
    label = bounded_text(label, "p3og-formation-history-digest-label")
    encoder = evidence_bytes if label in _EVIDENCE else canonical_bytes
    encoded = encoder(*values)
    return sha256(DOMAIN + label.encode("ascii") + b"\0" + encoded).hexdigest()

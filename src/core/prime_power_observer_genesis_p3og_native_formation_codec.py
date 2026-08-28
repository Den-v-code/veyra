"""Domain-separated digests for P3-OG native formation pressure v2."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

NATIVE_FORMATION_DOMAIN = b"veyra-p3og-native-formation-v2\0"
_EVIDENCE_LABELS = frozenset({"native-formation-genealogy", "native-formation-evidence"})


def native_formation_digest(label: str, *values: Any) -> str:
    label = bounded_text(label, "p3og-native-formation-digest-label")
    encoder = evidence_bytes if label in _EVIDENCE_LABELS else canonical_bytes
    encoded = encoder(*values)
    return sha256(
        NATIVE_FORMATION_DOMAIN + label.encode("ascii") + b"\0" + encoded,
    ).hexdigest()

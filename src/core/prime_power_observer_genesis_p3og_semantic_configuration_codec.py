"""Domain-separated digests for the P3-OG semantic configuration quotient."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import bounded_text, canonical_bytes

DOMAIN = b"veyra-p3og-semantic-configuration-v1\0"


def semantic_configuration_digest(label: str, *values: Any) -> str:
    """Digest exact finite semantic configuration values under an isolated domain."""
    label = bounded_text(label, "p3og-semantic-configuration-digest-label")
    encoded = canonical_bytes(*values)
    return sha256(DOMAIN + label.encode("ascii") + b"\0" + encoded).hexdigest()

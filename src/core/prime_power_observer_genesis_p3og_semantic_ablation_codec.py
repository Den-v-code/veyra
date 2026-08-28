"""Domain-separated digests for P3-OG semantic maintenance ablation."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import bounded_text, canonical_bytes

DOMAIN = b"veyra-p3og-semantic-ablation-v1\0"


def semantic_ablation_digest(label: str, *values: Any) -> str:
    """Hash one semantic-ablation value under its isolated domain."""
    label = bounded_text(label, "p3og-semantic-ablation-digest-label")
    return sha256(
        DOMAIN + label.encode("ascii") + b"\0" + canonical_bytes(*values),
    ).hexdigest()

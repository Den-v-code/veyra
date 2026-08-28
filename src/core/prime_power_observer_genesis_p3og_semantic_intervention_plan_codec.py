"""Domain-separated digests for the P3-OG semantic intervention plan."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import bounded_text, canonical_bytes

DOMAIN = b"veyra-p3og-semantic-intervention-plan-v1\0"


def semantic_intervention_plan_digest(label: str, *values: Any) -> str:
    """Hash one intervention-plan value under its isolated semantic domain."""
    label = bounded_text(label, "p3og-semantic-intervention-plan-digest-label")
    return sha256(
        DOMAIN + label.encode("ascii") + b"\0" + canonical_bytes(*values)
    ).hexdigest()

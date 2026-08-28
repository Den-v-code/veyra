"""Domain-separated digest for current retained-residue phase-effect evidence."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import bounded_text, evidence_bytes

DOMAIN = b"veyra-p3og-semantic-residue-phase-effect-v1\0"


def semantic_residue_phase_effect_digest(label: str, *values: Any) -> str:
    """Hash one phase-effect evidence value under its isolated domain."""
    label = bounded_text(label, "p3og-semantic-residue-phase-effect-digest-label")
    return sha256(
        DOMAIN + label.encode("ascii") + b"\0" + evidence_bytes(*values)
    ).hexdigest()

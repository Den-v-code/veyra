"""Domain-separated digest for matched semantic ablation/removal evidence."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import bounded_text, evidence_bytes

DOMAIN = b"veyra-p3og-semantic-matched-ablation-removal-v1\0"


def semantic_matched_ablation_removal_digest(label: str, *values: Any) -> str:
    """Hash one matched-ablation value under its isolated evidence domain."""
    label = bounded_text(label, "p3og-semantic-matched-ablation-removal-label")
    return sha256(
        DOMAIN + label.encode("ascii") + b"\0" + evidence_bytes(*values)
    ).hexdigest()

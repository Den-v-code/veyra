"""Domain-separated hashing for residue-aware P3-OG semantic tick pressure."""

from __future__ import annotations

from hashlib import sha256

from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes

DOMAIN = b"veyra-p3og-residue-aware-tick-v2\0"


def residue_aware_tick_digest(label: str, *values: object) -> str:
    if type(label) is not str or not label or len(label.encode("utf-8")) > 128:
        raise ValueError("p3og-residue-aware-tick-digest-label")
    encoder = evidence_bytes if label == "residue-aware-formation-compatibility-evidence" else canonical_bytes
    return sha256(DOMAIN + label.encode("utf-8") + b"\0" + encoder(*values)).hexdigest()

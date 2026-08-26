"""Domain-separated hashing for P3-OG retained-residue causal-effect pressure."""

from __future__ import annotations

from hashlib import sha256

from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes

DOMAIN = b"veyra-p3og-residue-causal-effect-v1\0"


def residue_causal_effect_digest(label: str, *values: object) -> str:
    if type(label) is not str or not label or len(label.encode("utf-8")) > 128:
        raise ValueError("p3og-residue-causal-effect-digest-label")
    encoder = evidence_bytes if label == "residue-causal-effect-evidence" else canonical_bytes
    return sha256(DOMAIN + label.encode("utf-8") + b"\0" + encoder(*values)).hexdigest()

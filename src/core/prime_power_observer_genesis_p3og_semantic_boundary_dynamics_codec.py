"""Domain-separated hashing for P3-OG semantic boundary-dynamics pressure."""

from __future__ import annotations

from hashlib import sha256

from .prime_power_observer_genesis_p3og_codec import canonical_bytes, evidence_bytes

DOMAIN = b"veyra-p3og-semantic-boundary-dynamics-v1\0"


def semantic_boundary_dynamics_digest(label: str, *values: object) -> str:
    """Hash bounded typed values under the boundary-dynamics domain."""
    if type(label) is not str or not label or len(label.encode("utf-8")) > 128:
        raise ValueError("p3og-semantic-boundary-dynamics-digest-label")
    encoder = evidence_bytes if label == "semantic-boundary-dynamics-evidence" else canonical_bytes
    return sha256(DOMAIN + label.encode("utf-8") + b"\0" + encoder(*values)).hexdigest()

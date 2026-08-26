"""Domain-separated digests for matched post-closure P3-OG history."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .prime_power_observer_genesis_p3og_codec import (
    bounded_text,
    canonical_bytes,
    evidence_bytes,
)

DOMAIN = b"veyra-p3og-matched-post-closure-v1\0"
_EVIDENCE = frozenset({"matched-post-closure-ancestry", "matched-post-closure-evidence"})


def matched_post_closure_digest(label: str, *values: Any) -> str:
    """Hash one matched-history value under its isolated domain."""
    label = bounded_text(label, "p3og-matched-post-closure-digest-label")
    encoder = evidence_bytes if label in _EVIDENCE else canonical_bytes
    return sha256(DOMAIN + label.encode("ascii") + b"\0" + encoder(*values)).hexdigest()

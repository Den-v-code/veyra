"""Shared certificate datatypes for Veyra verification."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Certificate:
    """One executable certificate item."""

    name: str
    method: str
    passed: bool
    detail: str
    level: int

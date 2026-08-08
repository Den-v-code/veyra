"""Closed evidence DTOs for bounded P3-N4 coordinate comparison."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .padic_completion_types import PadicCompletionPackage
from .padic_family_introduction_types import N1IntroductionPackage
from .padic_local_realization_types import (
    N34Open, N34Policy, N34Refuted, N34ResourceLimit,
)


@dataclass(frozen=True)
class BoundedCoordinateRow:
    depth: int
    modulus: int
    left_residue: int
    right_residue: int
    row_digest: str


@dataclass(frozen=True)
class BoundedCoordinateEqualitySource:
    version: str
    depth: int
    pomega2_package_digest: str
    left_family_source_digest: str
    right_family_source_digest: str
    rows: tuple[BoundedCoordinateRow, ...]
    source_digest: str


@dataclass(frozen=True)
class BoundedEqualityRequest:
    left_n1: N1IntroductionPackage
    right_n1: N1IntroductionPackage
    pomega2: PadicCompletionPackage
    source: BoundedCoordinateEqualitySource
    policy: N34Policy
    request_digest: str


BoundedEqualityResult: TypeAlias = N34Open | N34Refuted | N34ResourceLimit

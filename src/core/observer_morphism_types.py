"""Immutable DTOs for the provisional P1-A observer-morphism slice."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .observer_core_types import ResponseKind


class ProjectionStep(str, Enum):
    """Structural response projection through a product observer."""

    LEFT = "left"
    RIGHT = "right"


class MorphismStatus(str, Enum):
    """Outcomes relative to one explicitly declared structural projection."""

    STRONG = "strong"
    INFORMATION_ONLY = "information-only"
    INCOMPARABLE = "incomparable"


class InformationLoss(str, Enum):
    """Conservative structural information-loss classification."""

    LOSSLESS_IDENTITY = "lossless-identity"
    DROPS_PAIR_COMPONENTS = "drops-pair-components"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class ObserverSourceBinding:
    """Immutable doctrine membership binding; never a chronology receipt."""

    binding_id: str
    doctrine_fingerprint: str
    observer_ids: tuple[str, ...]
    observer_digests: tuple[str, ...]
    membership_digest: str
    scope: str = "immutability-membership-not-chronology"


@dataclass(frozen=True)
class R11DomainProfile:
    """Exact minimum recurrence depth for one closed R11 observer domain."""

    observer_id: str
    minimum_pulse_depth: int
    nonempty_witness_depth: int
    structurally_confirmed: bool
    scope: str = "closed-r11-minimum-pulse-domain"


@dataclass(frozen=True)
class ComparisonDomain:
    """The confirmed intersection Dom(fine) intersect Dom(coarse)."""

    fine_minimum_depth: int
    coarse_minimum_depth: int
    witness_depth: int
    confirmed_nonempty: bool
    scope: str = "exact-r11-domain-intersection"


@dataclass(frozen=True)
class ResponseTranslation:
    """A doctrine-bound structural fine-to-coarse response projection."""

    translation_id: str
    doctrine_fingerprint: str
    source_binding_digest: str
    fine_observer_id: str
    coarse_observer_id: str
    projection: tuple[ProjectionStep, ...]
    fine_kind: ResponseKind
    coarse_kind: ResponseKind
    translation_digest: str
    scope: str = "closed-r11-pair-projection"


@dataclass(frozen=True)
class ObserverMorphismJudgment:
    """Information factorization on C plus the separate strong-domain test."""

    morphism_id: str
    doctrine_fingerprint: str
    source_binding_digest: str
    fine_observer_id: str
    coarse_observer_id: str
    fine_domain: R11DomainProfile
    coarse_domain: R11DomainProfile
    comparison_domain: ComparisonDomain
    translation: ResponseTranslation | None
    information_factorizes_on_comparison: bool
    coarse_domain_in_fine_domain: bool
    witness_checked: bool
    information_loss: InformationLoss
    status: MorphismStatus
    obstruction: str
    scope: str = "provisional-p1a-observer-morphism"

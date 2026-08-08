"""Disjoint doctrine-open and genealogy-unavailable P3-N0 envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .prime_power_observer_actualization_evidence_types import N0TheoremSource
from .prime_power_observer_actualization_types import (
    ActualizationStatus, N0FormalFailure, N0Policy, N0ResourceLimit, PremiseStatus,
    PrimePowerObserverActualizationJudgment, PrimePowerObserverDoctrine, RoleStatus,
    UnavailableFamilyFiniteBridgeEvidence,
)


@dataclass(frozen=True)
class N0DoctrineOpen:
    source_digest: str
    run_digest: str
    doctrine_digest: str
    genealogy: PremiseStatus
    role: RoleStatus
    actualization: ActualizationStatus
    result_digest: str


@dataclass(frozen=True)
class N0UnavailableSource:
    prime: int
    depth: int
    lineage_id: str
    doctrine: PrimePowerObserverDoctrine
    policy: N0Policy
    theorem_source: N0TheoremSource
    bridge_evidence: UnavailableFamilyFiniteBridgeEvidence
    source_digest: str


@dataclass(frozen=True)
class N0UnavailableBridgeRequest:
    source: N0UnavailableSource
    reason: str
    evidence_digest: str
    request_digest: str


@dataclass(frozen=True)
class N0GenealogyUnavailable:
    source_digest: str
    request_digest: str
    run_digest: str
    evidence_digest: str
    genealogy: PremiseStatus
    role: RoleStatus
    actualization: ActualizationStatus
    result_digest: str


N0Result: TypeAlias = (
    PrimePowerObserverActualizationJudgment | N0DoctrineOpen | N0GenealogyUnavailable
    | N0ResourceLimit | N0FormalFailure
)

"""Closed finite counterexample DTOs for P1-D3 candidate family laws."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .all_depth_family_types import (
    CompletedCarrierStatus, FamilyEvidenceStatus, LawStatus,
)


class FamilyLaw(str, Enum):
    RELATION_REFLEXIVE = "relation-reflexive"
    RELATION_TRANSITIVE = "relation-transitive"
    RESTRICTION_CONGRUENCE = "restriction-congruence"
    RESTRICTION_IDENTITY = "restriction-identity"
    RESTRICTION_COMPOSITION = "restriction-composition"


class FamilyNonexistence(str, Enum):
    NOT_PROVED = "not-proved"


@dataclass(frozen=True)
class RelationEdge:
    left: str
    right: str


@dataclass(frozen=True)
class RestrictionRow:
    map_id: str
    source: str
    target: str


@dataclass(frozen=True)
class FiniteFamilyLawWitness:
    version: str
    law: FamilyLaw
    universe: tuple[str, ...]
    relation_edges: tuple[RelationEdge, ...]
    restriction_rows: tuple[RestrictionRow, ...]
    arguments: tuple[str, ...]
    witness_digest: str


@dataclass(frozen=True)
class CounterexampleLawVector:
    relation_reflexive: LawStatus
    relation_transitive: LawStatus
    restriction_congruence: LawStatus
    restriction_identity: LawStatus
    restriction_composition: LawStatus


@dataclass(frozen=True)
class FamilyLawCounterexampleAssessment:
    specification_digest: str
    source_digest: str
    law: FamilyLaw
    witness_digest: str
    evaluator_id: str
    evaluator_digest: str
    affected_status: LawStatus
    law_statuses: CounterexampleLawVector
    result_digest: str
    family_evidence: FamilyEvidenceStatus = FamilyEvidenceStatus.OPEN
    family_nonexistence: FamilyNonexistence = FamilyNonexistence.NOT_PROVED
    afip_introduction: bool = False
    completed_carrier: CompletedCarrierStatus = CompletedCarrierStatus.NOT_ESTABLISHED
    scope: str = "finite-candidate-law-counterexample-no-afip-impact"

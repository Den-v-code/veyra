"""Typed DTOs for declared P3-OG blind-selection source closure.

This module deliberately models only dependency information declared inside the
finite Veyra experiment.  It does not authenticate undeclared external inputs or
real-world chronology.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SelectionDependencyKind(str, Enum):
    """Typed provenance categories for selection dependencies."""

    PRESSURE_SOURCE = "pressure-source"
    POOL = "pool"
    BLIND_SEED = "blind-seed"
    SELECTOR_LAW = "selector-law"
    TRANSFORM = "transform"
    DISCRIMINATION_CRITERION = "discrimination-criterion"
    TARGET = "target"
    SELECTED_RESPONSE = "selected-response"
    LATER_STATUS = "later-status"
    THEOREM_CONCLUSION = "theorem-conclusion"


@dataclass(frozen=True, slots=True)
class P3OGSelectionDependencyNode:
    """One dependency node; ``parent_ids`` are the information it depends on."""

    node_id: str
    kind: SelectionDependencyKind
    parent_ids: tuple[str, ...]
    payload_digest: str
    node_digest: str


@dataclass(frozen=True, slots=True)
class P3OGSelectionSourceClosure:
    """Graph-derived transitive dependency closure of the three selection roots."""

    version: str
    pressure_source_digest: str
    nodes: tuple[P3OGSelectionDependencyNode, ...]
    root_ids: tuple[str, ...]
    closure_node_ids: tuple[str, ...]
    forbidden_node_ids: tuple[str, ...]
    boundary: str
    closure_digest: str


P3OG_SELECTION_SOURCE_CLOSURE_BOUNDARY = (
    "declared finite dependency graph only: proves that no typed criterion, target, "
    "selected response, later status, or theorem conclusion occurs in the transitive "
    "declared source closure of Pool/BlindSeed/SelectorLaw; does not authenticate "
    "undeclared or out-of-band dependencies, trusted chronology, one-shot occurrence, "
    "operator non-bypass, formation, observer role, HAP, theoremhood, or promotion"
)


P3OG_SELECTION_SOURCE_CLOSURE_NONCLAIMS = (
    "full-def-og-002-discharge",
    "historical-strict-past-commitment",
    "one-shot-capability-consumption",
    "undeclared-or-out-of-band-source-dependency-blindness",
    "externally-authenticated-dependency-completeness",
    "criterion-or-result-truth",
    "formation-or-first-closure",
    "typed-history-or-def-og-009-discharge",
    "doctrine-admission-or-observer-role",
    "n0-or-hap-lift",
    "formal-theorem-or-certificate",
    "promotion",
)

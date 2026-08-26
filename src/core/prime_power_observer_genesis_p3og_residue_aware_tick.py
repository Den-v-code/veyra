"""Non-root facade for residue-aware P3-OG semantic tick pressure."""

from .prime_power_observer_genesis_p3og_residue_aware_tick_runtime import (
    build_p3og_residue_aware_formation_compatibility_evidence,
    residue_aware_semantic_tick,
    validate_p3og_residue_aware_formation_compatibility_evidence,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_source import (
    p3og_residue_aware_tick_source,
    residue_aware_tick_rule,
    validate_residue_aware_tick_source,
)
from .prime_power_observer_genesis_p3og_residue_aware_tick_types import (
    P3OGResidueAwareFormationCompatibilityEvidence,
    P3OGResidueAwareTickSource,
    P3OG_RESIDUE_AWARE_TICK_NONCLAIMS,
    ResidueAwareFormationCompatibilityStatus,
    ResidueAwareSemanticTickReceipt,
    ResidueAwareTickRule,
    ResiduePresenceClass,
)

__all__ = (
    "P3OGResidueAwareFormationCompatibilityEvidence",
    "P3OGResidueAwareTickSource",
    "P3OG_RESIDUE_AWARE_TICK_NONCLAIMS",
    "ResidueAwareFormationCompatibilityStatus",
    "ResidueAwareSemanticTickReceipt",
    "ResidueAwareTickRule",
    "ResiduePresenceClass",
    "build_p3og_residue_aware_formation_compatibility_evidence",
    "p3og_residue_aware_tick_source",
    "residue_aware_semantic_tick",
    "residue_aware_tick_rule",
    "validate_p3og_residue_aware_formation_compatibility_evidence",
    "validate_residue_aware_tick_source",
)

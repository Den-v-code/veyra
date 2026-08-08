"""Frozen bounded DTO schema targets for P2-S2."""

from __future__ import annotations

import logging

from .status_promotion_digest import digest, text_rows
from .status_promotion_types import SchemaTarget

logger = logging.getLogger(__name__)

SCHEMA_ROWS = (
    ("finite-construction-judgment", (
        "doctrine_fingerprint", "source_binding_digest", "target_stage_id",
        "target_commitment", "replay", "formal_generability", "obstruction",
        "ontic_genesis", "target_independence", "scoped_object", "scope",
    )),
    ("observer-genesis-judgment", (
        "doctrine_digest", "source_digest", "adapter_digest", "witness_digest",
        "recurrence_digest", "oep_digest", "run_digest", "judgment_digest",
        "operation_status", "premises", "primitive_genealogy", "structural_closure",
        "recurrent_return", "counterfactual_discrimination", "bounded_persistence",
        "residue_efficacy", "observer_role_relative_to_scope",
        "historical_target_independence", "physical_instantiation", "scope",
    )),
    ("fork-confluence-judgment", (
        "plan_id", "plan_digest", "status", "transport_cell", "first_obstruction",
        "charged_checks", "local_finite_confluence", "global_confluence",
        "scoped_formation", "scope",
    )),
    ("finite-confluence-aggregate", (
        "doctrine_fingerprint", "diagram_digest", "catalog_digest", "policy_digest",
        "run_digest", "expected_local_keys", "expected_global_keys", "rows",
        "local_status", "global_status", "coverage", "first_obstruction",
        "total_charge", "nonclaims", "aggregate_digest",
    )),
    ("all-depth-family-judgment", (
        "spec", "source", "spec_validity", "coordinate_totality",
        "restriction_compatibility", "algebraic_laws", "evidence_status",
        "provenance", "ledger_status", "ledger_digest", "foundation_id",
        "tcb_digest", "family_term_digest", "introduction_evidence_digest",
        "judgment_digest", "completed_carrier", "universal_realization",
        "observer_separation", "scope",
    )),
)


def schema_targets(forbidden: tuple[str, ...]) -> tuple[SchemaTarget, ...]:
    """Return exact allowlisted schema commitments without module discovery."""
    logger.debug("schema_targets entry rows=%d", len(SCHEMA_ROWS))
    result = tuple(
        SchemaTarget(schema_id, fields, forbidden, digest("veyra.p2s.schema.v1", (
            ("schema-id", schema_id.encode()),
            *text_rows("field", fields),
            *text_rows("forbidden", forbidden),
        )))
        for schema_id, fields in SCHEMA_ROWS
    )
    logger.debug("schema_targets exit rows=%d", len(result))
    return result

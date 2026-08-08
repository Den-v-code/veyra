"""Exact closed grammar and evaluator for finite P1-D3 law counterexamples."""

from __future__ import annotations

import logging

from .all_depth_family_common import exact_digest, exact_identifier, exact_shape, reject
from .all_depth_family_digest import digest, frame, text_rows
from .all_depth_family_counterexample_types import (
    FamilyLaw, FiniteFamilyLawWitness, RelationEdge, RestrictionRow,
)

logger = logging.getLogger(__name__)
WITNESS_VERSION = "p1-d3-law-counterexample-v1"
EVALUATOR_ID = "p1-d3-closed-finite-law-evaluator-v1"
MAX_UNIVERSE = 32
MAX_RELATION_EDGES = 1024
MAX_RESTRICTION_ROWS = 1024
_ARG_COUNTS = {
    FamilyLaw.RELATION_REFLEXIVE: 1,
    FamilyLaw.RELATION_TRANSITIVE: 3,
    FamilyLaw.RESTRICTION_CONGRUENCE: 3,
    FamilyLaw.RESTRICTION_IDENTITY: 2,
    FamilyLaw.RESTRICTION_COMPOSITION: 4,
}


def relation_edge(left: str, right: str) -> RelationEdge:
    """Build one exact directed candidate-relation edge."""
    logger.debug("relation_edge entry")
    result = RelationEdge(
        exact_identifier(left, "relation-left"), exact_identifier(right, "relation-right"),
    )
    logger.debug("relation_edge exit")
    return result


def restriction_row(map_id: str, source: str, target: str) -> RestrictionRow:
    """Build one exact finite restriction-table row."""
    logger.debug("restriction_row entry")
    result = RestrictionRow(
        exact_identifier(map_id, "restriction-map-id"),
        exact_identifier(source, "restriction-source"),
        exact_identifier(target, "restriction-target"),
    )
    logger.debug("restriction_row exit")
    return result


def _snapshot_edge(value: RelationEdge) -> RelationEdge:
    logger.debug("_snapshot_edge entry")
    exact_shape(value, RelationEdge, "relation-edge")
    try:
        result = relation_edge(value.left, value.right)
    except AttributeError:
        reject("relation-edge-missing-fields")
    logger.debug("_snapshot_edge exit")
    return result


def _snapshot_restriction(value: RestrictionRow) -> RestrictionRow:
    logger.debug("_snapshot_restriction entry")
    exact_shape(value, RestrictionRow, "restriction-row")
    try:
        result = restriction_row(value.map_id, value.source, value.target)
    except AttributeError:
        reject("restriction-row-missing-fields")
    logger.debug("_snapshot_restriction exit")
    return result


def _witness_digest(
    law: FamilyLaw, universe: tuple[str, ...], edges: tuple[RelationEdge, ...],
    rows: tuple[RestrictionRow, ...], arguments: tuple[str, ...],
) -> str:
    logger.debug("_witness_digest entry law=%s", law.value)
    edge_bytes = tuple(
        (f"edge-{i}", frame("veyra.p1d3.law-edge.v1", (
            ("left", row.left.encode()), ("right", row.right.encode()),
        ))) for i, row in enumerate(edges)
    )
    row_bytes = tuple(
        (f"restriction-{i}", frame("veyra.p1d3.restriction-row.v1", (
            ("map", row.map_id.encode()), ("source", row.source.encode()),
            ("target", row.target.encode()),
        ))) for i, row in enumerate(rows)
    )
    result = digest("veyra.p1d3.law-witness.v1", (
        ("version", WITNESS_VERSION.encode()), ("law", law.value.encode()),
        *text_rows("universe", universe),
        ("edge-count", len(edges).to_bytes(8, "big")), *edge_bytes,
        ("restriction-count", len(rows).to_bytes(8, "big")), *row_bytes,
        *text_rows("argument", arguments),
    ))
    logger.debug("_witness_digest exit")
    return result


def finite_family_law_witness(
    law: FamilyLaw, universe: tuple[str, ...], relation_edges: tuple[RelationEdge, ...],
    restriction_rows: tuple[RestrictionRow, ...], arguments: tuple[str, ...],
) -> FiniteFamilyLawWitness:
    """Capture a bounded finite model and one exact law-test argument tuple."""
    logger.debug("finite_family_law_witness entry")
    if type(law) is not FamilyLaw:
        reject("family-law-must-be-exact")
    if type(universe) is not tuple or not 1 <= len(universe) <= MAX_UNIVERSE:
        reject("invalid-law-witness-universe")
    captured_universe = tuple(exact_identifier(item, "law-universe-item") for item in universe)
    if len(set(captured_universe)) != len(captured_universe):
        reject("duplicate-law-universe-item")
    if type(relation_edges) is not tuple or len(relation_edges) > MAX_RELATION_EDGES:
        reject("invalid-relation-edge-table")
    edges = tuple(_snapshot_edge(item) for item in relation_edges)
    if len({(item.left, item.right) for item in edges}) != len(edges):
        reject("duplicate-relation-edge")
    if any(item.left not in captured_universe or item.right not in captured_universe for item in edges):
        reject("relation-edge-universe-transplant")
    if type(restriction_rows) is not tuple or len(restriction_rows) > MAX_RESTRICTION_ROWS:
        reject("invalid-restriction-table")
    rows = tuple(_snapshot_restriction(item) for item in restriction_rows)
    if len({(item.map_id, item.source) for item in rows}) != len(rows):
        reject("nondeterministic-restriction-table")
    if any(item.source not in captured_universe or item.target not in captured_universe for item in rows):
        reject("restriction-row-universe-transplant")
    if type(arguments) is not tuple or len(arguments) != _ARG_COUNTS[law]:
        reject("invalid-law-witness-arguments")
    args = tuple(exact_identifier(item, "law-witness-argument") for item in arguments)
    _validate_argument_kinds(law, captured_universe, args)
    value = _witness_digest(law, captured_universe, edges, rows, args)
    result = FiniteFamilyLawWitness(
        WITNESS_VERSION, law, captured_universe, edges, rows, args, value,
    )
    logger.debug("finite_family_law_witness exit")
    return result


def _validate_argument_kinds(law: FamilyLaw, universe: tuple[str, ...], args: tuple[str, ...]) -> None:
    logger.debug("_validate_argument_kinds entry law=%s", law.value)
    value_args = args if law in (FamilyLaw.RELATION_REFLEXIVE, FamilyLaw.RELATION_TRANSITIVE) else (
        args[1:] if law is not FamilyLaw.RESTRICTION_COMPOSITION else args[3:]
    )
    if any(item not in universe for item in value_args):
        reject("law-witness-value-argument-transplant")
    logger.debug("_validate_argument_kinds exit")


def snapshot_family_law_witness(value: FiniteFamilyLawWitness) -> FiniteFamilyLawWitness:
    """Rebuild every nested scalar before comparing the commitment."""
    logger.debug("snapshot_family_law_witness entry")
    exact_shape(value, FiniteFamilyLawWitness, "finite-family-law-witness")
    try:
        if type(value.version) is not str or value.version != WITNESS_VERSION:
            reject("law-witness-version-drift")
        exact_digest(value.witness_digest, "witness-digest")
        expected = finite_family_law_witness(
            value.law, value.universe, value.relation_edges,
            value.restriction_rows, value.arguments,
        )
    except AttributeError:
        reject("finite-family-law-witness-missing-fields")
    if value != expected:
        reject("finite-family-law-witness-drift")
    logger.debug("snapshot_family_law_witness exit")
    return expected


def witness_refutes_law(value: FiniteFamilyLawWitness) -> bool:
    """Evaluate the exact directed relation/restriction grammar, not caller booleans."""
    logger.debug("witness_refutes_law entry")
    value = snapshot_family_law_witness(value)
    edges = {(row.left, row.right) for row in value.relation_edges}
    restrictions = {(row.map_id, row.source): row.target for row in value.restriction_rows}
    args = value.arguments
    try:
        if value.law is FamilyLaw.RELATION_REFLEXIVE:
            result = (args[0], args[0]) not in edges
        elif value.law is FamilyLaw.RELATION_TRANSITIVE:
            x, y, z = args
            result = (x, y) in edges and (y, z) in edges and (x, z) not in edges
        elif value.law is FamilyLaw.RESTRICTION_CONGRUENCE:
            map_id, x, y = args
            result = (x, y) in edges and (
                restrictions[(map_id, x)], restrictions[(map_id, y)]
            ) not in edges
        elif value.law is FamilyLaw.RESTRICTION_IDENTITY:
            map_id, x = args
            result = (restrictions[(map_id, x)], x) not in edges
        else:
            upper, lower, direct, x = args
            via = restrictions[(lower, restrictions[(upper, x)])]
            result = (via, restrictions[(direct, x)]) not in edges
    except KeyError:
        reject("law-witness-missing-restriction-row")
    logger.debug("witness_refutes_law exit result=%s", result)
    return result

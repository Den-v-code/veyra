"""Sage-friendly facade for finite topology echo checks."""

from __future__ import annotations

import logging

from src.core.topology_echo import topology_echo_checklist, topology_echo_shapes, topology_echo_summary, topology_invariant_rows, topology_obstruction_cards

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


def _display(value: object) -> object:
    """Return JSON-ready display value."""
    logger.debug("_display entry value=%r", value)
    result = str(value) if not isinstance(value, (int, bool)) else value
    logger.debug("_display exit result=%r", result)
    return result


class VeyraTopologyLab:
    """Finite topology echo lab over corridor and shell shadows."""

    def shape_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready shape invariant rows."""
        logger.debug("VeyraTopologyLab.shape_rows entry")
        result = [
            {
                "name": shape.name,
                "kind": shape.kind,
                "nodes": list(shape.nodes),
                "corridors": [list(edge) for edge in shape.corridors],
                "component_count": shape.component_count,
                "boundary_count": shape.boundary_count,
                "cycle_rank": shape.cycle_rank,
            }
            for shape in topology_echo_shapes()
        ]
        logger.debug("VeyraTopologyLab.shape_rows exit count=%d", len(result))
        return result

    def invariant_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready invariant comparison rows."""
        logger.debug("VeyraTopologyLab.invariant_rows entry")
        result = [row.__dict__.copy() for row in topology_invariant_rows()]
        logger.debug("VeyraTopologyLab.invariant_rows exit count=%d", len(result))
        return result

    def obstruction_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready obstruction cards."""
        logger.debug("VeyraTopologyLab.obstruction_rows entry")
        result = [card.__dict__.copy() for card in topology_obstruction_cards()]
        logger.debug("VeyraTopologyLab.obstruction_rows exit count=%d", len(result))
        return result

    def checklist(self) -> list[str]:
        """Return X4 acceptance checklist."""
        logger.debug("VeyraTopologyLab.checklist entry")
        result = list(topology_echo_checklist())
        logger.debug("VeyraTopologyLab.checklist exit count=%d", len(result))
        return result

    def summary(self) -> dict[str, int]:
        """Return compact topology echo summary."""
        logger.debug("VeyraTopologyLab.summary entry")
        result = topology_echo_summary()
        logger.debug("VeyraTopologyLab.summary exit result=%r", result)
        return result


def build_topology_echo_notebook() -> VeyraNotebook:
    """Build executable topology echo notebook."""
    logger.debug("build_topology_echo_notebook entry")
    cells = [
        VeyraNotebookCell("markdown", "# Veyra Topology Echo Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraTopologyLab\nlab = VeyraTopologyLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['invariant_hits'] == 4\nassert summary['blocked'] == 2"),
        VeyraNotebookCell("code", "assert len(lab.invariant_rows()) == 4\nassert lab.obstruction_rows()[-1]['obstruction'] == 'cycle-collapse'"),
        VeyraNotebookCell("markdown", "Topology-like claims stay finite: deformation-invariant corridor/shell echoes plus obstruction cards."),
    ]
    result = VeyraNotebook("topology_echo", tuple(cells))
    logger.debug("build_topology_echo_notebook exit summary=%r", result.summary())
    return result


def topology_echo_lab_summary() -> dict[str, int]:
    """Return Sage facade topology echo summary."""
    logger.debug("topology_echo_lab_summary entry")
    result = VeyraTopologyLab().summary()
    logger.debug("topology_echo_lab_summary exit result=%r", result)
    return result

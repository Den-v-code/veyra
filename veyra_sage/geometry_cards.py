"""Sage-facing geometry theorem-card and visual rows."""

from __future__ import annotations

import logging

from src.core.geometry_visual_regression import geometry_visual_scene_rows
from .card_examples import card_examples, run_card_example
from .notebooks import VeyraNotebook, VeyraNotebookCell
from .proof_discipline import VeyraProofDisciplineLab

logger = logging.getLogger(__name__)


class VeyraGeometryTheoremLab:
    """Sage-facing reader for geometry theorem cards, visuals, and exports."""

    def summary(self) -> dict[str, object]:
        """Return compact geometry theorem-card export summary."""
        logger.debug("VeyraGeometryTheoremLab.summary entry")
        cards = self.card_rows()
        result = {"cards": len(cards), "ready": sum(row["status"] == "ready" for row in cards), "visual_scenes": len(self.visual_rows()), "stable_exports": len(self.stable_export_rows()), "package_stable": False}
        logger.debug("VeyraGeometryTheoremLab.summary exit result=%r", result)
        return result

    def card_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready geometry theorem-card check rows."""
        logger.debug("VeyraGeometryTheoremLab.card_rows entry")
        result = [run_card_example(row.theorem_id).as_dict() | {"title": row.title, "source": row.source} for row in card_examples("geometry")]
        logger.debug("VeyraGeometryTheoremLab.card_rows exit count=%d", len(result))
        return result

    def visual_rows(self) -> list[dict[str, object]]:
        """Return lightweight visual scene rows for geometry notebooks."""
        logger.debug("VeyraGeometryTheoremLab.visual_rows entry")
        result = [dict(row) for row in geometry_visual_scene_rows()]
        logger.debug("VeyraGeometryTheoremLab.visual_rows exit count=%d", len(result))
        return result

    def stable_export_rows(self) -> list[dict[str, object]]:
        """Return geometry stable-card formal-export rows."""
        logger.debug("VeyraGeometryTheoremLab.stable_export_rows entry")
        rows = VeyraProofDisciplineLab().stable_export_rows()
        result = [row for row in rows if str(row["hook"]).startswith("geometry.")]
        logger.debug("VeyraGeometryTheoremLab.stable_export_rows exit count=%d", len(result))
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return Sprint G geometry export checklist."""
        logger.debug("VeyraGeometryTheoremLab.checklist entry")
        result = ("geometry theorem-card rows", "lightweight visual scene rows", "geometry stable-export rows", "package-stable Sage extension deferred")
        logger.debug("VeyraGeometryTheoremLab.checklist exit count=%d", len(result))
        return result


def build_geometry_theorem_card_notebook() -> VeyraNotebook:
    """Build notebook artifact for geometry theorem-card visuals and exports."""
    logger.debug("build_geometry_theorem_card_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Geometry Theorem-Card Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraGeometryTheoremLab\nlab = VeyraGeometryTheoremLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['cards'] == 5\nassert summary['ready'] == 5\nassert not summary['package_stable']"),
        VeyraNotebookCell("code", "assert len(lab.stable_export_rows()) == 5\nassert len(lab.checklist()) == 4"),
        VeyraNotebookCell("markdown", "## Visual scene rows\n\nRows are lightweight JSON sketches for later Sage/TikZ rendering."),
        VeyraNotebookCell("code", "visuals = lab.visual_rows()\nassert len(visuals) == 3\nvisuals"),
    )
    result = VeyraNotebook("Geometry Theorem-Card Lab", cells)
    logger.debug("build_geometry_theorem_card_notebook exit summary=%r", result.summary())
    return result


def geometry_theorem_lab_summary() -> dict[str, object]:
    """Return default geometry theorem-card lab summary."""
    logger.debug("geometry_theorem_lab_summary entry")
    result = VeyraGeometryTheoremLab().summary()
    logger.debug("geometry_theorem_lab_summary exit result=%r", result)
    return result

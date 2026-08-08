"""Sage-facing facade for the Veyra Essence/Core contract."""

from __future__ import annotations

import logging

from src.core.essence import essence_checklist, essence_report

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


class VeyraEssenceLab:
    """Sage-facing reader for executable Veyra Essence/Core readiness."""

    def summary(self) -> dict[str, object]:
        """Return compact Essence/Core summary."""
        logger.debug("VeyraEssenceLab.summary entry")
        result = essence_report().summary()
        logger.debug("VeyraEssenceLab.summary exit result=%r", result)
        return result

    def axiom_rows(self) -> list[dict[str, str]]:
        """Return JSON-ready Essence axiom rows."""
        logger.debug("VeyraEssenceLab.axiom_rows entry")
        result = [item.as_dict() for item in essence_report().axioms]
        logger.debug("VeyraEssenceLab.axiom_rows exit count=%d", len(result))
        return result

    def layer_rows(self) -> list[dict[str, str]]:
        """Return JSON-ready core layer rows."""
        logger.debug("VeyraEssenceLab.layer_rows entry")
        result = [item.as_dict() for item in essence_report().layers]
        logger.debug("VeyraEssenceLab.layer_rows exit count=%d", len(result))
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return Essence/Core completion checklist."""
        logger.debug("VeyraEssenceLab.checklist entry")
        result = essence_checklist()
        logger.debug("VeyraEssenceLab.checklist exit count=%d", len(result))
        return result


def build_essence_core_notebook() -> VeyraNotebook:
    """Build notebook artifact for Essence/Core smoke checks."""
    logger.debug("build_essence_core_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Essence/Core Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraEssenceLab\nlab = VeyraEssenceLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['core_ready']\nassert summary['axioms'] == 9"),
        VeyraNotebookCell("code", "assert len(lab.layer_rows()) == 36\nassert summary['theorem_derived'] == 2\nassert not summary['proof_complete']\nassert len(lab.checklist()) == 6"),
        VeyraNotebookCell("markdown", "Essence/Core is exposed as a finite readiness report."),
    )
    result = VeyraNotebook("Essence Core Lab", cells)
    logger.debug("build_essence_core_notebook exit summary=%r", result.summary())
    return result


def essence_lab_summary() -> dict[str, object]:
    """Return default Essence/Core lab summary."""
    logger.debug("essence_lab_summary entry")
    result = VeyraEssenceLab().summary()
    logger.debug("essence_lab_summary exit result=%r", result)
    return result

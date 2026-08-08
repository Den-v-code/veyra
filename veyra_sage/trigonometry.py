"""Sage-facing facade for Veyra trigonometry identity seeds."""

from __future__ import annotations

import logging

from src.core.ratio import ratio_shadow
from src.core.trigonometry_identities import double_angle_identity_card, inverse_phase_identity_card, pythagorean_identity_card, sum_angle_identity_card, trig_vector_from_ints, trigonometry_identity_checklist, unit_identity_gap

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


class VeyraTrigonometryIdentityLab:
    """Sage-facing reader for rational trigonometry identity cards."""

    def summary(self) -> dict[str, object]:
        """Return compact trigonometry identity summary."""
        logger.debug("VeyraTrigonometryIdentityLab.summary entry")
        rows = self.card_rows()
        result = {"checklist": len(self.checklist()), "cards": len(rows), "all_coherent": all(row["relation"] == "coherent" for row in rows), "unit_ready": self.phase_rows()[0]["gap"] == "0"}
        logger.debug("VeyraTrigonometryIdentityLab.summary exit result=%r", result)
        return result

    def phase_rows(self) -> list[dict[str, str]]:
        """Return JSON-ready rational phase rows."""
        logger.debug("VeyraTrigonometryIdentityLab.phase_rows entry")
        phases = (trig_vector_from_ints(3, 4, 5, "a"), trig_vector_from_ints(5, 12, 13, "b"))
        result = [{"label": item.label, "cos": item.shadow_pair()[0], "sin": item.shadow_pair()[1], "gap": str(ratio_shadow(unit_identity_gap(item)))} for item in phases]
        logger.debug("VeyraTrigonometryIdentityLab.phase_rows exit count=%d", len(result))
        return result

    def card_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready trigonometry theorem-card rows."""
        logger.debug("VeyraTrigonometryIdentityLab.card_rows entry")
        first = trig_vector_from_ints(3, 4, 5, "a")
        second = trig_vector_from_ints(5, 12, 13, "b")
        cards = (pythagorean_identity_card(first), sum_angle_identity_card(first, second), double_angle_identity_card(first), inverse_phase_identity_card(first))
        result = [{"name": card.name, "status": card.status, "relation": card.relation, "obstruction": card.obstruction, "evidence": list(card.evidence)} for card in cards]
        logger.debug("VeyraTrigonometryIdentityLab.card_rows exit count=%d", len(result))
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return trigonometry identity checklist."""
        logger.debug("VeyraTrigonometryIdentityLab.checklist entry")
        result = trigonometry_identity_checklist()
        logger.debug("VeyraTrigonometryIdentityLab.checklist exit count=%d", len(result))
        return result


def build_trigonometry_identity_notebook() -> VeyraNotebook:
    """Build notebook artifact for trigonometry identity smoke checks."""
    logger.debug("build_trigonometry_identity_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Trigonometry Identity Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraTrigonometryIdentityLab\nlab = VeyraTrigonometryIdentityLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['all_coherent']\nassert summary['unit_ready']"),
        VeyraNotebookCell("code", "assert len(lab.phase_rows()) == 2\nassert len(lab.card_rows()) == 4"),
        VeyraNotebookCell("markdown", "Trigonometry identities are exposed as rational phase theorem-card rows."),
    )
    result = VeyraNotebook("Trigonometry Identity Lab", cells)
    logger.debug("build_trigonometry_identity_notebook exit summary=%r", result.summary())
    return result


def trigonometry_identity_lab_summary() -> dict[str, object]:
    """Return default trigonometry identity lab summary."""
    logger.debug("trigonometry_identity_lab_summary entry")
    result = VeyraTrigonometryIdentityLab().summary()
    logger.debug("trigonometry_identity_lab_summary exit result=%r", result)
    return result

"""Sage-facing facade for Veyra linear algebra seed shadows."""

from __future__ import annotations

import logging

from src.core.linear_algebra import determinant_2x2, determinant_product_card, eigen_candidate_card, linear_algebra_seed_checklist, matrix_from_ints, matrix_vector_apply, trace_2x2, vector_from_ints
from src.core.ratio import ratio_from_ints, ratio_shadow

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


class VeyraLinearAlgebraLab:
    """Sage-facing reader for vector/matrix seed rows."""

    def summary(self) -> dict[str, object]:
        """Return compact linear algebra seed summary."""
        logger.debug("VeyraLinearAlgebraLab.summary entry")
        cards = self.card_rows()
        action = self.action_row()
        result = {"checklist": len(self.checklist()), "cards": len(cards), "action_ready": action["image"] == ["2", "6"], "determinant_ready": cards[0]["relation"] == "coherent"}
        logger.debug("VeyraLinearAlgebraLab.summary exit result=%r", result)
        return result

    def action_row(self) -> dict[str, object]:
        """Return JSON-ready matrix action row."""
        logger.debug("VeyraLinearAlgebraLab.action_row entry")
        matrix = matrix_from_ints([[2, 0], [0, 3]])
        vector = vector_from_ints([1, 2])
        image = matrix_vector_apply(matrix, vector)
        result = {"shape": list(matrix.shape), "vector": [str(ratio_shadow(value)) for value in vector.values], "image": [str(ratio_shadow(value)) for value in image.values], "det": str(ratio_shadow(determinant_2x2(matrix))), "trace": str(ratio_shadow(trace_2x2(matrix)))}
        logger.debug("VeyraLinearAlgebraLab.action_row exit result=%r", result)
        return result

    def card_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready theorem-card rows."""
        logger.debug("VeyraLinearAlgebraLab.card_rows entry")
        cards = (determinant_product_card(matrix_from_ints([[1, 2], [3, 4]]), matrix_from_ints([[2, 0], [1, 2]])), eigen_candidate_card(matrix_from_ints([[2, 0], [0, 3]]), vector_from_ints([1, 0]), ratio_from_ints(2)))
        result = [{"name": card.name, "status": card.status, "relation": card.relation, "obstruction": card.obstruction, "evidence": list(card.evidence)} for card in cards]
        logger.debug("VeyraLinearAlgebraLab.card_rows exit count=%d", len(result))
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return linear algebra seed checklist."""
        logger.debug("VeyraLinearAlgebraLab.checklist entry")
        result = linear_algebra_seed_checklist()
        logger.debug("VeyraLinearAlgebraLab.checklist exit count=%d", len(result))
        return result


def build_linear_algebra_seed_notebook() -> VeyraNotebook:
    """Build notebook artifact for linear algebra seed smoke checks."""
    logger.debug("build_linear_algebra_seed_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Linear Algebra Seed Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraLinearAlgebraLab\nlab = VeyraLinearAlgebraLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['action_ready']\nassert summary['determinant_ready']"),
        VeyraNotebookCell("code", "assert len(lab.card_rows()) == 2\nassert len(lab.checklist()) == 4"),
        VeyraNotebookCell("markdown", "Linear algebra seeds are exposed as matrix action and theorem-card rows."),
    )
    result = VeyraNotebook("Linear Algebra Seed Lab", cells)
    logger.debug("build_linear_algebra_seed_notebook exit summary=%r", result.summary())
    return result


def linear_algebra_seed_lab_summary() -> dict[str, object]:
    """Return default linear algebra seed lab summary."""
    logger.debug("linear_algebra_seed_lab_summary entry")
    result = VeyraLinearAlgebraLab().summary()
    logger.debug("linear_algebra_seed_lab_summary exit result=%r", result)
    return result

"""Sage-facing facade for Veyra calculus-depth shadows."""

from __future__ import annotations

import logging

from src.core.calculus_depth import calculus_depth_checklist, chain_rule_card, integral_coherence, integral_coherence_card, linearization_error, local_linearization, product_rule_card
from src.core.polynomial import polynomial_from_ints
from src.core.ratio import ratio_from_ints, ratio_shadow

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


class VeyraCalculusLab:
    """Sage-facing reader for polynomial calculus-depth certificates."""

    def summary(self) -> dict[str, object]:
        """Return compact calculus-depth lab summary."""
        logger.debug("VeyraCalculusLab.summary entry")
        rows = self.card_rows()
        result = {"checklist": len(self.checklist()), "cards": len(rows), "linearization_ready": self.linearization_row()["obstruction"] == "none", "integral_ready": rows[-1]["relation"] == "coherent"}
        logger.debug("VeyraCalculusLab.summary exit result=%r", result)
        return result

    def linearization_row(self) -> dict[str, object]:
        """Return JSON-ready local linearization smoke row."""
        logger.debug("VeyraCalculusLab.linearization_row entry")
        square = polynomial_from_ints([0, 0, 1])
        anchor = ratio_from_ints(3)
        point = ratio_from_ints(4)
        linear = local_linearization(square, anchor)
        error = linearization_error(square, anchor, point)
        result = {"anchor": str(ratio_shadow(anchor)), "value": str(ratio_shadow(linear.value)), "slope": str(ratio_shadow(linear.slope)), "point": str(ratio_shadow(point)), "error": str(ratio_shadow(error)), "obstruction": linear.obstruction}
        logger.debug("VeyraCalculusLab.linearization_row exit result=%r", result)
        return result

    def card_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready theorem-card rows for calculus-depth."""
        logger.debug("VeyraCalculusLab.card_rows entry")
        square = polynomial_from_ints([0, 0, 1])
        shift = polynomial_from_ints([1, 1])
        linear = polynomial_from_ints([0, 2])
        integral = integral_coherence(linear, ratio_from_ints(0), ratio_from_ints(3))
        cards = (product_rule_card(square, shift), chain_rule_card(square, shift), integral_coherence_card(linear, integral.lower, integral.upper, ratio_from_ints(9)))
        result = [{"name": card.name, "status": card.status, "relation": card.relation, "obstruction": card.obstruction, "evidence": list(card.evidence)} for card in cards]
        logger.debug("VeyraCalculusLab.card_rows exit count=%d", len(result))
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return calculus-depth acceptance checklist."""
        logger.debug("VeyraCalculusLab.checklist entry")
        result = calculus_depth_checklist()
        logger.debug("VeyraCalculusLab.checklist exit count=%d", len(result))
        return result


def build_calculus_depth_notebook() -> VeyraNotebook:
    """Build notebook artifact for calculus-depth smoke checks."""
    logger.debug("build_calculus_depth_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Calculus-Depth Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraCalculusLab\nlab = VeyraCalculusLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['linearization_ready']\nassert summary['integral_ready']"),
        VeyraNotebookCell("code", "assert len(lab.card_rows()) == 3\nassert len(lab.checklist()) == 4"),
        VeyraNotebookCell("markdown", "Calculus-depth is exposed as polynomial local/global coherence rows."),
    )
    result = VeyraNotebook("Calculus Depth Lab", cells)
    logger.debug("build_calculus_depth_notebook exit summary=%r", result.summary())
    return result


def calculus_depth_lab_summary() -> dict[str, object]:
    """Return default calculus-depth lab summary."""
    logger.debug("calculus_depth_lab_summary entry")
    result = VeyraCalculusLab().summary()
    logger.debug("calculus_depth_lab_summary exit result=%r", result)
    return result

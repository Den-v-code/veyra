"""Sage-facing facade for Veyra statistics inference seeds."""

from __future__ import annotations

import logging

from src.core.ratio import ratio_from_ints, ratio_shadow
from src.core.statistics_inference import bernoulli_family, hypothesis_mean_card, interval_contains_shadow, mean_interval, sample_echo_from_ints, standard_error_shadow, statistics_inference_checklist

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


class VeyraStatisticsInferenceLab:
    """Sage-facing reader for finite statistics inference rows."""

    def summary(self) -> dict[str, object]:
        """Return compact statistics inference summary."""
        logger.debug("VeyraStatisticsInferenceLab.summary entry")
        family = self.family_row()
        interval = self.interval_row()
        result = {"checklist": len(self.checklist()), "hypothesis_cards": len(self.hypothesis_rows()), "family_ready": family["p"] == "3/4", "interval_ready": interval["center"] == "2", "uncertainty": self.uncertainty_row()["variance_per_sample"]}
        logger.debug("VeyraStatisticsInferenceLab.summary exit result=%r", result)
        return result

    def family_row(self) -> dict[str, str]:
        """Return JSON-ready distribution-family row."""
        logger.debug("VeyraStatisticsInferenceLab.family_row entry")
        family = bernoulli_family(3, 4)
        result = {"name": family.name, "status": family.status, "p": family.parameter_shadow("p"), "variance": family.parameter_shadow("variance")}
        logger.debug("VeyraStatisticsInferenceLab.family_row exit result=%r", result)
        return result

    def interval_row(self) -> dict[str, object]:
        """Return JSON-ready mean-interval row."""
        logger.debug("VeyraStatisticsInferenceLab.interval_row entry")
        interval = mean_interval(sample_echo_from_ints([1, 2, 3]), ratio_from_ints(1, 2))
        result = {"center": str(ratio_shadow(interval.center)), "lower": str(ratio_shadow(interval.lower)), "upper": str(ratio_shadow(interval.upper)), "samples": interval.samples, "contains_center": interval_contains_shadow(interval, ratio_from_ints(2))}
        logger.debug("VeyraStatisticsInferenceLab.interval_row exit result=%r", result)
        return result

    def hypothesis_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready hypothesis-card rows."""
        logger.debug("VeyraStatisticsInferenceLab.hypothesis_rows entry")
        sample = sample_echo_from_ints([1, 2, 3])
        cards = (hypothesis_mean_card(sample, ratio_from_ints(2), ratio_from_ints(0)), hypothesis_mean_card(sample, ratio_from_ints(5), ratio_from_ints(1)))
        result = [{"name": card.name, "status": card.status, "relation": card.relation, "obstruction": card.obstruction, "evidence": list(card.evidence)} for card in cards]
        logger.debug("VeyraStatisticsInferenceLab.hypothesis_rows exit count=%d", len(result))
        return result

    def uncertainty_row(self) -> dict[str, str]:
        """Return JSON-ready uncertainty seed row."""
        logger.debug("VeyraStatisticsInferenceLab.uncertainty_row entry")
        result = {"variance_per_sample": str(ratio_shadow(standard_error_shadow(ratio_from_ints(3, 16), 4)))}
        logger.debug("VeyraStatisticsInferenceLab.uncertainty_row exit result=%r", result)
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return statistics inference checklist."""
        logger.debug("VeyraStatisticsInferenceLab.checklist entry")
        result = statistics_inference_checklist()
        logger.debug("VeyraStatisticsInferenceLab.checklist exit count=%d", len(result))
        return result


def build_statistics_inference_notebook() -> VeyraNotebook:
    """Build notebook artifact for statistics inference smoke checks."""
    logger.debug("build_statistics_inference_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Statistics Inference Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraStatisticsInferenceLab\nlab = VeyraStatisticsInferenceLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['family_ready']\nassert summary['interval_ready']"),
        VeyraNotebookCell("code", "assert len(lab.hypothesis_rows()) == 2\nassert len(lab.checklist()) == 4"),
        VeyraNotebookCell("markdown", "Statistics inference seeds are exposed as family, interval, hypothesis, and uncertainty rows."),
    )
    result = VeyraNotebook("Statistics Inference Lab", cells)
    logger.debug("build_statistics_inference_notebook exit summary=%r", result.summary())
    return result


def statistics_inference_lab_summary() -> dict[str, object]:
    """Return default statistics inference lab summary."""
    logger.debug("statistics_inference_lab_summary entry")
    result = VeyraStatisticsInferenceLab().summary()
    logger.debug("statistics_inference_lab_summary exit result=%r", result)
    return result

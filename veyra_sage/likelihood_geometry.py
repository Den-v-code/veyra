"""Sage-friendly facade for finite likelihood geometry checks."""

from __future__ import annotations

import logging

from src.core.likelihood_geometry import finite_likelihood_segments, likelihood_geometry_checklist, likelihood_geometry_summary, likelihood_grid, likelihood_peak_card, residual_family_certificates

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


class VeyraLikelihoodGeometryLab:
    """Finite likelihood/residual family lab."""

    def likelihood_rows(self) -> list[dict[str, str]]:
        """Return JSON-ready likelihood grid rows."""
        logger.debug("VeyraLikelihoodGeometryLab.likelihood_rows entry")
        result = [point.as_dict() for point in likelihood_grid()]
        logger.debug("VeyraLikelihoodGeometryLab.likelihood_rows exit count=%d", len(result))
        return result

    def segment_rows(self) -> list[dict[str, str]]:
        """Return JSON-ready finite likelihood segment rows."""
        logger.debug("VeyraLikelihoodGeometryLab.segment_rows entry")
        result = [segment.as_dict() for segment in finite_likelihood_segments(likelihood_grid())]
        logger.debug("VeyraLikelihoodGeometryLab.segment_rows exit count=%d", len(result))
        return result

    def peak_row(self) -> dict[str, str]:
        """Return JSON-ready finite peak card."""
        logger.debug("VeyraLikelihoodGeometryLab.peak_row entry")
        result = likelihood_peak_card(likelihood_grid()).as_dict()
        logger.debug("VeyraLikelihoodGeometryLab.peak_row exit result=%r", result)
        return result

    def residual_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready domain residual certificate rows."""
        logger.debug("VeyraLikelihoodGeometryLab.residual_rows entry")
        result = [cert.as_dict() for cert in residual_family_certificates()]
        logger.debug("VeyraLikelihoodGeometryLab.residual_rows exit count=%d", len(result))
        return result

    def checklist(self) -> list[str]:
        """Return X5 checklist."""
        logger.debug("VeyraLikelihoodGeometryLab.checklist entry")
        result = list(likelihood_geometry_checklist())
        logger.debug("VeyraLikelihoodGeometryLab.checklist exit count=%d", len(result))
        return result

    def summary(self) -> dict[str, int]:
        """Return compact likelihood geometry summary."""
        logger.debug("VeyraLikelihoodGeometryLab.summary entry")
        result = likelihood_geometry_summary()
        logger.debug("VeyraLikelihoodGeometryLab.summary exit result=%r", result)
        return result


def build_likelihood_geometry_notebook() -> VeyraNotebook:
    """Build executable likelihood geometry notebook."""
    logger.debug("build_likelihood_geometry_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Likelihood Geometry Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraLikelihoodGeometryLab\nlab = VeyraLikelihoodGeometryLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['likelihood_points'] == 3\nassert summary['blocked_domains'] == 1"),
        VeyraNotebookCell("code", "assert lab.peak_row()['parameter'] == '3/4'\nassert lab.residual_rows()[-1]['obstruction'] == 'residual-outlier'"),
        VeyraNotebookCell("markdown", "Likelihood geometry stays finite: parameter-grid slopes plus domain residual-family certificates."),
    )
    result = VeyraNotebook("likelihood_geometry", cells)
    logger.debug("build_likelihood_geometry_notebook exit summary=%r", result.summary())
    return result


def likelihood_geometry_lab_summary() -> dict[str, int]:
    """Return default likelihood geometry lab summary."""
    logger.debug("likelihood_geometry_lab_summary entry")
    result = VeyraLikelihoodGeometryLab().summary()
    logger.debug("likelihood_geometry_lab_summary exit result=%r", result)
    return result

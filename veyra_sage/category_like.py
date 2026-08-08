"""Sage-facing facade for Veyra category-like translation rows."""

from __future__ import annotations

import logging
from fractions import Fraction

from src.core.category_like import category_closure_rows, category_invariant_rows, category_like_checklist, category_like_examples, category_like_summary, category_universal_shadow_rows

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


def _display(value: object) -> object:
    """Return notebook-safe display value for exact shadows."""
    logger.debug("_display entry value=%r", value)
    if isinstance(value, tuple):
        result = tuple(_display(item) for item in value)
    elif isinstance(value, Fraction):
        result = str(value)
    else:
        result = value
    logger.debug("_display exit result=%r", result)
    return result


class VeyraCategoryLab:
    """Sage-facing reader for Sprint X3 finite category-like shadows."""

    def object_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready finite object rows."""
        logger.debug("VeyraCategoryLab.object_rows entry")
        result = [{"name": obj.name, "observer": obj.observer, "shadows": [_display(x) for x in obj.shadows]} for obj in category_like_examples()]
        logger.debug("VeyraCategoryLab.object_rows exit count=%d", len(result))
        return result

    def morphism_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready morphism closure rows."""
        logger.debug("VeyraCategoryLab.morphism_rows entry")
        result = [{"morphism": row.morphism, "source": row.source, "target": row.target, "graph": [_display(pair) for pair in row.graph], "status": row.status, "obstruction": row.obstruction} for row in category_closure_rows()]
        logger.debug("VeyraCategoryLab.morphism_rows exit count=%d", len(result))
        return result

    def invariant_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready invariant/counterexample rows."""
        logger.debug("VeyraCategoryLab.invariant_rows entry")
        result = [{"name": row.name, "morphism": row.morphism, "before": _display(row.before), "after": _display(row.after), "status": row.status, "obstruction": row.obstruction} for row in category_invariant_rows()]
        logger.debug("VeyraCategoryLab.invariant_rows exit count=%d", len(result))
        return result

    def universal_rows(self) -> list[dict[str, object]]:
        """Return bounded universal-shadow rows."""
        logger.debug("VeyraCategoryLab.universal_rows entry")
        result = [{"name": row.name, "status": row.status, "witness": [_display(pair) for pair in row.witness], "obstruction": row.obstruction} for row in category_universal_shadow_rows()]
        logger.debug("VeyraCategoryLab.universal_rows exit count=%d", len(result))
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return X3 acceptance checklist."""
        logger.debug("VeyraCategoryLab.checklist entry")
        result = category_like_checklist()
        logger.debug("VeyraCategoryLab.checklist exit count=%d", len(result))
        return result

    def summary(self) -> dict[str, int]:
        """Return compact category-like lab summary."""
        logger.debug("VeyraCategoryLab.summary entry")
        result = category_like_summary()
        logger.debug("VeyraCategoryLab.summary exit result=%r", result)
        return result


def build_category_like_notebook() -> VeyraNotebook:
    """Build notebook artifact for category-like translation smoke checks."""
    logger.debug("build_category_like_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Category-Like Translation Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraCategoryLab\nlab = VeyraCategoryLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['objects'] == 4\nassert summary['blocked'] == 1"),
        VeyraNotebookCell("code", "assert len(lab.morphism_rows()) == 4\nassert lab.universal_rows()[-1]['status'] == 'blocked'"),
        VeyraNotebookCell("markdown", "Objects are finite observer clouds; morphisms are transformer-backed rows; universal claims stay bounded shadows."),
    )
    result = VeyraNotebook("Category-Like Translation Lab", cells)
    logger.debug("build_category_like_notebook exit summary=%r", result.summary())
    return result


def category_like_lab_summary() -> dict[str, int]:
    """Return default category-like lab summary."""
    logger.debug("category_like_lab_summary entry")
    result = VeyraCategoryLab().summary()
    logger.debug("category_like_lab_summary exit result=%r", result)
    return result

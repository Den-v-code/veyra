"""Sage-facing facade for native Veyra number-theory certificates."""

from __future__ import annotations

import logging

from src.core.compression import CompressionWeights
from src.core.modes import Mode
from src.core.native_number import cycle_divisibility_row, native_number_theory_checklist, prime_obstruction_rows, rank_factor_comparison
from src.core.native_number_theorems import native_fermat_obstruction_rows, native_fermat_phase_rows

from .notebooks import VeyraNotebook, VeyraNotebookCell

logger = logging.getLogger(__name__)


class VeyraNumberTheoryLab:
    """Sage-facing reader for Sprint X2 native number-theory rows."""

    def divisibility_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready cycle-echo divisibility examples."""
        logger.debug("VeyraNumberTheoryLab.divisibility_rows entry")
        whole = Mode.from_word("abab")
        rows = (cycle_divisibility_row(Mode.from_word("ba"), whole), cycle_divisibility_row(Mode.from_word("aba"), whole))
        result = [{"part": r.part.word, "whole": r.whole.word, "exponent": r.exponent, "lift_word": r.lift_word, "status": r.status, "obstruction": r.obstruction} for r in rows]
        logger.debug("VeyraNumberTheoryLab.divisibility_rows exit count=%d", len(result))
        return result

    def prime_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready resonance-prime obstruction rows."""
        logger.debug("VeyraNumberTheoryLab.prime_rows entry")
        rows = prime_obstruction_rows([Mode.from_word("ab"), Mode.from_word("aa"), Mode.from_word("a")])
        result = [{"mode": r.mode.word, "numeric_prime": r.profile.numeric_prime, "cyclic_primitive": r.profile.cyclic_primitive, "resonance_prime": r.profile.ordered_resonance_prime, "status": r.status, "obstruction": r.obstruction} for r in rows]
        logger.debug("VeyraNumberTheoryLab.prime_rows exit count=%d", len(result))
        return result

    def rank_factor_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready spectrum/compression/factor-lift rows."""
        logger.debug("VeyraNumberTheoryLab.rank_factor_rows entry")
        rows = rank_factor_comparison(Mode.from_word("abab"), [Mode.from_word("ab"), Mode.from_word("ba"), Mode.from_word("aa")], 0, CompressionWeights(defect_weight=1.0))
        result = [{"part": r.part.word, "spectrum_rank": r.spectrum_rank, "compression_rank": r.compression_rank, "factor_status": r.factor_status, "lift_word": r.lift_word, "obstruction": r.obstruction} for r in rows]
        logger.debug("VeyraNumberTheoryLab.rank_factor_rows exit count=%d", len(result))
        return result

    def fermat_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready finite Fermat phase rows plus blocked obstructions."""
        logger.debug("VeyraNumberTheoryLab.fermat_rows entry")
        rows = native_fermat_phase_rows() + native_fermat_obstruction_rows()
        result = [row.as_dict() for row in rows]
        logger.debug("VeyraNumberTheoryLab.fermat_rows exit count=%d", len(result))
        return result

    def checklist(self) -> tuple[str, ...]:
        """Return X2 acceptance checklist."""
        logger.debug("VeyraNumberTheoryLab.checklist entry")
        result = native_number_theory_checklist()
        logger.debug("VeyraNumberTheoryLab.checklist exit count=%d", len(result))
        return result

    def summary(self) -> dict[str, int]:
        """Return compact native number-theory lab summary."""
        logger.debug("VeyraNumberTheoryLab.summary entry")
        divs = self.divisibility_rows(); primes = self.prime_rows(); ranks = self.rank_factor_rows(); fermat = self.fermat_rows()
        result = {"divisibility": len(divs), "blocked": sum(r["status"] == "blocked" for r in divs), "prime_rows": len(primes), "rank_rows": len(ranks), "factor_hits": sum(r["factor_status"] == "divides" for r in ranks), "fermat_rows": len(fermat), "fermat_derived": sum(r["status"] == "derived" for r in fermat), "fermat_units": sum(len(r["unit_lengths"]) for r in fermat), "checklist": len(self.checklist())}
        logger.debug("VeyraNumberTheoryLab.summary exit result=%r", result)
        return result


def build_number_theory_notebook() -> VeyraNotebook:
    """Build notebook artifact for native number-theory smoke checks."""
    logger.debug("build_number_theory_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Native Number-Theory Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraNumberTheoryLab\nlab = VeyraNumberTheoryLab()"),
        VeyraNotebookCell("code", "summary = lab.summary()\nassert summary['factor_hits'] == 2\nassert summary['blocked'] == 1\nassert summary['fermat_derived'] == 4"),
        VeyraNotebookCell("code", "assert len(lab.prime_rows()) == 3\nassert len(lab.rank_factor_rows()) == 3\nassert len(lab.fermat_rows()) == 7\nassert len(lab.checklist()) == 4"),
        VeyraNotebookCell("markdown", "Native number theory is exposed as cycle divisibility, prime obstruction, rank/factor rows, and finite prime-period Fermat phase rows."),
    )
    result = VeyraNotebook("Native Number-Theory Lab", cells)
    logger.debug("build_number_theory_notebook exit summary=%r", result.summary())
    return result


def number_theory_lab_summary() -> dict[str, int]:
    """Return default native number-theory lab summary."""
    logger.debug("number_theory_lab_summary entry")
    result = VeyraNumberTheoryLab().summary()
    logger.debug("number_theory_lab_summary exit result=%r", result)
    return result

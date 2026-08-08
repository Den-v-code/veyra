"""Sage-facing facade for Veyra proof-discipline coverage."""
from __future__ import annotations
import logging
from src.core.proof_discipline import primitive_model_notes, proof_discipline_checklist, proof_discipline_summary, proof_rule_coverage, semantic_domain_coverage, stable_formal_export_rows
from .notebooks import VeyraNotebook, VeyraNotebookCell
logger = logging.getLogger(__name__)
class VeyraProofDisciplineLab:
    """Sage-facing reader for rule/span/domain/model/export discipline."""
    def rule_coverage_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready rule coverage rows."""
        logger.debug("VeyraProofDisciplineLab.rule_coverage_rows entry")
        result = [row.__dict__.copy() for row in proof_rule_coverage()]
        logger.debug("VeyraProofDisciplineLab.rule_coverage_rows exit count=%d", len(result))
        return result
    def semantic_domain_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready semantic domain rows."""
        logger.debug("VeyraProofDisciplineLab.semantic_domain_rows entry")
        result = [row.__dict__.copy() for row in semantic_domain_coverage()]
        logger.debug("VeyraProofDisciplineLab.semantic_domain_rows exit count=%d", len(result))
        return result
    def primitive_model_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready primitive model notes."""
        logger.debug("VeyraProofDisciplineLab.primitive_model_rows entry")
        result = [row.__dict__.copy() for row in primitive_model_notes()]
        logger.debug("VeyraProofDisciplineLab.primitive_model_rows exit count=%d", len(result))
        return result
    def stable_export_rows(self) -> list[dict[str, object]]:
        """Return JSON-ready stable-card export gate rows."""
        logger.debug("VeyraProofDisciplineLab.stable_export_rows entry")
        result = [row.__dict__.copy() for row in stable_formal_export_rows()]
        logger.debug("VeyraProofDisciplineLab.stable_export_rows exit count=%d", len(result))
        return result
    def checklist(self) -> tuple[str, ...]:
        """Return proof-discipline checklist."""
        logger.debug("VeyraProofDisciplineLab.checklist entry")
        result = proof_discipline_checklist()
        logger.debug("VeyraProofDisciplineLab.checklist exit count=%d", len(result))
        return result
    def summary(self) -> dict[str, int]:
        """Return proof-discipline summary."""
        logger.debug("VeyraProofDisciplineLab.summary entry")
        result = proof_discipline_summary()
        logger.debug("VeyraProofDisciplineLab.summary exit result=%r", result)
        return result

def build_proof_discipline_notebook() -> VeyraNotebook:
    """Build notebook artifact for proof-discipline smoke checks."""
    logger.debug("build_proof_discipline_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Proof Discipline Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraProofDisciplineLab\nlab = VeyraProofDisciplineLab()"),
        VeyraNotebookCell("code", "assert lab.summary()['rules'] == 7\nassert lab.summary()['exports'] == 19"),
        VeyraNotebookCell("code", "assert len(lab.semantic_domain_rows()) == 7\nassert all(r['certificate'] == 'declared-shadow' for r in lab.semantic_domain_rows())\nassert len(lab.primitive_model_rows()) == 10"),
        VeyraNotebookCell("markdown", "Rule coverage, semantic shadows, primitive notes, and stable exports are visible."),
    )
    result = VeyraNotebook("Proof Discipline Lab", cells)
    logger.debug("build_proof_discipline_notebook exit summary=%r", result.summary())
    return result

def proof_discipline_lab_summary() -> dict[str, int]:
    """Return default proof-discipline lab summary."""
    logger.debug("proof_discipline_lab_summary entry")
    result = VeyraProofDisciplineLab().summary()
    logger.debug("proof_discipline_lab_summary exit result=%r", result)
    return result

"""Sage-facing wrapper for the Veyra Core Language stack."""
from __future__ import annotations
from dataclasses import dataclass
import logging
from src.core.language import interpret_veyra
from src.core.language_coverage import language_coverage_report
from src.core.language_span_coverage import span_diagnostic_coverage_report
from src.core.language_fuzz import generated_language_mutation_report, language_mutation_report, property_language_fuzz_report
from src.core.language_proof import proof_summary, trace_veyra_proof
from .notebooks import VeyraNotebook, VeyraNotebookCell
logger = logging.getLogger(__name__)
@dataclass(frozen=True)
class VeyraLanguageResult:
    """JSON-ready Core Language interpretation row."""
    source: str
    normal: str
    status: str
    kind: str
    domain: str
    obstruction: str
    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready result mapping."""
        logger.debug("VeyraLanguageResult.as_dict entry source=%s", self.source)
        result = {"source": self.source, "normal": self.normal, "status": self.status, "kind": self.kind, "domain": self.domain, "obstruction": self.obstruction}
        logger.debug("VeyraLanguageResult.as_dict exit result=%r", result)
        return result
@dataclass(frozen=True)
class VeyraLanguageTraceRow:
    """JSON-ready proof-trace summary row."""
    source: str
    parse_ok: bool
    final_status: str
    steps: int
    ready: int
    blocked: int
    unknown: int
    first_rule: str
    last_rule: str
    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready trace row."""
        logger.debug("VeyraLanguageTraceRow.as_dict entry source=%s", self.source)
        result = self.__dict__.copy()
        logger.debug("VeyraLanguageTraceRow.as_dict exit result=%r", result)
        return result
class VeyraLanguageLab:
    """Sage-facing facade over Core Language interpreter/proof/fuzz layers."""
    def __init__(self, domain: str = "logic") -> None:
        """Create lab facade for a default semantic domain."""
        logger.debug("VeyraLanguageLab.__init__ entry domain=%s", domain)
        self.domain = domain
        logger.debug("VeyraLanguageLab.__init__ exit")
    def interpret(self, source: str, domain: str | None = None) -> VeyraLanguageResult:
        """Interpret a Core Language source string."""
        logger.debug("VeyraLanguageLab.interpret entry source=%s domain=%s", source, domain)
        used_domain = domain or self.domain
        item = interpret_veyra(source, used_domain)
        kind = "none" if item.check.kind is None else item.check.kind.value
        result = VeyraLanguageResult(source, item.normal, item.check.status, kind, used_domain, item.check.obstruction)
        logger.debug("VeyraLanguageLab.interpret exit result=%r", result)
        return result
    def trace(self, source: str) -> VeyraLanguageTraceRow:
        """Return compact proof-trace row for source."""
        logger.debug("VeyraLanguageLab.trace entry source=%s", source)
        trace = trace_veyra_proof(source)
        summary = proof_summary(trace)
        first = trace.steps[0].rule if trace.steps else "none"
        last = trace.steps[-1].rule if trace.steps else "none"
        result = VeyraLanguageTraceRow(source, trace.parse_ok, summary.final_status, summary.steps, summary.ready, summary.blocked, summary.unknown, first, last)
        logger.debug("VeyraLanguageLab.trace exit result=%r", result)
        return result
    def mutation_summary(self) -> dict[str, int]:
        """Return deterministic mutation-pressure summary."""
        logger.debug("VeyraLanguageLab.mutation_summary entry")
        report = language_mutation_report()
        result = report.__dict__.copy()
        logger.debug("VeyraLanguageLab.mutation_summary exit result=%r", result)
        return result
    def generated_family_summary(self) -> dict[str, int]:
        """Return generated mutation-family summary."""
        logger.debug("VeyraLanguageLab.generated_family_summary entry")
        report = generated_language_mutation_report()
        result = report.__dict__.copy()
        logger.debug("VeyraLanguageLab.generated_family_summary exit result=%r", result)
        return result
    def property_fuzz_summary(self) -> dict[str, int]:
        """Return deterministic property-fuzz and shrinker summary."""
        logger.debug("VeyraLanguageLab.property_fuzz_summary entry")
        report = property_language_fuzz_report()
        result = report.__dict__.copy()
        logger.debug("VeyraLanguageLab.property_fuzz_summary exit result=%r", result)
        return result
    def coverage_summary(self) -> dict[str, int]:
        """Return language mutation coverage-matrix summary."""
        logger.debug("VeyraLanguageLab.coverage_summary entry")
        report = language_coverage_report()
        result = report.__dict__.copy()
        logger.debug("VeyraLanguageLab.coverage_summary exit result=%r", result)
        return result
    def span_diagnostic_summary(self) -> dict[str, int]:
        """Return source-span diagnostic coverage summary."""
        logger.debug("VeyraLanguageLab.span_diagnostic_summary entry")
        report = span_diagnostic_coverage_report()
        result = report.__dict__.copy()
        logger.debug("VeyraLanguageLab.span_diagnostic_summary exit result=%r", result)
        return result
    def summary(self) -> dict[str, object]:
        """Return compact lab capability summary."""
        logger.debug("VeyraLanguageLab.summary entry")
        ready = self.interpret("echo(nod:a,nod:b,observer:kind)")
        blocked = self.interpret("echo(nod:a,nod:b,observer:trace)")
        mutations = self.mutation_summary()
        families = self.generated_family_summary()
        fuzz = self.property_fuzz_summary()
        coverage = self.coverage_summary()
        span_diag = self.span_diagnostic_summary()
        result = {"domain": self.domain, "ready_status": ready.status, "blocked_status": blocked.status, "mutation_cases": mutations["cases"], "mutation_unexpected": mutations["unexpected"], "family_cases": families["cases"], "family_unexpected": families["unexpected"], "property_cases": fuzz["cases"], "property_unexpected": fuzz["unexpected"], "property_shrunk": fuzz["shrunk"], "coverage_cases": coverage["cases"], "coverage_missed": coverage["missed"], "span_diag_cases": span_diag["cases"], "span_diag_missed": span_diag["missed"]}
        logger.debug("VeyraLanguageLab.summary exit result=%r", result)
        return result
def build_language_lab_notebook() -> VeyraNotebook:
    """Build notebook artifact for Core Language wrapper smoke."""
    logger.debug("build_language_lab_notebook entry")
    cells = (
        VeyraNotebookCell("markdown", "# Veyra Core Language Lab"),
        VeyraNotebookCell("code", "from veyra_sage.all import VeyraLanguageLab\nlab = VeyraLanguageLab()"),
        VeyraNotebookCell("code", "assert lab.interpret('echo(nod:a,nod:b,observer:kind)').status == 'ready'"),
        VeyraNotebookCell("code", "assert lab.trace('echo(nod:a,nod:b,observer:trace)').blocked >= 1"),
        VeyraNotebookCell("code", "assert lab.mutation_summary()['unexpected'] == 0\nassert lab.generated_family_summary()['unexpected'] == 0\nassert lab.property_fuzz_summary()['shrunk'] == 24\nassert lab.coverage_summary()['missed'] == 0\nassert lab.span_diagnostic_summary()['missed'] == 0"),
        VeyraNotebookCell("markdown", "Core Language wrapper exposes interpreter, proof traces, and mutation pressure."),
    )
    result = VeyraNotebook("Core Language Lab", cells)
    logger.debug("build_language_lab_notebook exit summary=%r", result.summary())
    return result
def language_lab_summary() -> dict[str, object]:
    """Return default language-lab summary."""
    logger.debug("language_lab_summary entry")
    result = VeyraLanguageLab().summary()
    logger.debug("language_lab_summary exit result=%r", result)
    return result

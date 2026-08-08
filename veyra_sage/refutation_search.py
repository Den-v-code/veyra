"""Parameterized refutation search for Veyra Sage theorem-card labs."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
import logging

from src.core.algebra_analysis_cards import continuity_card, polynomial_identity_card
from src.core.change import sampled_continuity
from src.core.cyclic_probability_stats import FiniteDistribution, WeightedOutcome
from src.core.depth_packs import independence_card
from src.core.geometry import event_from_ints
from src.core.geometry_theorems import TheoremCard, pythagorean_card
from src.core.polynomial import polynomial_from_ints
from src.core.ratio import ratio_from_ints, ratio_shadow

from .notebooks import VeyraNotebook, VeyraNotebookCell
from .proofs import VeyraProofCheck, VeyraProofGraph

logger = logging.getLogger(__name__)
Builder = Callable[[], object]


@dataclass(frozen=True)
class VeyraSearchHit:
    """One blocked candidate discovered by parameterized search."""

    candidate_id: str
    theorem_id: str
    domain: str
    parameters: tuple[tuple[str, str], ...]
    relation: str
    obstruction: str

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraSearchHit({self.candidate_id}:{self.obstruction})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready search hit."""
        logger.debug("VeyraSearchHit.as_dict entry candidate=%s", self.candidate_id)
        result = {"candidate_id": self.candidate_id, "theorem_id": self.theorem_id, "domain": self.domain, "parameters": dict(self.parameters), "relation": self.relation, "obstruction": self.obstruction}
        logger.debug("VeyraSearchHit.as_dict exit obstruction=%s", self.obstruction)
        return result


@dataclass(frozen=True)
class VeyraSearchReport:
    """Refutation search report for one domain."""

    domain: str
    tried: int
    blocked: tuple[VeyraSearchHit, ...]

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraSearchReport({self.domain}:tried={self.tried}, blocked={len(self.blocked)})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_dict(self) -> dict[str, object]:
        """Return JSON-ready report."""
        logger.debug("VeyraSearchReport.as_dict entry domain=%s", self.domain)
        result = {"domain": self.domain, "tried": self.tried, "blocked": [item.as_dict() for item in self.blocked]}
        logger.debug("VeyraSearchReport.as_dict exit blocked=%d", len(self.blocked))
        return result


@dataclass(frozen=True)
class _Candidate:
    candidate_id: str
    theorem_id: str
    domain: str
    parameters: tuple[tuple[str, str], ...]
    builder: Builder


def _uniform_distribution() -> FiniteDistribution:
    """Return four-outcome uniform distribution for probability searches."""
    logger.debug("_uniform_distribution entry")
    result = FiniteDistribution(tuple(WeightedOutcome(name, 1, ratio_from_ints(0)) for name in ("00", "01", "10", "11")))
    logger.debug("_uniform_distribution exit")
    return result


def _jump_card(threshold: int = 0):
    """Return continuity card for a threshold jump rule."""
    logger.debug("_jump_card entry threshold=%d", threshold)

    def jump(x):
        return ratio_from_ints(0) if ratio_shadow(x) < threshold else ratio_from_ints(1)

    result = continuity_card(sampled_continuity(jump, ratio_from_ints(0), ratio_from_ints(1), ratio_from_ints(1, 2), 2))
    logger.debug("_jump_card exit obstruction=%s", result.obstruction)
    return result


def _candidate_space() -> tuple[_Candidate, ...]:
    """Return finite parameterized candidate space with good and bad cases."""
    logger.debug("_candidate_space entry")
    dist = _uniform_distribution
    result = (
        _Candidate("geo-right", "pythagorean-separation", "geometry", (("point", "0,4"),), lambda: pythagorean_card(event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((0, 4)))),
        _Candidate("geo-non-right", "pythagorean-separation", "geometry", (("point", "1,1"),), lambda: pythagorean_card(event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((1, 1)))),
        _Candidate("poly-same", "polynomial-identity", "algebra", (("left", "1"), ("right", "1")), lambda: polynomial_identity_card(polynomial_from_ints([1]), polynomial_from_ints([1]))),
        _Candidate("poly-mismatch", "polynomial-identity", "algebra", (("left", "1"), ("right", "2")), lambda: polynomial_identity_card(polynomial_from_ints([1]), polynomial_from_ints([2]))),
        _Candidate("jump-threshold-0", "sampled-continuity", "analysis", (("threshold", "0"),), lambda: _jump_card(0)),
        _Candidate("independent-events", "probability-independence", "probability", (("left", "10,11"), ("right", "01,11")), lambda: independence_card(dist(), frozenset({"10", "11"}), frozenset({"01", "11"}))),
        _Candidate("dependent-events", "probability-independence", "probability", (("left", "00"), ("right", "00,01")), lambda: independence_card(dist(), frozenset({"00"}), frozenset({"00", "01"}))),
        _Candidate("binomial-mutant", "binomial-symmetry", "combinatorics", (("mutation", "count"),), lambda: TheoremCard("binomial-symmetry", "exact", "broken", "count-mismatch", ())),
        _Candidate("chord-mutant", "chord-symmetry", "trig", (("mutation", "chord"),), lambda: TheoremCard("chord-symmetry", "exact", "broken", "chord-mismatch", ())),
        _Candidate("variance-mutant", "variance-shift", "statistics", (("mutation", "variance"),), lambda: TheoremCard("variance-shift", "exact", "broken", "variance-gap", ())),
    )
    logger.debug("_candidate_space exit count=%d", len(result))
    return result


def run_search_candidate(candidate_id: str) -> VeyraProofCheck:
    """Run one search candidate by ID."""
    logger.debug("run_search_candidate entry candidate=%s", candidate_id)
    table = {item.candidate_id: item for item in _candidate_space()}
    if candidate_id not in table:
        logger.error("run_search_candidate unknown=%s", candidate_id)
        raise KeyError(candidate_id)
    item = table[candidate_id]
    result = VeyraProofGraph().proof_object(item.theorem_id).check(item.builder())
    logger.debug("run_search_candidate exit status=%s obstruction=%s", result.status, result.obstruction)
    return result


def refutation_search(domain: str | None = None) -> tuple[VeyraSearchReport, ...]:
    """Run parameterized search and group blocked candidates by domain."""
    logger.debug("refutation_search entry domain=%s", domain)
    candidates = tuple(item for item in _candidate_space() if domain is None or item.domain == domain)
    if domain is not None and not candidates:
        logger.error("refutation_search unknown domain=%s", domain)
        raise KeyError(domain)
    reports = []
    for item_domain in sorted({item.domain for item in candidates}):
        subset = tuple(item for item in candidates if item.domain == item_domain)
        hits = []
        for item in subset:
            check = run_search_candidate(item.candidate_id)
            if check.status == "blocked":
                hits.append(VeyraSearchHit(item.candidate_id, item.theorem_id, item.domain, item.parameters, check.relation, check.obstruction))
        reports.append(VeyraSearchReport(item_domain, len(subset), tuple(hits)))
    result = tuple(reports)
    logger.debug("refutation_search exit reports=%d", len(result))
    return result


def refutation_search_summary() -> dict[str, int]:
    """Return compact search summary."""
    logger.debug("refutation_search_summary entry")
    reports = refutation_search()
    result = {"domains": len(reports), "tried": sum(item.tried for item in reports), "blocked": sum(len(item.blocked) for item in reports)}
    logger.debug("refutation_search_summary exit result=%r", result)
    return result


def build_refutation_search_notebook(domain: str) -> VeyraNotebook:
    """Build notebook that runs parameterized refutation search for one domain."""
    logger.debug("build_refutation_search_notebook entry domain=%s", domain)
    report = refutation_search(domain)[0]
    ids = tuple(item.candidate_id for item in report.blocked)
    catalogue = "\n".join(f"- `{item.candidate_id}` → `{item.obstruction}`" for item in report.blocked)
    cells = (
        VeyraNotebookCell("markdown", f"# Veyra {domain} refutation search\n\nParameterized search for blocked theorem-card candidates."),
        VeyraNotebookCell("markdown", f"## Search snapshot\n\n- domain: `{domain}`\n- tried: {report.tried}\n- blocked: {len(report.blocked)}"),
        VeyraNotebookCell("code", "from veyra_sage.all import refutation_search, run_search_candidate\nreports = refutation_search(" + repr(domain) + ")"),
        VeyraNotebookCell("code", "[item.as_dict() for item in reports]"),
        VeyraNotebookCell("markdown", "## Blocked candidates\n\n" + catalogue),
        VeyraNotebookCell("code", "ids = " + repr(ids) + "\n[run_search_candidate(item).as_dict() for item in ids]"),
    )
    result = VeyraNotebook(f"Veyra {domain} refutation search", cells)
    logger.debug("build_refutation_search_notebook exit cells=%d", len(cells))
    return result


def build_all_refutation_search_notebooks() -> dict[str, VeyraNotebook]:
    """Build refutation-search notebooks for every searched domain."""
    logger.debug("build_all_refutation_search_notebooks entry")
    result = {report.domain: build_refutation_search_notebook(report.domain) for report in refutation_search()}
    logger.debug("build_all_refutation_search_notebooks exit count=%d", len(result))
    return result

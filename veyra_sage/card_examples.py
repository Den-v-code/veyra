"""Executable theorem-card examples for Veyra Sage notebooks."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from collections.abc import Callable

from src.core.algebra_analysis_cards import area_additivity_card, continuity_card, drift_stability_card, linear_equation_card, polynomial_evaluation_card, polynomial_identity_card
from src.core.change import riemann_area, sampled_continuity, symmetric_difference_quotient
from src.core.cyclic_probability_stats import CyclicPhase, FiniteDistribution, SampleEcho, WeightedOutcome, chord_symmetry_card, mean_balance_card, phase_period_card, probability_complement_card
from src.core.depth_packs import binomial_symmetry_card, independence_card, probability_union_card, variance_shift_card
from src.core.equation import LinearEquation, constant, variable
from src.core.geometry import TremorCorridor, event_from_ints
from src.core.geometry_theorems import identity_relabel, line_shell_intersections, pythagorean_card, relabel_composition_card, sas_card, sss_card
from src.core.polynomial import add_polynomials, polynomial_from_ints
from src.core.ratio import ratio_from_ints
from src.core.transformer import affine_transformer, apply_transformer, transformer_from_polynomial

from .notebooks import VeyraNotebook, VeyraNotebookCell
from .proofs import VeyraProofCheck, VeyraProofGraph

logger = logging.getLogger(__name__)
Builder = Callable[[], object]


@dataclass(frozen=True)
class VeyraCardExample:
    """Executable theorem-card example descriptor."""

    theorem_id: str
    domain: str
    title: str
    expected_status: str
    expected_obstruction: str
    source: str

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraCardExample({self.theorem_id}:{self.expected_status})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready descriptor."""
        logger.debug("VeyraCardExample.as_dict entry theorem=%s", self.theorem_id)
        result = {"theorem_id": self.theorem_id, "domain": self.domain, "title": self.title, "expected_status": self.expected_status, "expected_obstruction": self.expected_obstruction, "source": self.source}
        logger.debug("VeyraCardExample.as_dict exit status=%s", self.expected_status)
        return result


def _triangle() -> tuple[object, object, object]:
    """Return standard 3-4-5 right triangle events."""
    logger.debug("_triangle entry")
    result = (event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((0, 4)))
    logger.debug("_triangle exit")
    return result


def _distribution() -> FiniteDistribution:
    """Return four-outcome uniform distribution."""
    logger.debug("_distribution entry")
    result = FiniteDistribution(tuple(WeightedOutcome(name, 1, ratio_from_ints(0)) for name in ("00", "01", "10", "11")))
    logger.debug("_distribution exit")
    return result


def _sample() -> SampleEcho:
    """Return stable sample for statistics examples."""
    logger.debug("_sample entry")
    result = SampleEcho((ratio_from_ints(1), ratio_from_ints(3), ratio_from_ints(5)))
    logger.debug("_sample exit")
    return result


def _continuity_example():
    rule = affine_transformer(ratio_from_ints(2), ratio_from_ints(0), "double")
    return continuity_card(sampled_continuity(lambda x: apply_transformer(rule, x), ratio_from_ints(0), ratio_from_ints(1, 10), ratio_from_ints(1), 2))


def _drift_example():
    square = transformer_from_polynomial("square", polynomial_from_ints([0, 0, 1]))
    rule = lambda x: apply_transformer(square, x)
    quotients = tuple(symmetric_difference_quotient(rule, ratio_from_ints(3), ratio_from_ints(step)) for step in (1, 2, 3))
    return drift_stability_card(quotients)


def _area_example():
    identity = affine_transformer(ratio_from_ints(1), ratio_from_ints(0), "id")
    rule = lambda x: apply_transformer(identity, x)
    left = riemann_area(rule, ratio_from_ints(0), ratio_from_ints(1), 4, "mid")
    right = riemann_area(rule, ratio_from_ints(1), ratio_from_ints(2), 4, "mid")
    whole = riemann_area(rule, ratio_from_ints(0), ratio_from_ints(2), 8, "mid")
    return area_additivity_card(left, right, whole)


def _builders() -> dict[str, Builder]:
    """Return theorem-card example builders."""
    logger.debug("_builders entry")
    left = frozenset({"10", "11"})
    right = frozenset({"01", "11"})
    result: dict[str, Builder] = {
        "pythagorean-separation": lambda: pythagorean_card(*_triangle()),
        "sss-triangle": lambda: sss_card(_triangle(), _triangle()),
        "sas-triangle": lambda: sas_card(_triangle(), _triangle()),
        "line-shell-intersection": lambda: line_shell_intersections(TremorCorridor(event_from_ints((5, -1)), event_from_ints((5, 1)), "tangent"), event_from_ints((0, 0)), ratio_from_ints(25)),
        "plane-relabel-composition": lambda: relabel_composition_card(identity_relabel(), identity_relabel(), event_from_ints((2, 3))),
        "linear-equation-solution": lambda: linear_equation_card(LinearEquation(variable(2, 1), constant(7))),
        "polynomial-identity": lambda: polynomial_identity_card(add_polynomials(polynomial_from_ints([1, 2]), polynomial_from_ints([3, -2])), polynomial_from_ints([4])),
        "polynomial-evaluation": lambda: polynomial_evaluation_card(polynomial_from_ints([1, 0, 1]), ratio_from_ints(3), ratio_from_ints(10)),
        "sampled-continuity": _continuity_example,
        "drift-stability": _drift_example,
        "area-additivity": _area_example,
        "cyclic-period": lambda: phase_period_card(CyclicPhase(1, 12)),
        "chord-symmetry": lambda: chord_symmetry_card(CyclicPhase(1, 12), CyclicPhase(10, 12)),
        "probability-complement": lambda: probability_complement_card(_distribution(), frozenset({"00"})),
        "mean-balance": lambda: mean_balance_card(_sample()),
        "binomial-symmetry": lambda: binomial_symmetry_card(6, 2),
        "probability-union": lambda: probability_union_card(_distribution(), left, right),
        "probability-independence": lambda: independence_card(_distribution(), left, right),
        "variance-shift": lambda: variance_shift_card(_sample(), ratio_from_ints(10)),
    }
    logger.debug("_builders exit count=%d", len(result))
    return result


def run_card_example(theorem_id: str) -> VeyraProofCheck:
    """Run one executable card example and return proof check."""
    logger.debug("run_card_example entry theorem=%s", theorem_id)
    builders = _builders()
    if theorem_id not in builders:
        logger.error("run_card_example unknown theorem=%s", theorem_id)
        raise KeyError(theorem_id)
    graph = VeyraProofGraph()
    result = graph.proof_object(theorem_id).check(builders[theorem_id]())
    logger.debug("run_card_example exit status=%s obstruction=%s", result.status, result.obstruction)
    return result


def card_examples(domain: str | None = None) -> tuple[VeyraCardExample, ...]:
    """Return executable card descriptors, optionally filtered by domain."""
    logger.debug("card_examples entry domain=%s", domain)
    graph = VeyraProofGraph()
    builders = _builders()
    rows = []
    for obj in graph.proof_objects(domain):
        if obj.theorem_id not in builders:
            continue
        check = run_card_example(obj.theorem_id)
        source = f"from veyra_sage.all import run_card_example\nrun_card_example({obj.theorem_id!r}).as_dict()"
        rows.append(VeyraCardExample(obj.theorem_id, obj.hook.split(".", 1)[0], obj.title, check.status, check.obstruction, source))
    result = tuple(rows)
    logger.debug("card_examples exit count=%d", len(result))
    return result


def card_example_summary() -> dict[str, int]:
    """Return compact executable-card coverage summary."""
    logger.debug("card_example_summary entry")
    rows = card_examples()
    result = {"examples": len(rows), "ready": sum(1 for row in rows if row.expected_status == "ready"), "domains": len({row.domain for row in rows})}
    logger.debug("card_example_summary exit result=%r", result)
    return result


def build_executable_card_notebook(domain: str) -> VeyraNotebook:
    """Build a domain notebook with executable theorem-card checks."""
    logger.debug("build_executable_card_notebook entry domain=%s", domain)
    rows = card_examples(domain)
    if not rows:
        logger.error("build_executable_card_notebook empty domain=%s", domain)
        raise KeyError(domain)
    ids = tuple(row.theorem_id for row in rows)
    catalogue = "\n".join(f"- `{row.theorem_id}` → `{row.expected_status}` / `{row.expected_obstruction}`" for row in rows)
    cells = (
        VeyraNotebookCell("markdown", f"# Veyra {domain} executable theorem-card lab\n\nGenerated card examples for `{domain}`."),
        VeyraNotebookCell("markdown", f"## Card snapshot\n\n- domain: `{domain}`\n- examples: {len(rows)}\n- ready: {sum(1 for row in rows if row.expected_status == 'ready')}"),
        VeyraNotebookCell("code", "from veyra_sage.all import run_card_example, card_examples\nids = " + repr(ids)),
        VeyraNotebookCell("code", "checks = [run_card_example(item).as_dict() for item in ids]\nchecks"),
        VeyraNotebookCell("markdown", "## Executable checks\n\n" + catalogue),
        VeyraNotebookCell("code", "assert all(item['status'] == 'ready' for item in checks)\n[(item['theorem_id'], item['relation']) for item in checks]"),
        VeyraNotebookCell("markdown", "## Source snippets\n\nEach row exposes a minimal reproducible source snippet."),
        VeyraNotebookCell("code", "[item.as_dict() for item in card_examples(" + repr(domain) + ")]"),
    )
    result = VeyraNotebook(f"Veyra {domain} executable theorem-card lab", cells)
    logger.debug("build_executable_card_notebook exit cells=%d", len(cells))
    return result


def build_all_executable_card_notebooks() -> dict[str, VeyraNotebook]:
    """Build executable theorem-card notebooks for every covered domain."""
    logger.debug("build_all_executable_card_notebooks entry")
    domains = tuple(sorted({row.domain for row in card_examples()}))
    result = {domain: build_executable_card_notebook(domain) for domain in domains}
    logger.debug("build_all_executable_card_notebooks exit count=%d", len(result))
    return result

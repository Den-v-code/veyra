"""Mutation/refutation examples for Veyra Sage theorem-card labs."""

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
class VeyraRefutationExample:
    """Descriptor for one intentional failing theorem-card example."""

    refutation_id: str
    theorem_id: str
    domain: str
    kind: str
    expected_obstruction: str
    source: str

    def _repr_(self) -> str:
        """Return Sage-style representation."""
        return f"VeyraRefutationExample({self.refutation_id})"

    def __repr__(self) -> str:
        """Return Python representation."""
        return self._repr_()

    def as_dict(self) -> dict[str, str]:
        """Return JSON-ready descriptor."""
        logger.debug("VeyraRefutationExample.as_dict entry refutation=%s", self.refutation_id)
        result = {"refutation_id": self.refutation_id, "theorem_id": self.theorem_id, "domain": self.domain, "kind": self.kind, "expected_obstruction": self.expected_obstruction, "source": self.source}
        logger.debug("VeyraRefutationExample.as_dict exit obstruction=%s", self.expected_obstruction)
        return result


def _dependent_distribution() -> FiniteDistribution:
    """Return distribution where selected events are not independent."""
    logger.debug("_dependent_distribution entry")
    result = FiniteDistribution(tuple(WeightedOutcome(name, 1, ratio_from_ints(0)) for name in ("00", "01", "10", "11")))
    logger.debug("_dependent_distribution exit")
    return result


def _jump_rule_card():
    """Return sampled-continuity card for a jump rule."""
    logger.debug("_jump_rule_card entry")

    def jump(x):
        return ratio_from_ints(0) if ratio_shadow(x) < 0 else ratio_from_ints(1)

    result = continuity_card(sampled_continuity(jump, ratio_from_ints(0), ratio_from_ints(1), ratio_from_ints(1, 2), 2))
    logger.debug("_jump_rule_card exit obstruction=%s", result.obstruction)
    return result


def _refutation_table() -> dict[str, tuple[str, str, str, str, Builder]]:
    """Return refutation metadata and card builders."""
    logger.debug("_refutation_table entry")
    result: dict[str, tuple[str, str, str, str, Builder]] = {
        "pythagorean-non-right": ("pythagorean-separation", "geometry", "counterexample", "non-right-apex", lambda: pythagorean_card(event_from_ints((0, 0)), event_from_ints((3, 0)), event_from_ints((1, 1)))),
        "polynomial-coeff-mismatch": ("polynomial-identity", "algebra", "counterexample", "coefficient-mismatch", lambda: polynomial_identity_card(polynomial_from_ints([1]), polynomial_from_ints([2]))),
        "continuity-jump": ("sampled-continuity", "analysis", "counterexample", "echo-jump", _jump_rule_card),
        "dependent-events": ("probability-independence", "probability", "counterexample", "product-gap", lambda: independence_card(_dependent_distribution(), frozenset({"00"}), frozenset({"00", "01"}))),
        "binomial-mutated-count": ("binomial-symmetry", "combinatorics", "mutation", "count-mismatch", lambda: TheoremCard("binomial-symmetry", "exact", "broken", "count-mismatch", ())),
        "chord-mutated-symmetry": ("chord-symmetry", "trig", "mutation", "chord-mismatch", lambda: TheoremCard("chord-symmetry", "exact", "broken", "chord-mismatch", ())),
        "variance-mutated-shift": ("variance-shift", "statistics", "mutation", "variance-gap", lambda: TheoremCard("variance-shift", "exact", "broken", "variance-gap", ())),
    }
    logger.debug("_refutation_table exit count=%d", len(result))
    return result


def run_refutation_example(refutation_id: str) -> VeyraProofCheck:
    """Run one intentional failing theorem-card example."""
    logger.debug("run_refutation_example entry refutation=%s", refutation_id)
    table = _refutation_table()
    if refutation_id not in table:
        logger.error("run_refutation_example unknown=%s", refutation_id)
        raise KeyError(refutation_id)
    theorem_id, _, _, _, builder = table[refutation_id]
    result = VeyraProofGraph().proof_object(theorem_id).check(builder())
    logger.debug("run_refutation_example exit status=%s obstruction=%s", result.status, result.obstruction)
    return result


def refutation_examples(domain: str | None = None) -> tuple[VeyraRefutationExample, ...]:
    """Return refutation descriptors, optionally filtered by domain."""
    logger.debug("refutation_examples entry domain=%s", domain)
    rows = []
    for refutation_id, (theorem_id, item_domain, kind, obstruction, _) in sorted(_refutation_table().items()):
        if domain is not None and item_domain != domain:
            continue
        source = f"from veyra_sage.all import run_refutation_example\nrun_refutation_example({refutation_id!r}).as_dict()"
        rows.append(VeyraRefutationExample(refutation_id, theorem_id, item_domain, kind, obstruction, source))
    result = tuple(rows)
    logger.debug("refutation_examples exit count=%d", len(result))
    return result


def refutation_summary() -> dict[str, int]:
    """Return compact refutation coverage summary."""
    logger.debug("refutation_summary entry")
    rows = refutation_examples()
    checks = tuple(run_refutation_example(row.refutation_id) for row in rows)
    result = {"examples": len(rows), "blocked": sum(1 for item in checks if item.status == "blocked"), "domains": len({row.domain for row in rows}), "mutations": sum(1 for row in rows if row.kind == "mutation")}
    logger.debug("refutation_summary exit result=%r", result)
    return result


def build_refutation_notebook(domain: str) -> VeyraNotebook:
    """Build a domain notebook with intentional failing card checks."""
    logger.debug("build_refutation_notebook entry domain=%s", domain)
    rows = refutation_examples(domain)
    if not rows:
        logger.error("build_refutation_notebook empty domain=%s", domain)
        raise KeyError(domain)
    ids = tuple(row.refutation_id for row in rows)
    catalogue = "\n".join(f"- `{row.refutation_id}` → `{row.theorem_id}` / `{row.expected_obstruction}`" for row in rows)
    cells = (
        VeyraNotebookCell("markdown", f"# Veyra {domain} refutation lab\n\nIntentional failing cards for `{domain}`."),
        VeyraNotebookCell("markdown", f"## Refutation snapshot\n\n- domain: `{domain}`\n- examples: {len(rows)}"),
        VeyraNotebookCell("code", "from veyra_sage.all import run_refutation_example, refutation_examples\nids = " + repr(ids)),
        VeyraNotebookCell("code", "checks = [run_refutation_example(item).as_dict() for item in ids]\nchecks"),
        VeyraNotebookCell("markdown", "## Expected blocked checks\n\n" + catalogue),
        VeyraNotebookCell("code", "assert all(item['status'] == 'blocked' for item in checks)\n[(item['theorem_id'], item['obstruction']) for item in checks]"),
        VeyraNotebookCell("markdown", "## Refutation sources\n\nEach descriptor exposes a minimal reproducible source snippet."),
        VeyraNotebookCell("code", "[item.as_dict() for item in refutation_examples(" + repr(domain) + ")]"),
    )
    result = VeyraNotebook(f"Veyra {domain} refutation lab", cells)
    logger.debug("build_refutation_notebook exit cells=%d", len(cells))
    return result


def build_all_refutation_notebooks() -> dict[str, VeyraNotebook]:
    """Build refutation notebooks for all covered domains."""
    logger.debug("build_all_refutation_notebooks entry")
    domains = tuple(sorted({row.domain for row in refutation_examples()}))
    result = {domain: build_refutation_notebook(domain) for domain in domains}
    logger.debug("build_all_refutation_notebooks exit count=%d", len(result))
    return result

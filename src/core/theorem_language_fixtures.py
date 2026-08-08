"""Default finite-obligation fixtures for the legacy theorem harness."""

from __future__ import annotations

import logging

from .theorem_language import (
    ProofObligation,
    TheoremEnvironment,
    check_theorem_statement,
    parse_theorem_statement,
)

logger = logging.getLogger(__name__)


def theorem_obligation_rows() -> tuple[ProofObligation, ...]:
    """Return default F2 obligation rows, including a blocked diagnostic."""
    logger.debug("theorem_obligation_rows entry")
    good = parse_theorem_statement(
        "theorem echo_kind_reflexive forall x:nod :: ready(echo($x,$x,observer:kind))"
    )
    bad = parse_theorem_statement(
        "theorem trace_echo_false forall x:nod,y:nod :: ready(echo($x,$y,observer:trace))"
    )
    environments = default_theorem_environments()
    result = (
        check_theorem_statement(good, environments[:2]).obligations
        + check_theorem_statement(bad, environments[2:]).obligations
    )
    logger.debug("theorem_obligation_rows exit count=%d", len(result))
    return result


def default_theorem_environments() -> tuple[TheoremEnvironment, ...]:
    """Return finite theorem-language fixtures."""
    logger.debug("default_theorem_environments entry")
    result = (
        TheoremEnvironment("nod-a", {"x": "nod:a", "y": "nod:a"}),
        TheoremEnvironment("nod-b", {"x": "nod:b", "y": "nod:b"}),
        TheoremEnvironment("trace-mismatch", {"x": "nod:a", "y": "nod:b"}),
    )
    logger.debug("default_theorem_environments exit count=%d", len(result))
    return result


def theorem_language_checklist() -> tuple[str, ...]:
    """Return F2 theorem-language capabilities."""
    logger.debug("theorem_language_checklist entry")
    result = (
        "theorem names",
        "forall quantifiers",
        "typed variables",
        "status propositions",
        "implication/equivalence parsing",
        "finite proof obligations",
        "blocked diagnostics",
    )
    logger.debug("theorem_language_checklist exit count=%d", len(result))
    return result

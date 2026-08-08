"""Structural validation for directly constructed legacy theorem objects."""

from __future__ import annotations

import logging
import re
from typing import Protocol

from .language import VeyraKind
from .theorem_language_substitution import template_variables

logger = logging.getLogger(__name__)
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")


class QuantifierLike(Protocol):
    name: str
    kind: VeyraKind


class PropositionLike(Protocol):
    expected_status: str
    template: str


def exact_statement_graph(
    statement: object,
    statement_type: type,
    quantifier_type: type,
    proposition_type: type,
) -> bool:
    """Accept only the immutable dataclass graph owned by the legacy harness."""
    logger.debug("exact_statement_graph entry type=%s", type(statement).__name__)
    result = (
        type(statement) is statement_type
        and type(statement.name) is str
        and type(statement.connective) is str
        and type(statement.quantifiers) is tuple
        and type(statement.assumptions) is tuple
        and type(statement.conclusions) is tuple
        and all(type(item) is quantifier_type for item in statement.quantifiers)
        and all(
            type(item.name) is str and type(item.kind) is VeyraKind
            for item in statement.quantifiers
        )
        and all(
            type(item) is proposition_type
            for item in statement.assumptions + statement.conclusions
        )
        and all(
            type(item.expected_status) is str and type(item.template) is str
            for item in statement.assumptions + statement.conclusions
        )
    )
    logger.debug("exact_statement_graph exit result=%s", result)
    return result


def statement_errors(
    name: object,
    quantifiers: tuple[QuantifierLike, ...],
    assumptions: tuple[PropositionLike, ...],
    conclusions: tuple[PropositionLike, ...],
    connective: object,
) -> tuple[str, ...]:
    """Return fail-closed structural errors for a legacy theorem statement."""
    logger.debug("statement_errors entry theorem=%r", name)
    errors: list[str] = []
    if not isinstance(name, str) or not _IDENTIFIER.fullmatch(name):
        errors.append("bad theorem name")
    names: list[str] = []
    for quantifier in quantifiers:
        if not isinstance(quantifier.name, str) or not _IDENTIFIER.fullmatch(quantifier.name):
            errors.append("bad quantifier name")
        elif quantifier.name in names:
            errors.append(f"duplicate quantifier {quantifier.name}")
        else:
            names.append(quantifier.name)
        if not isinstance(quantifier.kind, VeyraKind):
            errors.append(f"bad quantifier kind {quantifier.name}")
    if not conclusions:
        errors.append("no conclusions")
    if connective not in {"asserts", "implies", "iff"}:
        errors.append("bad connective")
    if connective == "asserts" and assumptions:
        errors.append("assertion cannot contain assumptions")
    if connective in {"implies", "iff"} and not assumptions:
        errors.append(f"{connective} requires assumptions")
    declared = frozenset(names)
    for proposition in assumptions + conclusions:
        if proposition.expected_status not in {"ready", "blocked", "unknown"}:
            errors.append("bad proposition status")
        if not isinstance(proposition.template, str) or not proposition.template.strip():
            errors.append("empty proposition template")
            continue
        try:
            variables = frozenset(template_variables(proposition.template))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        unknown = variables - declared
        if unknown:
            errors.append(f"undeclared theorem placeholder ${sorted(unknown)[0]}")
    result = tuple(dict.fromkeys(errors))
    logger.debug("statement_errors exit count=%d", len(result))
    return result

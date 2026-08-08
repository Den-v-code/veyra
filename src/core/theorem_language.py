"""Legacy finite-obligation Core Language v0.9 fixture harness."""

from __future__ import annotations
from dataclasses import dataclass
import logging
import re
from collections.abc import Iterable, Mapping
from .language import VeyraKind, expr_kind, infer_veyra, parse_veyra
from .theorem_language_substitution import substitute_template, template_variables
from .theorem_language_validation import exact_statement_graph, statement_errors

logger = logging.getLogger(__name__)
FINITE_OBLIGATION_EVIDENCE_CLASS = "finite-obligation"
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
@dataclass(frozen=True)
class TheoremQuantifier:
    """A quantified variable declaration."""

    name: str
    kind: VeyraKind
@dataclass(frozen=True)
class TheoremProposition:
    """A status predicate over a Veyra expression template."""

    expected_status: str
    template: str
@dataclass(frozen=True)
class TheoremStatement:
    """Parsed theorem object with quantifiers and a logical connective."""

    name: str
    quantifiers: tuple[TheoremQuantifier, ...]
    assumptions: tuple[TheoremProposition, ...]
    conclusions: tuple[TheoremProposition, ...]
    connective: str
@dataclass(frozen=True)
class TheoremEnvironment:
    """Finite witness assignment for quantified theorem variables."""

    name: str
    assignments: Mapping[str, str]


@dataclass(frozen=True)
class ProofObligation:
    """One checked obligation produced by a theorem statement."""

    theorem: str
    environment: str
    role: str
    source: str
    expected_status: str
    actual_status: str
    status: str
    obstruction: str = ""


@dataclass(frozen=True)
class TheoremCheck:
    """Aggregate result for finite theorem obligations."""

    theorem: str
    status: str
    obligations: tuple[ProofObligation, ...]
    blocked: tuple[str, ...]
    evidence_class: str = FINITE_OBLIGATION_EVIDENCE_CLASS

    def __post_init__(self) -> None:
        logger.debug("TheoremCheck.__post_init__ entry theorem=%s", self.theorem)
        if self.evidence_class != FINITE_OBLIGATION_EVIDENCE_CLASS:
            logger.error(
                "TheoremCheck.__post_init__ invalid evidence_class=%r",
                self.evidence_class,
            )
            raise ValueError("theorem check evidence class must be finite-obligation")
        logger.debug("TheoremCheck.__post_init__ exit theorem=%s", self.theorem)


def parse_theorem_statement(source: str) -> TheoremStatement:
    """Parse `theorem name forall x:kind :: prop -> prop` syntax."""
    logger.debug("parse_theorem_statement entry source=%r", source)
    if "::" not in source:
        logger.error("parse_theorem_statement missing separator")
        raise ValueError("missing theorem body separator '::'")
    header, body = (part.strip() for part in source.split("::", 1))
    match = re.fullmatch(r"theorem\s+([A-Za-z][\w-]*)\s+forall\s+(.+)", header)
    if not match:
        logger.error("parse_theorem_statement bad header=%s", header)
        raise ValueError("bad theorem header")
    name = match.group(1)
    quantifiers = _parse_quantifiers(match.group(2))
    connective, left, right = _split_body(body)
    assumptions = tuple(_parse_prop(part) for part in _split_conjunction(left)) if right else ()
    conclusions = tuple(_parse_prop(part) for part in _split_conjunction(right or left))
    declared = frozenset(quantifier.name for quantifier in quantifiers)
    for prop in assumptions + conclusions:
        unknown = frozenset(template_variables(prop.template)) - declared
        if unknown:
            logger.error(
                "parse_theorem_statement undeclared placeholders=%r",
                sorted(unknown),
            )
            raise ValueError(f"undeclared theorem placeholder ${sorted(unknown)[0]}")
    result = TheoremStatement(name, quantifiers, assumptions, conclusions, connective)
    logger.debug("parse_theorem_statement exit result=%r", result)
    return result


def check_theorem_statement(statement: TheoremStatement, environments: Iterable[TheoremEnvironment]) -> TheoremCheck:
    """Check finite proof obligations for a theorem statement."""
    theorem_name = statement.name if type(statement) is TheoremStatement and type(statement.name) is str else "<invalid>"
    logger.debug("check_theorem_statement entry theorem=%s", theorem_name)
    obligations: list[ProofObligation] = []
    blocked: list[str] = []
    if not exact_statement_graph(
        statement, TheoremStatement, TheoremQuantifier, TheoremProposition,
    ):
        logger.error("check_theorem_statement noncanonical statement graph")
        return TheoremCheck(
            theorem_name, "blocked", (), ("invalid-statement:noncanonical object graph",),
        )
    validation_errors = statement_errors(
        statement.name,
        statement.quantifiers,
        statement.assumptions,
        statement.conclusions,
        statement.connective,
    )
    if validation_errors:
        logger.error(
            "check_theorem_statement invalid statement theorem=%r errors=%r",
            statement.name,
            validation_errors,
        )
        return TheoremCheck(
            statement.name,
            "blocked",
            (),
            tuple(f"invalid-statement:{error}" for error in validation_errors),
        )
    finite_environments = tuple(environments)
    if not finite_environments:
        logger.error("check_theorem_statement no finite environments theorem=%s", statement.name)
        blocked.append("no-finite-environments")
    environment_names = tuple(environment.name for environment in finite_environments)
    duplicates = tuple(dict.fromkeys(
        name for name in environment_names if environment_names.count(name) > 1
    ))
    if duplicates:
        logger.error("check_theorem_statement duplicate environments=%r", duplicates)
        reasons = tuple(f"duplicate-environment-name:{name}" for name in duplicates)
        return TheoremCheck(statement.name, "blocked", (), reasons)
    for env in finite_environments:
        try:
            assignments = dict(env.assignments.items())
        except (AttributeError, TypeError, ValueError) as exc:
            logger.error(
                "check_theorem_statement invalid environment env=%r error=%s",
                env.name,
                exc,
            )
            blocked.append(f"{env.name}:invalid assignments")
            continue
        declared = frozenset(quantifier.name for quantifier in statement.quantifiers)
        stable_env = TheoremEnvironment(
            env.name, {name: value for name, value in assignments.items() if name in declared},
        )
        env_errors = _environment_errors(statement, stable_env)
        if env_errors:
            blocked.extend(f"{env.name}:{err}" for err in env_errors)
            continue
        rows = [_check_prop(statement.name, stable_env, "assumption", prop) for prop in statement.assumptions]
        rows.extend(_check_prop(statement.name, stable_env, "conclusion", prop) for prop in statement.conclusions)
        obligations.extend(rows)
        if any(row.status != "ready" for row in rows):
            blocked.append(env.name)
    result = TheoremCheck(statement.name, "ready" if not blocked else "blocked", tuple(obligations), tuple(blocked))
    logger.debug("check_theorem_statement exit status=%s obligations=%d", result.status, len(result.obligations))
    return result


def theorem_obligation_rows() -> tuple[ProofObligation, ...]:
    """Return default F2 obligation rows, including a blocked diagnostic."""
    from .theorem_language_fixtures import theorem_obligation_rows as build_rows
    return build_rows()
def default_theorem_environments() -> tuple[TheoremEnvironment, ...]:
    """Return finite theorem-language fixtures."""
    from .theorem_language_fixtures import default_theorem_environments as build_environments
    return build_environments()
def theorem_language_checklist() -> tuple[str, ...]:
    """Return F2 theorem-language capabilities."""
    from .theorem_language_fixtures import theorem_language_checklist as build_checklist
    return build_checklist()


def _parse_quantifiers(text: str) -> tuple[TheoremQuantifier, ...]:
    logger.debug("_parse_quantifiers entry text=%s", text)
    rows = []
    for part in text.split(","):
        pieces = tuple(piece.strip() for piece in part.split(":"))
        if len(pieces) != 2 or not _IDENTIFIER.fullmatch(pieces[0]):
            logger.error("_parse_quantifiers bad declaration=%r", part)
            raise ValueError(f"bad quantifier declaration {part!r}")
        name, kind = pieces
        if any(row.name == name for row in rows):
            logger.error("_parse_quantifiers duplicate name=%s", name)
            raise ValueError(f"duplicate quantifier {name!r}")
        try:
            rows.append(TheoremQuantifier(name, VeyraKind(kind)))
        except ValueError as exc:
            logger.error("_parse_quantifiers bad kind name=%s kind=%s", name, kind)
            raise ValueError(f"bad quantifier kind {kind!r}") from exc
    result = tuple(rows)
    logger.debug("_parse_quantifiers exit count=%d", len(result))
    return result


def _split_body(body: str) -> tuple[str, str, str]:
    logger.debug("_split_body entry body=%s", body)
    for op, name in (("<->", "iff"), ("->", "implies")):
        parts = _split_top_level(body, op)
        if parts:
            result = (name, parts[0].strip(), parts[1].strip())
            logger.debug("_split_body exit result=%r", result)
            return result
    result = ("asserts", body.strip(), "")
    logger.debug("_split_body exit result=%r", result)
    return result


def _split_top_level(text: str, op: str) -> tuple[str, str] | None:
    logger.debug("_split_top_level entry op=%s", op)
    depth = 0
    for index, char in enumerate(text):
        depth += char == "("
        depth -= char == ")"
        if depth == 0 and text.startswith(op, index):
            return text[:index], text[index + len(op) :]
    logger.debug("_split_top_level exit none")
    return None


def _split_conjunction(text: str) -> tuple[str, ...]:
    logger.debug("_split_conjunction entry text=%s", text)
    result = tuple(part.strip() for part in re.split(r"\s+&\s+", text) if part.strip())
    logger.debug("_split_conjunction exit count=%d", len(result))
    return result


def _parse_prop(text: str) -> TheoremProposition:
    logger.debug("_parse_prop entry text=%s", text)
    match = re.fullmatch(r"(ready|blocked|unknown)\((.*)\)", text.strip())
    if not match:
        logger.error("_parse_prop bad proposition=%s", text)
        raise ValueError(f"bad proposition {text!r}")
    result = TheoremProposition(match.group(1), match.group(2).strip())
    logger.debug("_parse_prop exit result=%r", result)
    return result


def _environment_errors(statement: TheoremStatement, env: TheoremEnvironment) -> tuple[str, ...]:
    logger.debug("_environment_errors entry theorem=%s env=%s", statement.name, env.name)
    errors = []
    for quant in statement.quantifiers:
        source = env.assignments.get(quant.name)
        if source is None:
            errors.append(f"missing ${quant.name}")
            continue
        if not isinstance(source, str) or "$" in source:
            errors.append(f"invalid ${quant.name}: replacement must be placeholder-free text")
            continue
        try:
            check = expr_kind(parse_veyra(source))
        except ValueError as exc:
            logger.error(
                "_environment_errors invalid replacement env=%s variable=%s error=%s",
                env.name,
                quant.name,
                exc,
            )
            errors.append(f"invalid ${quant.name}: {exc}")
            continue
        if check.kind != quant.kind:
            errors.append(f"kind ${quant.name} expected {quant.kind.value} got {check.kind}")
    result = tuple(errors)
    logger.debug("_environment_errors exit count=%d", len(result))
    return result


def _check_prop(theorem: str, env: TheoremEnvironment, role: str, prop: TheoremProposition) -> ProofObligation:
    logger.debug("_check_prop entry theorem=%s env=%s role=%s", theorem, env.name, role)
    source = substitute_template(prop.template, env.assignments)
    check = infer_veyra(parse_veyra(source))
    status = "ready" if check.status == prop.expected_status else "blocked"
    result = ProofObligation(
        theorem, env.name, role, source, prop.expected_status, check.status, status, check.obstruction
    )
    logger.debug("_check_prop exit result=%r", result)
    return result

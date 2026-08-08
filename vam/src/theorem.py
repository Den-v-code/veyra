"""VAM theorem/obligation carrier layer.

This module lowers Core theorem-language records into structured VAM data.
It transports finite Core obligation checks; it is not a proof checker.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable, Mapping

from src.core.theorem_language import (
    ProofObligation as CoreProofObligation,
    TheoremEnvironment,
    TheoremStatement,
    check_theorem_statement,
    parse_theorem_statement,
)

from .model import VamObject
from .theorem_snapshot import snapshot_environments

logger = logging.getLogger(__name__)
PROOF_STATUSES = frozenset({"verified", "imported", "conjectural", "blocked", "open"})
CORE_FINITE_BOUNDARY = "core.finite_obligation_check"
SUPPORTED_QUANTIFIER = "forall"


@dataclass(frozen=True)
class VamTheoremEnvironment:
    """Finite environment transported into a VAM theorem record."""

    name: str
    assignments: Mapping[str, str]
    status: str
    diagnostics: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "assignments": dict(self.assignments), "status": self.status, "diagnostics": self.diagnostics}


@dataclass(frozen=True)
class VamTheoremObligation:
    """One named VAM proof obligation derived from Core finite checks."""

    id: str
    theorem: str
    environment: str
    role: str
    category: str
    source: str
    expected_status: str
    actual_status: str
    status: str
    obstruction: str = ""

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class VamFiniteTheoremCase:
    """Explicit finite quantified theorem carrier for one executable case."""

    id: str
    environment: str
    quantifiers: tuple[dict[str, str], ...]
    assumptions: tuple[dict[str, str], ...]
    conclusions: tuple[dict[str, str], ...]
    status: str
    obstruction: str = ""

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class VamTheoremRecord:
    """Structured VAM theorem carrier with explicit no-overclaim fields."""

    id: str
    source: str
    binders: tuple[dict[str, str], ...]
    assumptions: tuple[dict[str, str], ...]
    claim: tuple[dict[str, str], ...]
    proof_status: str
    obligations: tuple[VamTheoremObligation, ...]
    environments: tuple[VamTheoremEnvironment, ...]
    finite_cases: tuple[VamFiniteTheoremCase, ...]
    trust_boundary: str
    diagnostics: tuple[str, ...]
    core_id: str

    def as_dict(self) -> dict[str, Any]:
        logger.debug("VamTheoremRecord.as_dict id=%s status=%s", self.id, self.proof_status)
        data = self.__dict__.copy()
        data["obligations"] = tuple(row.as_dict() for row in self.obligations)
        data["environments"] = tuple(env.as_dict() for env in self.environments)
        data["finite_cases"] = tuple(case.as_dict() for case in self.finite_cases)
        return data

    def as_vam_object(self) -> VamObject:
        """Return this theorem as a VAM runtime object for transport."""
        logger.debug("VamTheoremRecord.as_vam_object id=%s", self.id)
        return VamObject("Theorem", self.as_dict())


def lower_theorem_source(source: str, environments: Iterable[TheoremEnvironment], *, module: str = "core", requested_status: str | None = None, trust_boundary: str = CORE_FINITE_BOUNDARY) -> VamTheoremRecord:
    """Parse and lower a Core theorem source string into a VAM record."""
    logger.debug("lower_theorem_source entry module=%s requested=%s", module, requested_status)
    return lower_theorem_statement(parse_theorem_statement(source), environments, module=module, source=source, requested_status=requested_status, trust_boundary=trust_boundary)


def lower_theorem_statement(statement: TheoremStatement, environments: Iterable[TheoremEnvironment], *, module: str = "core", source: str | None = None, requested_status: str | None = None, trust_boundary: str = CORE_FINITE_BOUNDARY) -> VamTheoremRecord:
    """Lower an already parsed theorem statement into a VAM theorem record."""
    envs = snapshot_environments(tuple(environments))
    logger.debug("lower_theorem_statement entry theorem=%s envs=%d", statement.name, len(envs))
    quantifier_problem = _quantifier_problem(statement)
    if quantifier_problem:
        obligations = (_unsupported_quantifier_obligation(statement.name, quantifier_problem),)
        env_records = tuple(VamTheoremEnvironment(env.name, env.assignments, "open", (quantifier_problem,)) for env in envs)
        finite_cases: tuple[VamFiniteTheoremCase, ...] = ()
        check_status = "unsupported"
    else:
        check = check_theorem_statement(statement, envs)
        obligations = _lower_obligations(statement.name, check.obligations, check.blocked)
        env_records = _environment_records(envs, check.blocked)
        finite_cases = _finite_cases(statement, envs, obligations, check.blocked)
        check_status = check.status
    proof_status = _proof_status(check_status, finite_cases, requested_status, trust_boundary)
    record = VamTheoremRecord(
        id=f"vam:{module}:{statement.name}", source=source or statement.name,
        binders=tuple(_binder_dict(q) for q in statement.quantifiers),
        assumptions=tuple(_prop_dict("assumption", i, p) for i, p in enumerate(statement.assumptions)),
        claim=tuple(_prop_dict("conclusion", i, p) for i, p in enumerate(statement.conclusions)),
        proof_status=proof_status, obligations=obligations, environments=env_records, finite_cases=finite_cases,
        trust_boundary=trust_boundary, diagnostics=_diagnostics(check_status, obligations, requested_status, finite_cases, trust_boundary), core_id=statement.name)
    logger.debug("lower_theorem_statement exit theorem=%s status=%s cases=%d", statement.name, proof_status, len(finite_cases))
    return record


def _binder_dict(quantifier: Any) -> dict[str, str]:
    return {"name": _quantifier_name(quantifier), "kind": _kind_value(quantifier), "quantifier": _quantifier_shape(quantifier)}


def _prop_dict(role: str, index: int, prop: Any) -> dict[str, str]:
    return {"id": f"{role}:{index}", "expected_status": prop.expected_status, "template": prop.template}


def _quantifier_name(quantifier: Any) -> str:
    return str(getattr(quantifier, "name", ""))


def _quantifier_shape(quantifier: Any) -> str:
    return str(getattr(quantifier, "quantifier", SUPPORTED_QUANTIFIER))


def _kind_value(quantifier: Any) -> str:
    kind = getattr(quantifier, "kind", "")
    return str(getattr(kind, "value", kind))


def _quantifier_problem(statement: TheoremStatement) -> str:
    if not statement.quantifiers:
        return "unsupported quantifier shape: no finite forall binders"
    for quantifier in statement.quantifiers:
        shape = _quantifier_shape(quantifier)
        if shape != SUPPORTED_QUANTIFIER:
            return f"unsupported quantifier shape: {shape}"
        if not _quantifier_name(quantifier) or not _kind_value(quantifier):
            return "unsupported quantifier shape: missing finite binder name or kind"
    return ""


def _unsupported_quantifier_obligation(theorem: str, reason: str) -> VamTheoremObligation:
    return VamTheoremObligation(f"{theorem}:quantifier:0", theorem, "", "quantifier", "wf.quantifier", reason, "finite.forall", "unsupported", "open", reason)


def _lower_obligations(theorem: str, core_rows: tuple[CoreProofObligation, ...], blocked: tuple[str, ...]) -> tuple[VamTheoremObligation, ...]:
    rows = [_lower_core_obligation(index, row) for index, row in enumerate(core_rows)]
    start = len(rows)
    for offset, reason in enumerate(blocked):
        if ":" not in reason:
            continue
        env, obstruction = reason.split(":", 1)
        rows.append(VamTheoremObligation(f"{theorem}:{env}:env:{start + offset}", theorem, env, "environment", "wf.quantifier", env, "ready", "blocked", "open", obstruction.strip()))
    return tuple(rows)


def _lower_core_obligation(index: int, row: CoreProofObligation) -> VamTheoremObligation:
    return VamTheoremObligation(f"{row.theorem}:{row.environment}:{row.role}:{index}", row.theorem, row.environment, row.role, _category(row), row.source, row.expected_status, row.actual_status, _obligation_status(row), row.obstruction)


def _obligation_status(row: CoreProofObligation) -> str:
    return "blocked" if row.actual_status == "unknown" or row.expected_status == "unknown" else ("verified" if row.status == "ready" else "blocked")


def _category(row: CoreProofObligation) -> str:
    if row.actual_status == "unknown" or row.expected_status == "unknown":
        return "semantics.opaque"
    return "boundary.no_overclaim" if row.status != "ready" else ("proof.finite" if row.role == "conclusion" else "proof.assumption")


def _blocked_reasons(blocked: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    reasons: dict[str, list[str]] = {}
    for item in blocked:
        env, sep, detail = item.partition(":")
        reasons.setdefault(env, []).extend([detail or "blocked obligation"] if sep else [])
    return {env: tuple(rows) for env, rows in reasons.items()}


def _environment_records(envs: tuple[TheoremEnvironment, ...], blocked: tuple[str, ...]) -> tuple[VamTheoremEnvironment, ...]:
    reasons = _blocked_reasons(blocked)
    return tuple(VamTheoremEnvironment(env.name, env.assignments, _environment_status(reasons.get(env.name, ())), reasons.get(env.name, ())) for env in envs)


def _environment_status(reasons: tuple[str, ...]) -> str:
    if not reasons:
        return "ready"
    return "open" if any("missing" in r or "kind $" in r for r in reasons) else "blocked"


def _finite_cases(statement: TheoremStatement, envs: tuple[TheoremEnvironment, ...], obligations: tuple[VamTheoremObligation, ...], blocked: tuple[str, ...]) -> tuple[VamFiniteTheoremCase, ...]:
    by_env: dict[str, list[VamTheoremObligation]] = {}
    reasons = _blocked_reasons(blocked)
    for row in obligations:
        if row.role != "environment":
            by_env.setdefault(row.environment, []).append(row)
    cases = []
    for env in envs:
        if _environment_status(reasons.get(env.name, ())) == "open":
            continue
        rows = tuple(by_env.get(env.name, ()))
        if not rows:
            continue
        obstruction = "; ".join(row.obstruction or row.category for row in rows if row.status != "verified")
        cases.append(VamFiniteTheoremCase(f"{statement.name}:{env.name}", env.name, _case_quantifiers(statement, env), _case_props(rows, "assumption"), _case_props(rows, "conclusion"), _case_status(rows), obstruction))
    return tuple(cases)


def _case_quantifiers(statement: TheoremStatement, env: TheoremEnvironment) -> tuple[dict[str, str], ...]:
    return tuple({**_binder_dict(q), "value": env.assignments.get(_quantifier_name(q), ""), "status": "bound" if _quantifier_name(q) in env.assignments else "missing"} for q in statement.quantifiers)


def _case_props(rows: tuple[VamTheoremObligation, ...], role: str) -> tuple[dict[str, str], ...]:
    return tuple({"id": row.id, "source": row.source, "expected_status": row.expected_status, "actual_status": row.actual_status, "status": row.status, "category": row.category, "obstruction": row.obstruction} for row in rows if row.role == role)


def _case_status(rows: tuple[VamTheoremObligation, ...]) -> str:
    return "blocked" if any(row.status == "blocked" for row in rows) else ("verified" if rows and all(row.status == "verified" for row in rows) else "open")


def _proof_status(check_status: str, finite_cases: tuple[VamFiniteTheoremCase, ...], requested: str | None, trust_boundary: str) -> str:
    logger.debug("_proof_status entry check=%s requested=%s cases=%d", check_status, requested, len(finite_cases))
    if not finite_cases:
        return "open"
    if any(case.status == "blocked" for case in finite_cases):
        return "blocked"
    if any(case.status != "verified" for case in finite_cases) or check_status != "ready" or (requested is not None and requested not in PROOF_STATUSES):
        return "open"
    if requested == "imported":
        return "imported" if trust_boundary else "blocked"
    return "conjectural" if requested == "conjectural" else "verified"


def _diagnostics(check_status: str, obligations: tuple[VamTheoremObligation, ...], requested: str | None, finite_cases: tuple[VamFiniteTheoremCase, ...], trust_boundary: str) -> tuple[str, ...]:
    rows = [f"finite theorem carrier transports executable Core obligations only via {trust_boundary or 'no-boundary'}; not proof-assistant semantics"]
    if not finite_cases:
        rows.append("no executable finite obligation cases; theorem status remains open")
    if requested is not None and requested not in PROOF_STATUSES:
        rows.append(f"unsupported requested proof status: {requested}")
    if requested == "verified" and any(row.status != "verified" for row in obligations):
        rows.append("requested verified downgraded by open or blocked obligations")
    if any(row.category == "semantics.opaque" for row in obligations):
        rows.append("opaque or unsupported executable semantics block verification at the non-proof boundary")
    if check_status != "ready":
        rows.append(f"Core finite check status: {check_status}")
    return tuple(rows)

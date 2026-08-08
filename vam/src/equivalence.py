"""Conservative whole-program execution summaries for VAM optimizer checks."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable, Sequence

from .interpreter import execute
from .model import Instruction, VamExecutionError, VamObject, VamState
from .report import canonical_report

logger = logging.getLogger(__name__)
Status = str
VERDICT_SAFE = "safe"
VERDICT_NON_SAFE = "non-safe"
SIDE_EFFECT_ROOTS = {"CERT", "ECHO", "OBSTRUCT"}


@dataclass(frozen=True)
class EquivalenceCheck:
    """One bounded comparison between two executed VAM programs."""

    name: str
    status: Status
    detail: str
    original: Any = None
    optimized: Any = None


@dataclass(frozen=True)
class EquivalenceSummary:
    """Execution-based optimizer equivalence evidence, not a proof."""

    status: Status
    verdict: str
    original_ops: int
    optimized_ops: int
    original_trace: int
    optimized_trace: int
    checks: tuple[EquivalenceCheck, ...]

    @property
    def safe(self) -> bool:
        """True only when all required executable checks matched."""
        return self.verdict == VERDICT_SAFE

    def check(self, name: str) -> EquivalenceCheck:
        """Fetch a named check for tests and callers."""
        for item in self.checks:
            if item.name == name:
                return item
        raise KeyError(name)


def summarize_equivalence(
    original: Iterable[Instruction],
    optimized: Iterable[Instruction],
    *,
    root_registers: Sequence[str] | None = None,
) -> EquivalenceSummary:
    """Execute two VAM programs and compare conservative observable summaries."""
    original_program = tuple(original)
    optimized_program = tuple(optimized)
    logger.debug(
        "summarize_equivalence entry original_ops=%d optimized_ops=%d",
        len(original_program),
        len(optimized_program),
    )
    try:
        original_state = execute(original_program)
        optimized_state = execute(optimized_program)
    except VamExecutionError as exc:
        check = EquivalenceCheck("execution", "blocked", str(exc))
        return _summary("blocked", original_program, optimized_program, None, None, (check,))

    roots = tuple(root_registers) if root_registers is not None else _selected_roots(original_program, optimized_program)
    checks = (
        _cert_acceptance_check(original_program, optimized_program, original_state, optimized_state),
        _report_fingerprint_check(original_program, optimized_program, original_state, optimized_state, roots),
        _obstruction_count_check(original_state, optimized_state),
        _root_evidence_check(roots, original_state, optimized_state),
    )
    if any(item.status == "blocked" for item in checks):
        status = "blocked"
    elif any(item.status == "unknown" for item in checks):
        status = "unknown"
    else:
        status = "equivalent"
    result = _summary(status, original_program, optimized_program, original_state, optimized_state, checks)
    logger.debug("summarize_equivalence exit status=%s verdict=%s", result.status, result.verdict)
    return result


def compare_optimizer_programs(
    original: Iterable[Instruction],
    optimized: Iterable[Instruction],
    *,
    root_registers: Sequence[str] | None = None,
) -> EquivalenceSummary:
    """Alias with a name that states the intended optimizer boundary."""
    return summarize_equivalence(original, optimized, root_registers=root_registers)


def _summary(
    status: Status,
    original: tuple[Instruction, ...],
    optimized: tuple[Instruction, ...],
    original_state: VamState | None,
    optimized_state: VamState | None,
    checks: tuple[EquivalenceCheck, ...],
) -> EquivalenceSummary:
    verdict = VERDICT_SAFE if status == "equivalent" else VERDICT_NON_SAFE
    return EquivalenceSummary(
        status,
        verdict,
        len(original),
        len(optimized),
        len(original_state.trace) if original_state else 0,
        len(optimized_state.trace) if optimized_state else 0,
        checks,
    )


def _dst(inst: Instruction) -> str | None:
    if inst.args and isinstance(inst.args[0], str) and inst.args[0].startswith("%r"):
        return inst.args[0]
    return None


def _selected_roots(original: tuple[Instruction, ...], optimized: tuple[Instruction, ...]) -> tuple[str, ...]:
    common = {_dst(inst) for inst in original if _dst(inst)} & {_dst(inst) for inst in optimized if _dst(inst)}
    roots = [_dst(inst) for inst in original if inst.op in SIDE_EFFECT_ROOTS and _dst(inst) in common]
    if roots:
        return tuple(dict.fromkeys(reg for reg in roots if reg))
    for inst in reversed(original):
        dst = _dst(inst)
        if dst in common:
            return (dst,)
    return ()


def _cert_acceptance_check(
    original_program: tuple[Instruction, ...],
    optimized_program: tuple[Instruction, ...],
    original_state: VamState,
    optimized_state: VamState,
) -> EquivalenceCheck:
    original_certs = _cert_acceptance(original_program, original_state)
    optimized_certs = _cert_acceptance(optimized_program, optimized_state)
    status = "equivalent" if original_certs == optimized_certs else "blocked"
    detail = "certificate acceptance matched" if status == "equivalent" else "certificate acceptance mismatch"
    return EquivalenceCheck("cert-acceptance", status, detail, original_certs, optimized_certs)


def _cert_acceptance(program: tuple[Instruction, ...], state: VamState) -> tuple[tuple[Any, bool | None], ...]:
    rows: list[tuple[Any, bool | None]] = []
    for inst in program:
        if inst.op != "CERT":
            continue
        dst = _dst(inst)
        cert = state.registers.get(dst or "")
        rows.append((cert.field("claim") if cert else None, cert.field("accepted") if cert else None))
    return tuple(rows)


def _report_fingerprint_check(
    original_program: tuple[Instruction, ...],
    optimized_program: tuple[Instruction, ...],
    original_state: VamState,
    optimized_state: VamState,
    roots: tuple[str, ...],
) -> EquivalenceCheck:
    original_report = canonical_report(original_program, original_state)
    optimized_report = canonical_report(optimized_program, optimized_state)
    original_fingerprint = _report_fingerprint(original_report, roots)
    optimized_fingerprint = _report_fingerprint(optimized_report, roots)
    status = "equivalent" if original_fingerprint == optimized_fingerprint else "blocked"
    detail = (
        f"canonical report fingerprint matched for {len(roots)} root(s)"
        if status == "equivalent"
        else "canonical report fingerprint mismatch"
    )
    return EquivalenceCheck("report-fingerprint", status, detail, original_fingerprint, optimized_fingerprint)


def _report_fingerprint(report: dict[str, Any], roots: tuple[str, ...]) -> tuple[Any, ...]:
    root_rows = tuple((reg, report["registers"].get(reg)) for reg in roots)
    cert_rows = tuple(
        (
            cert["data"]["claim"],
            cert["data"]["accepted"],
            cert["data"]["boundary"],
            cert["data"]["evidence"],
        )
        for cert in report["certs"]
    )
    obstruction_rows = tuple(report["obstructions"])
    return (root_rows, cert_rows, obstruction_rows)


def _obstruction_count_check(original_state: VamState, optimized_state: VamState) -> EquivalenceCheck:
    original_count = _nested_obstruction_count(original_state)
    optimized_count = _nested_obstruction_count(optimized_state)
    status = "equivalent" if original_count == optimized_count else "blocked"
    detail = "obstruction counts matched" if status == "equivalent" else "obstruction count mismatch"
    return EquivalenceCheck("obstruction-count", status, detail, original_count, optimized_count)


def _nested_obstruction_count(state: VamState) -> int:
    seen: set[int] = set()
    return sum(_count_obstructions(obj, seen) for obj in state.registers.values())


def _count_obstructions(value: Any, seen: set[int]) -> int:
    if isinstance(value, VamObject):
        ident = id(value)
        if ident in seen:
            return 0
        seen.add(ident)
        return (1 if value.kind == "Obstruction" else 0) + _count_obstructions(value.data, seen)
    if isinstance(value, dict):
        return sum(_count_obstructions(item, seen) for item in value.values())
    if isinstance(value, (tuple, list)):
        return sum(_count_obstructions(item, seen) for item in value)
    return 0


def _root_evidence_check(roots: tuple[str, ...], original_state: VamState, optimized_state: VamState) -> EquivalenceCheck:
    if not roots:
        return EquivalenceCheck("root-evidence", "unknown", "no common semantic root registers")
    original_missing = tuple(reg for reg in roots if reg not in original_state.registers)
    optimized_missing = tuple(reg for reg in roots if reg not in optimized_state.registers)
    if original_missing or optimized_missing:
        if original_missing == optimized_missing:
            return EquivalenceCheck("root-evidence", "unknown", "selected roots missing", original_missing, optimized_missing)
        return EquivalenceCheck("root-evidence", "blocked", "selected root availability mismatch", original_missing, optimized_missing)
    original = tuple((reg, _fingerprint(original_state.registers.get(reg))) for reg in roots)
    optimized = tuple((reg, _fingerprint(optimized_state.registers.get(reg))) for reg in roots)
    status = "equivalent" if original == optimized else "blocked"
    detail = f"root evidence matched for {len(roots)} register(s)" if status == "equivalent" else "root evidence mismatch"
    return EquivalenceCheck("root-evidence", status, detail, original, optimized)


def _fingerprint(value: Any) -> Any:
    if isinstance(value, VamObject):
        return (value.kind, _fingerprint(value.data))
    if isinstance(value, dict):
        return tuple((key, _fingerprint(value[key])) for key in sorted(value))
    if isinstance(value, (tuple, list)):
        return tuple(_fingerprint(item) for item in value)
    if isinstance(value, set):
        return tuple(sorted(_fingerprint(item) for item in value))
    return value

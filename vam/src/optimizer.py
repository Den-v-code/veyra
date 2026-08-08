"""Conservative VAM optimizer: preserve echo/cert/obstruction semantics."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable

from .interpreter import execute, execute_with_definition_objects
from .model import Instruction, VamObject

logger = logging.getLogger(__name__)
CANDIDATE_DEAD_OPS, SIDE_EFFECT_OPS = {"OBSERVE", "COMPRESS"}, {"CERT", "OBSTRUCT", "ECHO"}
IDEMPOTENT_OBSERVER_KINDS = {"boundary", "kind", "label", "length", "trace"}
UseMap = dict[str, list[tuple[int, Instruction]]]


@dataclass(frozen=True)
class OptimizationRow:
    """One optimizer decision row."""

    pass_name: str
    action: str
    detail: str
    accepted: bool


@dataclass(frozen=True)
class OptimizationReport:
    """Optimizer result and audit rows."""

    original: tuple[Instruction, ...]
    optimized: tuple[Instruction, ...]
    rows: tuple[OptimizationRow, ...]

    @property
    def accepted_rows(self) -> tuple[OptimizationRow, ...]:
        return tuple(row for row in self.rows if row.accepted)

    @property
    def rejected_rows(self) -> tuple[OptimizationRow, ...]:
        return tuple(row for row in self.rows if not row.accepted)


PassResult = tuple[tuple[Instruction, ...], list[OptimizationRow]]

def _dst(inst: Instruction) -> str | None:
    return inst.args[0] if inst.args and isinstance(inst.args[0], str) and inst.args[0].startswith("%r") else None


def _used_regs(inst: Instruction) -> set[str]:
    return {arg for arg in inst.args[1:] if isinstance(arg, str) and arg.startswith("%r")}


def _rewrite_args(args: tuple[Any, ...], aliases: dict[str, str]) -> tuple[Any, ...]:
    if not args:
        return args
    head, tail = args[0], args[1:]
    rewritten = tuple(aliases.get(arg, arg) if isinstance(arg, str) else arg for arg in tail)
    return (head, *rewritten)


def _definition_counts(program: Iterable[Instruction]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for inst in program:
        dst = _dst(inst)
        if dst:
            counts[dst] = counts.get(dst, 0) + 1
    return counts


def _definition_objects(program: tuple[Instruction, ...]) -> dict[int, VamObject]:
    return execute_with_definition_objects(program)[1]


def _contains_obstruction(value: Any) -> bool:
    if isinstance(value, VamObject):
        return value.kind == "Obstruction" or _contains_obstruction(value.data)
    if isinstance(value, dict):
        return any(_contains_obstruction(item) for item in value.values())
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_contains_obstruction(item) for item in value)
    return False


def _has_single_definition(reg: Any, counts: dict[str, int]) -> bool:
    return isinstance(reg, str) and reg.startswith("%r") and counts.get(reg) == 1


def _is_reg(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("%r")


def _use_contexts(program: tuple[Instruction, ...]) -> UseMap:
    uses: UseMap = {}
    for index, inst in enumerate(program):
        for arg in inst.args[1:]:
            if _is_reg(arg):
                uses.setdefault(arg, []).append((index, inst))
    return uses


def _compress_defs(program: tuple[Instruction, ...]) -> dict[str, tuple[str, str, int]]:
    definitions: dict[str, tuple[str, str, int]] = {}
    for index, inst in enumerate(program):
        dst = _dst(inst)
        if inst.op == "COMPRESS" and dst and len(inst.args) == 3:
            source, observer = inst.args[1], inst.args[2]
            if _is_reg(source) and _is_reg(observer):
                definitions[dst] = (source, observer, index)
    return definitions


def _same_observer_use_reason(dst: str, observer: str, use_contexts: UseMap, after_index: int) -> str | None:
    uses = [(index, inst) for index, inst in use_contexts.get(dst, ()) if index > after_index]
    if not uses:
        return "unused candidate is handled by dead-shadow"
    for _, inst in uses:
        positions = [pos for pos, arg in enumerate(inst.args) if pos > 0 and arg == dst]
        for pos in positions:
            if inst.op in {"OBSERVE", "COMPRESS"}:
                if len(inst.args) != 3 or pos != 1 or inst.args[2] != observer:
                    return f"{dst} used outside same-observer {inst.op}"
            elif inst.op == "ECHO":
                if len(inst.args) != 4 or pos not in {1, 2} or inst.args[3] != observer:
                    return f"{dst} used outside same-observer ECHO"
            elif inst.op == "OBSTRUCT":
                return "candidate feeds OBSTRUCT evidence boundary"
            elif inst.op == "CERT":
                return "candidate feeds CERT directly"
            else:
                return f"unsupported use {inst.op}"
    return None


def _idempotent_reject_reason(
    dst: str, source: str, observer: str, prior_source: str, counts: dict[str, int], objects: dict[str, VamObject],
    use_contexts: UseMap, index: int,
) -> str | None:
    if not all(_is_reg(reg) for reg in (dst, source, observer, prior_source)):
        return "non-register compression operand"
    if not all(_has_single_definition(reg, counts) for reg in (dst, source, observer, prior_source)):
        return "multiple definitions"
    target_obj, source_obj, candidate_obj = objects.get(prior_source), objects.get(source), objects.get(dst)
    if not target_obj or not source_obj or not candidate_obj:
        return "missing definition object"
    if _contains_obstruction(target_obj):
        return "compression target obstruction would be hidden"
    if _contains_obstruction(source_obj) or _contains_obstruction(candidate_obj):
        return "nested obstruction would be erased"
    observer_obj = objects.get(observer)
    if not observer_obj or observer_obj.kind != "Observer":
        return "observer missing or malformed"
    kind = str(observer_obj.field("kind"))
    if kind not in IDEMPOTENT_OBSERVER_KINDS:
        return f"observer kind {kind!r} lacks idempotent contract"
    return _same_observer_use_reason(dst, observer, use_contexts, index)


def _observer_alias_pass(program: tuple[Instruction, ...]) -> tuple[tuple[Instruction, ...], list[OptimizationRow]]:
    logger.debug("observer_alias_pass entry instructions=%d", len(program))
    counts = _definition_counts(program)
    aliases: dict[str, str] = {}
    observer_by_kind: dict[str, str] = {}
    output: list[Instruction] = []
    rows: list[OptimizationRow] = []
    for inst in program:
        args = _rewrite_args(inst.args, aliases)
        dst = _dst(Instruction(inst.op, args, inst.line))
        if inst.op == "OBSERVER" and dst and len(args) == 2 and counts.get(dst) == 1:
            kind = str(args[1])
            if kind in observer_by_kind:
                aliases[dst] = observer_by_kind[kind]
                detail = f"{dst}->{observer_by_kind[kind]} kind={kind}"
                rows.append(OptimizationRow("observer-alias", "remove", detail, True))
                continue
            observer_by_kind[kind] = dst
        output.append(Instruction(inst.op, args, inst.line))
    logger.debug("observer_alias_pass exit instructions=%d rows=%d", len(output), len(rows))
    return tuple(output), rows


def _compress_alias_pass(program: tuple[Instruction, ...]) -> tuple[tuple[Instruction, ...], list[OptimizationRow]]:
    logger.debug("compress_alias_pass entry instructions=%d", len(program))
    counts = _definition_counts(program)
    objects = _definition_objects(program)
    aliases: dict[str, str] = {}
    compress_by_pair: dict[tuple[str, str], tuple[str, int]] = {}
    output: list[Instruction] = []
    rows: list[OptimizationRow] = []
    for index, inst in enumerate(program):
        args = _rewrite_args(inst.args, aliases)
        current = Instruction(inst.op, args, inst.line)
        dst = _dst(current)
        if current.op != "COMPRESS" or not dst or len(args) != 3:
            output.append(current)
            continue
        source, observer = args[1], args[2]
        pair = (source, observer)
        prior = compress_by_pair.get(pair)
        if prior:
            prior_dst, prior_index = prior
            safe_defs = all(_has_single_definition(reg, counts) for reg in (dst, prior_dst, source, observer))
            safe_objects = not (_contains_obstruction(objects[index]) or _contains_obstruction(objects[prior_index]))
            if safe_defs and safe_objects:
                aliases[dst] = prior_dst
                detail = f"{dst}->{prior_dst} source={source} observer={observer}"
                rows.append(OptimizationRow("compress-alias", "remove", detail, True))
                continue
            reason = "multiple definitions" if not safe_defs else "obstruction would be erased"
            rows.append(OptimizationRow("compress-alias", "reject", f"keep {dst}: {reason}", False))
        else:
            compress_by_pair[pair] = (dst, index)
        output.append(current)
    logger.debug("compress_alias_pass exit instructions=%d rows=%d", len(output), len(rows))
    return tuple(output), rows


def _compress_idempotent_pass(program: tuple[Instruction, ...]) -> PassResult:
    logger.debug("compress_idempotent_pass entry instructions=%d", len(program))
    counts = _definition_counts(program)
    objects = execute(program).registers
    use_contexts = _use_contexts(program)
    compress_defs = _compress_defs(program)
    aliases: dict[str, str] = {}
    output: list[Instruction] = []
    rows: list[OptimizationRow] = []
    for index, inst in enumerate(program):
        args = _rewrite_args(inst.args, aliases)
        current = Instruction(inst.op, args, inst.line)
        dst = _dst(current)
        if current.op != "COMPRESS" or not dst or len(args) != 3:
            output.append(current)
            continue
        source, observer = args[1], args[2]
        prior = compress_defs.get(source)
        if not prior:
            output.append(current)
            continue
        prior_source, prior_observer, _ = prior
        if prior_observer != observer:
            detail = f"keep {dst}: observer differs source={source} observer={observer} prior={prior_observer}"
            rows.append(OptimizationRow("compress-idempotent", "reject", detail, False))
            output.append(current)
            continue
        reason = _idempotent_reject_reason(dst, source, observer, prior_source, counts, objects, use_contexts, index)
        if reason:
            rows.append(OptimizationRow("compress-idempotent", "reject", f"keep {dst}: {reason}", False))
            output.append(current)
            continue
        aliases[dst] = source
        detail = f"{dst}->{source} prior_source={prior_source} observer={observer} reason=same-observer-visible"
        rows.append(OptimizationRow("compress-idempotent", "remove", detail, True))
    logger.debug("compress_idempotent_pass exit instructions=%d rows=%d", len(output), len(rows))
    return tuple(output), rows


def _dead_shadow_pass(program: tuple[Instruction, ...]) -> tuple[tuple[Instruction, ...], list[OptimizationRow]]:
    logger.debug("dead_shadow_pass entry instructions=%d", len(program))
    counts = _definition_counts(program)
    objects = _definition_objects(program)
    live: set[str] = set()
    output: list[Instruction] = []
    rows: list[OptimizationRow] = []
    for index, inst in reversed(list(enumerate(program))):
        dst = _dst(inst)
        removable = dst and dst not in live and inst.op in CANDIDATE_DEAD_OPS
        if removable and counts.get(dst) != 1:
            rows.append(OptimizationRow("dead-shadow", "reject", f"keep {dst}: multiple definitions", False))
        elif removable and _contains_obstruction(objects[index]):
            rows.append(OptimizationRow("dead-shadow", "reject", f"keep {dst}: obstruction would be erased", False))
        elif removable:
            rows.append(OptimizationRow("dead-shadow", "remove", f"drop unused {inst.op} {dst}", True))
            live.update(_used_regs(inst))
            continue
        output.append(inst)
        if dst and inst.op not in SIDE_EFFECT_OPS:
            live.discard(dst)
        live.update(_used_regs(inst))
    output.reverse()
    logger.debug("dead_shadow_pass exit instructions=%d rows=%d", len(output), len(rows))
    return tuple(output), rows


def optimize(program: Iterable[Instruction]) -> OptimizationReport:
    """Run safe VAM rewrites and return an auditable report."""
    original = tuple(program)
    logger.debug("optimize entry instructions=%d", len(original))
    aliased, alias_rows = _observer_alias_pass(original)
    compressed, compress_rows = _compress_alias_pass(aliased)
    normalized, normalize_rows = _compress_idempotent_pass(compressed)
    optimized, dead_rows = _dead_shadow_pass(normalized)
    rows = tuple(alias_rows + compress_rows + normalize_rows + dead_rows)
    logger.debug("optimize exit original=%d optimized=%d rows=%d", len(original), len(optimized), len(rows))
    return OptimizationReport(original, optimized, rows)

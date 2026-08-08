"""Bounded guard diagnostics and a whole-optimizer theorem skeleton.

The rows here expose missing proof premises.  They do not promote executable
equivalence checks into a proof of optimizer correctness.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Iterable

from .equivalence import summarize_equivalence
from .model import Instruction
from .opcodes import OpcodeValidationError, classify_instruction
from .optimizer import optimize

logger = logging.getLogger(__name__)

BOUNDARY = "bounded-optimizer-completion-skeleton"
CLAIM = "diagnostic-premise-ledger-not-proof"
PASS_ORDER = ("observer-alias", "compress-alias", "compress-idempotent", "dead-shadow")
MAX_PROGRAM_ROWS = 4096
MAX_CORPUS_ROWS = 128
UNRESOLVED_PREMISES = (
    "pass-domain closure for every well-formed VAM program",
    "compositional preservation between all pass pairs",
    "side-effect and obstruction trace bisimulation",
    "machine-checked correspondence between implementation and local laws",
)


@dataclass(frozen=True, slots=True)
class VisibleUseGuardRow:
    """Classification of every post-definition use of one candidate register."""

    candidate: str
    observer: str
    uses: int
    status: str
    reasons: tuple[str, ...]
    boundary: str = BOUNDARY


@dataclass(frozen=True, slots=True)
class OptimizerTheoremSkeleton:
    """Executable premises and explicit holes for a future optimizer theorem."""

    program_name: str
    pass_rows: tuple[tuple[str, int], ...]
    equivalence_status: str
    executable_premises_hold: bool
    unresolved_premises: tuple[str, ...]
    theorem_status: str = "open"
    proof_complete: bool = False
    boundary: str = BOUNDARY
    claim: str = CLAIM


@dataclass(frozen=True, slots=True)
class VamdEmissionPolicy:
    """Fail-closed result for the currently unavailable optimized VAMD encoder."""

    requested: bool
    allowed: bool
    status: str
    obstruction: str
    required_gates: tuple[str, ...]
    boundary: str = "vamd-optimized-frame-emission-policy"


def visible_use_guard(
    program: Iterable[Instruction], candidate: str, observer: str, *, after_index: int | None = None,
) -> VisibleUseGuardRow:
    """Check every use after one validated same-observer ``COMPRESS`` definition.

    Candidate index and observer are derived from the program. Caller values
    remain compatibility assertions and cannot choose either trust boundary.
    """
    rows = _snapshot_program(program)
    logger.debug(
        "visible_use_guard entry candidate=%s observer=%s rows=%d after=%r",
        candidate, observer, len(rows), after_index,
    )
    reasons: list[str] = []
    uses = 0
    malformed = _malformed_guard_rows(rows)
    if malformed:
        reasons.extend(malformed)
        result = VisibleUseGuardRow(candidate, observer, uses, "guard-rejected", tuple(reasons))
        logger.error("visible_use_guard rejected malformed rows=%d", len(malformed))
        logger.debug("visible_use_guard exit status=guard-rejected uses=0 reasons=%d", len(reasons))
        return result
    definition_indexes = tuple(
        index for index, inst in enumerate(rows) if inst.args[0] == candidate
    )
    if len(definition_indexes) != 1:
        reasons.append(f"candidate definitions={len(definition_indexes)}; expected exactly one")
    definition_index = definition_indexes[0] if len(definition_indexes) == 1 else None
    derived_observer = observer
    if definition_index is not None:
        definition = rows[definition_index]
        if definition.op != "COMPRESS":
            reasons.append(f"candidate definition op={definition.op}; expected COMPRESS")
        else:
            derived_observer = definition.args[2]
            if observer != derived_observer:
                reasons.append(
                    f"observer={observer!r} does not match candidate observer={derived_observer!r}"
                )
            observer_indexes = tuple(
                index for index, inst in enumerate(rows) if inst.args[0] == derived_observer
            )
            if len(observer_indexes) != 1:
                reasons.append(f"observer definitions={len(observer_indexes)}; expected exactly one")
            elif rows[observer_indexes[0]].op != "OBSERVER" or observer_indexes[0] >= definition_index:
                reasons.append("candidate observer lacks one prior OBSERVER definition")
    if after_index is not None and (
        type(after_index) is not int or definition_index is None or after_index != definition_index
    ):
        reasons.append(
            f"after_index={after_index!r} does not match validated definition index={definition_index!r}"
        )
    for index, inst in enumerate(rows):
        if definition_index is None or index <= definition_index:
            continue
        for position, arg in enumerate(inst.args[1:], start=1):
            if arg != candidate:
                continue
            uses += 1
            reason = _visible_use_rejection(inst, position, derived_observer)
            if reason:
                reasons.append(f"line={inst.line} index={index}: {reason}")
    if uses == 0:
        reasons.append("candidate has no visible post-definition uses")
    status = "guard-satisfied" if not reasons else "guard-rejected"
    result = VisibleUseGuardRow(candidate, derived_observer, uses, status, tuple(reasons))
    logger.debug("visible_use_guard exit status=%s uses=%d reasons=%d", status, uses, len(reasons))
    return result


def _malformed_guard_rows(rows: tuple[Instruction, ...]) -> tuple[str, ...]:
    """Return deterministic schema errors before any use classification."""
    logger.debug("malformed_guard_rows entry rows=%d", len(rows))
    reasons: list[str] = []
    for index, inst in enumerate(rows):
        if type(inst.op) is not str or type(inst.args) is not tuple or type(inst.line) is not int:
            reasons.append(f"line={inst.line!r} index={index}: malformed instruction row")
            continue
        try:
            classification = classify_instruction(inst)
        except (OpcodeValidationError, AttributeError, TypeError) as exc:
            reasons.append(f"line={inst.line} index={index}: malformed instruction row: {exc}")
            continue
        if inst.op != classification.op:
            reasons.append(
                f"line={inst.line} index={index}: malformed instruction row: noncanonical opcode {inst.op!r}"
            )
    logger.debug("malformed_guard_rows exit reasons=%d", len(reasons))
    return tuple(reasons)


def _visible_use_rejection(inst: Instruction, position: int, observer: str) -> str:
    logger.debug("visible_use_rejection entry op=%s position=%d", inst.op, position)
    if inst.op in {"OBSERVE", "COMPRESS"}:
        reason = "" if len(inst.args) == 3 and position == 1 and inst.args[2] == observer else (
            f"{inst.op} is not a same-observer source use"
        )
    elif inst.op == "ECHO":
        reason = "" if len(inst.args) == 4 and position in {1, 2} and inst.args[3] == observer else (
            "ECHO is not a same-observer operand use"
        )
    elif inst.op == "CERT":
        reason = "candidate feeds CERT evidence directly"
    elif inst.op == "OBSTRUCT":
        reason = "candidate crosses an OBSTRUCT evidence boundary"
    else:
        reason = f"unsupported visible use {inst.op}"
    logger.debug("visible_use_rejection exit rejected=%s", bool(reason))
    return reason


def optimizer_theorem_skeleton(
    program_name: str, program: Iterable[Instruction],
) -> OptimizerTheoremSkeleton:
    """Populate bounded executable premises while leaving general proof holes open."""
    rows = _snapshot_program(program)
    logger.debug("optimizer_theorem_skeleton entry name=%s rows=%d", program_name, len(rows))
    report = optimize(rows)
    equivalence = summarize_equivalence(report.original, report.optimized)
    pass_rows = tuple((name, sum(row.pass_name == name for row in report.rows)) for name in PASS_ORDER)
    holds = equivalence.status == "equivalent"
    result = OptimizerTheoremSkeleton(
        program_name, pass_rows, equivalence.status, holds, UNRESOLVED_PREMISES,
    )
    logger.debug(
        "optimizer_theorem_skeleton exit name=%s equivalence=%s decisions=%d",
        program_name, equivalence.status, sum(count for _, count in pass_rows),
    )
    return result


def optimizer_corpus_skeleton(
    programs: Iterable[tuple[str, Iterable[Instruction]]],
) -> tuple[OptimizerTheoremSkeleton, ...]:
    """Build deterministic theorem-skeleton rows for a caller-owned finite corpus."""
    if type(programs) not in (tuple, list) or len(programs) > MAX_CORPUS_ROWS:
        logger.error("optimizer_corpus_skeleton noncanonical or oversized corpus")
        raise ValueError("optimizer corpus requires a bounded exact sequence")
    frozen = tuple((name, _snapshot_program(program)) for name, program in programs)
    logger.debug("optimizer_corpus_skeleton entry programs=%d", len(frozen))
    names = tuple(name for name, _ in frozen)
    if len(set(names)) != len(names):
        logger.error("optimizer_corpus_skeleton duplicate names=%r", names)
        raise ValueError("optimizer corpus names must be unique")
    result = tuple(optimizer_theorem_skeleton(name, program) for name, program in frozen)
    logger.debug("optimizer_corpus_skeleton exit rows=%d", len(result))
    return result


def _snapshot_program(program: Iterable[Instruction]) -> tuple[Instruction, ...]:
    """Snapshot one exact bounded program without consuming open iterators."""
    logger.debug("snapshot_optimizer_program entry type=%s", type(program).__name__)
    if type(program) not in (tuple, list) or len(program) > MAX_PROGRAM_ROWS:
        logger.error("snapshot_optimizer_program noncanonical or oversized program")
        raise ValueError("optimizer program requires a bounded exact sequence")
    rows = tuple(program)
    if any(type(row) is not Instruction for row in rows):
        logger.error("snapshot_optimizer_program noncanonical instruction")
        raise ValueError("optimizer program requires exact instructions")
    logger.debug("snapshot_optimizer_program exit rows=%d", len(rows))
    return rows


def vamd_optimized_emission_policy(*, requested: bool = True) -> VamdEmissionPolicy:
    """Specify gates and reject emission until a native VAMD encoder is integrated."""
    logger.debug("vamd_optimized_emission_policy entry requested=%s", requested)
    gates = (
        "native VAMD encoder with exact opcode/argument validation",
        "optimized IR re-decodes byte-exactly",
        "Python/Rust optimized semantic report parity",
        "malformed-frame and resource-limit regression coverage",
    )
    result = VamdEmissionPolicy(
        requested=requested,
        allowed=False,
        status="blocked" if requested else "not-requested",
        obstruction="native optimized VAMD frame encoder is not integrated",
        required_gates=gates,
    )
    logger.debug("vamd_optimized_emission_policy exit status=%s", result.status)
    return result


__all__ = [
    "BOUNDARY", "CLAIM", "OptimizerTheoremSkeleton", "VamdEmissionPolicy",
    "VisibleUseGuardRow", "optimizer_corpus_skeleton", "optimizer_theorem_skeleton",
    "vamd_optimized_emission_policy", "visible_use_guard",
]

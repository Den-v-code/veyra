"""Isolated symbolic quantified-theorem schema model.

Unlike the legacy finite-case carrier, this module retains a universally
quantified schema as executable symbolic state.  It validates scope and
specialization, but is not wired into VAM opcode/runtime semantics and provides no proof operation.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
from typing import Mapping

logger = logging.getLogger(__name__)
PROFILE = "veyra.vam.quantified-theorem.v1"
BOUNDARY = "symbolic-schema-and-specialization-not-proof"
_IDENTIFIER = re.compile(r"[A-Za-z][A-Za-z0-9_-]*\Z")
MAX_BINDERS = 128
MAX_TEXT_ROWS = 256
MAX_TEXT_BYTES = 4096

@dataclass(frozen=True, slots=True)
class QuantifiedBinder:
    """One universally quantified typed binder."""
    name: str
    kind: str


@dataclass(frozen=True, slots=True)
class QuantifiedTheoremInstruction:
    """Intensional theorem declaration retained without finite enumeration."""
    theorem_id: str
    binders: tuple[QuantifiedBinder, ...]
    assumptions: tuple[str, ...]
    conclusions: tuple[str, ...]
    opcode: str = "DECLARE_FORALL"
    profile: str = PROFILE


@dataclass(frozen=True, slots=True)
class QuantifiedTheoremState:
    """Validated symbolic declaration state; never a proof certificate."""
    instruction: QuantifiedTheoremInstruction
    status: str
    free_variables: tuple[str, ...]
    canonical_text: str
    proof_status: str = "open"
    boundary: str = BOUNDARY


@dataclass(frozen=True, slots=True)
class TheoremSpecialization:
    """Capture-safe total specialization of one symbolic declaration."""
    theorem_id: str
    assignments: tuple[tuple[str, str], ...]
    assumptions: tuple[str, ...]
    conclusions: tuple[str, ...]
    status: str = "instantiated-open"
    proof_status: str = "open"
    boundary: str = BOUNDARY


@dataclass(frozen=True, slots=True)
class NativeParityBoundary:
    """Exact executable parity surface and the missing proof-grade bridge."""
    parity_surfaces: tuple[str, ...]
    status: str
    proof_grade: bool
    obstruction: str
    required_formal_gates: tuple[str, ...]
    boundary: str = "quantified-theorem-native-parity-boundary"


def declare_quantified_theorem(
    theorem_id: str,
    binders: tuple[QuantifiedBinder, ...],
    assumptions: tuple[str, ...],
    conclusions: tuple[str, ...],
) -> QuantifiedTheoremState:
    """Validate and retain a symbolic universal theorem declaration."""
    logger.debug("declare_quantified_theorem entry theorem=%r binders_type=%s", theorem_id, type(binders).__name__)
    instruction = QuantifiedTheoremInstruction(theorem_id, binders, assumptions, conclusions)
    _validate_instruction(instruction)
    canonical = canonical_quantified_instruction(instruction)
    result = QuantifiedTheoremState(instruction, "well-formed-open", (), canonical)
    logger.debug("declare_quantified_theorem exit theorem=%s status=%s", theorem_id, result.status)
    return result


def canonical_quantified_instruction(instruction: QuantifiedTheoremInstruction) -> str:
    """Return a language-neutral deterministic representation for native parity."""
    logger.debug("canonical_quantified_instruction entry type=%s", type(instruction).__name__)
    _validate_instruction(instruction)
    body = {
        "assumptions": list(instruction.assumptions),
        "binders": [{"kind": row.kind, "name": row.name} for row in instruction.binders],
        "conclusions": list(instruction.conclusions),
        "opcode": instruction.opcode,
        "profile": instruction.profile,
        "theorem_id": instruction.theorem_id,
    }
    result = json.dumps(body, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    logger.debug("canonical_quantified_instruction exit theorem=%s bytes=%d", instruction.theorem_id, len(result.encode()))
    return result


def specialize_quantified_theorem(
    state: QuantifiedTheoremState, assignments: Mapping[str, str],
) -> TheoremSpecialization:
    """Instantiate binders with exact ``kind:atom`` values, without proving them."""
    logger.debug("specialize_quantified_theorem entry state_type=%s", type(state).__name__)
    if type(state) is not QuantifiedTheoremState or type(state.instruction) is not QuantifiedTheoremInstruction:
        logger.error("specialize_quantified_theorem noncanonical state")
        raise ValueError("noncanonical quantified theorem state")
    _validate_instruction(state.instruction)
    expected_canonical = canonical_quantified_instruction(state.instruction)
    if (
        state.status != "well-formed-open"
        or state.proof_status != "open"
        or state.canonical_text != expected_canonical
    ):
        logger.error("specialize_quantified_theorem invalid state status=%s", state.status)
        raise ValueError("quantified theorem state is not an open declaration")
    if type(assignments) is not dict:
        logger.error("specialize_quantified_theorem noncanonical assignment mapping")
        raise ValueError("invalid specialization assignment mapping")
    snapshot = assignments.copy()
    if any(type(name) is not str or len(name.encode()) > MAX_TEXT_BYTES for name in snapshot):
        logger.error("specialize_quantified_theorem invalid assignment key")
        raise ValueError("invalid specialization assignment mapping")
    names = tuple(row.name for row in state.instruction.binders)
    extra = tuple(sorted(set(snapshot) - set(names)))
    missing = tuple(name for name in names if name not in snapshot)
    if missing or extra:
        logger.error("specialize_quantified_theorem assignment mismatch missing=%r extra=%r", missing, extra)
        raise ValueError(f"specialization assignment mismatch: missing={missing}, extra={extra}")
    stable: list[tuple[str, str]] = []
    for binder in state.instruction.binders:
        name = binder.name
        value = snapshot[name]
        _validate_typed_atom(name, binder.kind, value)
        stable.append((name, value))
    mapping = dict(stable)
    assumptions = tuple(_substitute(row, mapping) for row in state.instruction.assumptions)
    conclusions = tuple(_substitute(row, mapping) for row in state.instruction.conclusions)
    result = TheoremSpecialization(state.instruction.theorem_id, tuple(stable), assumptions, conclusions)
    logger.debug("specialize_quantified_theorem exit theorem=%s", result.theorem_id)
    return result


def native_quantified_parity_boundary() -> NativeParityBoundary:
    """Report executable parity while refusing a proof-grade correspondence claim."""
    logger.debug("native_quantified_parity_boundary entry")
    result = NativeParityBoundary(
        parity_surfaces=("validation", "canonical-text", "total-specialization"),
        status="bounded-executable-parity",
        proof_grade=False,
        obstruction="no checked Python/Rust correspondence theorem or integrated native instruction",
        required_formal_gates=(
            "formal schema semantics",
            "source-bound Python refinement theorem",
            "source-bound Rust refinement theorem",
            "toolchain-bound cross-language correspondence",
        ),
    )
    logger.debug("native_quantified_parity_boundary exit proof_grade=%s", result.proof_grade)
    return result


def _validate_instruction(instruction: QuantifiedTheoremInstruction) -> None:
    logger.debug("validate_quantified_instruction entry theorem=%s", instruction.theorem_id)
    if type(instruction) is not QuantifiedTheoremInstruction:
        logger.error("validate_quantified_instruction noncanonical instruction")
        raise ValueError("noncanonical quantified theorem instruction")
    if (
        type(instruction.opcode) is not str
        or type(instruction.profile) is not str
        or instruction.opcode != "DECLARE_FORALL"
        or instruction.profile != PROFILE
    ):
        logger.error("validate_quantified_instruction bad envelope")
        raise ValueError("unsupported quantified theorem instruction envelope")
    if (
        type(instruction.theorem_id) is not str
        or len(instruction.theorem_id.encode()) > MAX_TEXT_BYTES
        or not _IDENTIFIER.fullmatch(instruction.theorem_id)
    ):
        logger.error("validate_quantified_instruction bad theorem id=%r", instruction.theorem_id)
        raise ValueError("invalid quantified theorem id")
    if (
        type(instruction.binders) is not tuple
        or type(instruction.assumptions) is not tuple
        or type(instruction.conclusions) is not tuple
        or any(type(row) is not QuantifiedBinder for row in instruction.binders)
    ):
        logger.error("validate_quantified_instruction mutable or noncanonical fields")
        raise ValueError("noncanonical quantified theorem fields")
    if (
        not instruction.binders
        or len(instruction.binders) > MAX_BINDERS
        or not instruction.conclusions
        or len(instruction.assumptions) + len(instruction.conclusions) > MAX_TEXT_ROWS
    ):
        logger.error("validate_quantified_instruction empty binders/conclusions")
        raise ValueError("quantified theorem requires binders and conclusions")
    names = tuple(row.name for row in instruction.binders)
    if len(set(names)) != len(names):
        logger.error("validate_quantified_instruction duplicate binders=%r", names)
        raise ValueError("duplicate quantified binder")
    if any(
        type(row.name) is not str
        or type(row.kind) is not str
        or len(row.name.encode()) > MAX_TEXT_BYTES
        or len(row.kind.encode()) > MAX_TEXT_BYTES
        or not _IDENTIFIER.fullmatch(row.name)
        or not _IDENTIFIER.fullmatch(row.kind)
        for row in instruction.binders
    ):
        logger.error("validate_quantified_instruction invalid binder")
        raise ValueError("invalid quantified binder")
    texts = instruction.assumptions + instruction.conclusions
    if any(type(text) is not str or len(text.encode()) > MAX_TEXT_BYTES for text in texts):
        logger.error("validate_quantified_instruction invalid or oversized text")
        raise ValueError("invalid quantified theorem text")
    try:
        referenced = {name for text in texts for name in _placeholder_names(text)}
    except ValueError:
        logger.error("validate_quantified_instruction invalid placeholder")
        raise
    free = tuple(sorted(referenced - set(names)))
    if free:
        logger.error("validate_quantified_instruction free variables=%r", free)
        raise ValueError(f"free quantified variables: {free}")
    logger.debug("validate_quantified_instruction exit theorem=%s", instruction.theorem_id)


def _validate_typed_atom(name: str, expected_kind: str, value: object) -> None:
    logger.debug("validate_typed_atom entry binder=%s expected_kind=%s", name, expected_kind)
    if type(value) is not str or len(value.encode()) > MAX_TEXT_BYTES:
        logger.error("validate_typed_atom invalid value binder=%s", name)
        raise ValueError(f"unsafe specialization value for {name}")
    kind, separator, atom = value.partition(":")
    if separator != ":" or kind != expected_kind or not _is_identifier(atom):
        logger.error("validate_typed_atom kind/syntax mismatch binder=%s", name)
        raise ValueError(f"typed specialization mismatch for {name}: expected {expected_kind}:atom")
    logger.debug("validate_typed_atom exit binder=%s", name)


def _placeholder_names(text: str) -> tuple[str, ...]:
    names: list[str] = []
    index = 0
    while index < len(text):
        if text[index] != "$":
            index += 1
            continue
        end = index + 1
        while end < len(text) and (text[end].isascii() and (text[end].isalnum() or text[end] in "_-")):
            end += 1
        name = text[index + 1:end]
        if not _is_identifier(name):
            raise ValueError("invalid quantified placeholder")
        names.append(name)
        index = end
    return tuple(names)


def _substitute(template: str, assignments: Mapping[str, str]) -> str:
    logger.debug("substitute_quantified_template entry bytes=%d", len(template.encode()))
    parts: list[str] = []
    used_bytes = 0
    cursor = 0
    for name in _placeholder_names(template):
        marker = f"${name}"
        start = template.index(marker, cursor)
        for part in (template[cursor:start], assignments[name]):
            used_bytes += len(part.encode())
            if used_bytes > MAX_TEXT_BYTES:
                logger.error("substitute_quantified_template output exceeds bound")
                raise ValueError("specialized theorem text exceeds resource bound")
            parts.append(part)
        cursor = start + len(marker)
    tail = template[cursor:]
    if used_bytes + len(tail.encode()) > MAX_TEXT_BYTES:
        logger.error("substitute_quantified_template output exceeds bound")
        raise ValueError("specialized theorem text exceeds resource bound")
    result = "".join((*parts, tail))
    logger.debug("substitute_quantified_template exit bytes=%d", len(result.encode()))
    return result


def _is_identifier(value: str) -> bool:
    return bool(value) and len(value.encode()) <= MAX_TEXT_BYTES and _IDENTIFIER.fullmatch(value) is not None


__all__ = [
    "BOUNDARY", "PROFILE", "NativeParityBoundary", "QuantifiedBinder", "QuantifiedTheoremInstruction",
    "QuantifiedTheoremState", "TheoremSpecialization", "canonical_quantified_instruction",
    "declare_quantified_theorem", "native_quantified_parity_boundary", "specialize_quantified_theorem",
]

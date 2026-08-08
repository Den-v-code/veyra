"""Dense opcode metadata groundwork for current VAM instructions.

This module is metadata only. It validates and classifies existing
``Instruction`` rows; it does not encode dense bytecode and is not wired into
the assembler, VAM0 JSON frame, optimizer, or interpreter.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Iterable

from .model import Instruction

logger = logging.getLogger(__name__)

DEST_REG = "dest_reg"
REG = "reg"
LITERAL = "literal"
LABEL = "label"
OBSERVER_KIND = "observer_kind"
CLAIM = "claim"
BOUNDARY = "boundary"
OperandClass = str


class OpcodeValidationError(ValueError):
    """Raised when an instruction row does not match opcode metadata."""


@dataclass(frozen=True)
class Arity:
    """Total operand count, including the destination register."""

    minimum: int
    maximum: int | None = None

    def accepts(self, count: int) -> bool:
        """Return true when count is inside this arity range."""
        logger.debug("arity accepts entry count=%d min=%d max=%s", count, self.minimum, self.maximum)
        result = count >= self.minimum and (self.maximum is None or count <= self.maximum)
        logger.debug("arity accepts exit result=%s", result)
        return result

    def to_row(self) -> dict[str, int | None]:
        """Return deterministic row form for metadata round-trips."""
        return {"min": self.minimum, "max": self.maximum}

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Arity":
        """Load arity metadata from row form."""
        minimum, maximum = row.get("min"), row.get("max")
        if not isinstance(minimum, int) or not (maximum is None or isinstance(maximum, int)):
            raise OpcodeValidationError(f"bad arity row: {row!r}")
        return cls(minimum, maximum)


@dataclass(frozen=True)
class OpcodeSpec:
    """Stable dense opcode metadata for one current VAM operation."""

    name: str
    code: int
    arity: Arity
    operand_classes: tuple[OperandClass, ...]
    side_effect: bool = False
    certificate: bool = False
    obstruction: bool = False

    def expanded_classes(self, count: int) -> tuple[OperandClass, ...]:
        """Expand operand classes for a concrete row length."""
        logger.debug("opcode expanded_classes entry op=%s count=%d", self.name, count)
        if not self.arity.accepts(count):
            raise OpcodeValidationError(_arity_message(self.name, self.arity, count))
        if len(self.operand_classes) == count:
            result = self.operand_classes
        elif self.arity.maximum is None and count >= len(self.operand_classes):
            result = self.operand_classes + (self.operand_classes[-1],) * (count - len(self.operand_classes))
        else:
            raise OpcodeValidationError(_arity_message(self.name, self.arity, count))
        logger.debug("opcode expanded_classes exit op=%s classes=%s", self.name, result)
        return result

    def to_row(self) -> dict[str, Any]:
        """Return deterministic row form for metadata round-trips."""
        return {
            "name": self.name,
            "code": self.code,
            "arity": self.arity.to_row(),
            "operand_classes": list(self.operand_classes),
            "side_effect": self.side_effect,
            "certificate": self.certificate,
            "obstruction": self.obstruction,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "OpcodeSpec":
        """Load opcode metadata from deterministic row form."""
        try:
            name, code = row["name"], row["code"]
            operand_classes = tuple(row["operand_classes"])
        except KeyError as exc:
            raise OpcodeValidationError(f"missing opcode metadata field: {exc.args[0]}") from exc
        if not isinstance(name, str) or not isinstance(code, int):
            raise OpcodeValidationError(f"bad opcode identity row: {row!r}")
        if not all(isinstance(item, str) for item in operand_classes):
            raise OpcodeValidationError(f"bad operand class row: {row!r}")
        return cls(
            name.upper(),
            code,
            Arity.from_row(row["arity"]),
            operand_classes,
            bool(row.get("side_effect", False)),
            bool(row.get("certificate", False)),
            bool(row.get("obstruction", False)),
        )


@dataclass(frozen=True)
class InstructionClassification:
    """Validated metadata view of one existing Instruction row."""

    op: str
    code: int
    line: int
    arity: int
    operand_classes: tuple[OperandClass, ...]
    side_effect: bool
    certificate: bool
    obstruction: bool

    def to_row(self) -> dict[str, Any]:
        """Return deterministic row form for tests and diagnostics."""
        return {
            "op": self.op,
            "code": self.code,
            "line": self.line,
            "arity": self.arity,
            "operand_classes": list(self.operand_classes),
            "side_effect": self.side_effect,
            "certificate": self.certificate,
            "obstruction": self.obstruction,
        }


_OPCODE_SPECS = (
    OpcodeSpec("REZ", 0x01, Arity(2, 2), (DEST_REG, LABEL)),
    OpcodeSpec("NOD", 0x02, Arity(3, 3), (DEST_REG, REG, LABEL)),
    OpcodeSpec("TACT", 0x03, Arity(4, 4), (DEST_REG, REG, REG, LABEL)),
    OpcodeSpec("BREATH", 0x04, Arity(2, None), (DEST_REG, REG)),
    OpcodeSpec("MODE", 0x05, Arity(2, 2), (DEST_REG, REG)),
    OpcodeSpec("OBSERVER", 0x06, Arity(2, 2), (DEST_REG, OBSERVER_KIND)),
    OpcodeSpec("OBSERVE", 0x07, Arity(3, 3), (DEST_REG, REG, REG)),
    OpcodeSpec("ECHO", 0x08, Arity(4, 4), (DEST_REG, REG, REG, REG), side_effect=True),
    OpcodeSpec("OBSTRUCT", 0x09, Arity(3, 3), (DEST_REG, CLAIM, REG), side_effect=True, obstruction=True),
    OpcodeSpec("COMPRESS", 0x0A, Arity(3, 3), (DEST_REG, REG, REG)),
    OpcodeSpec("CERT", 0x0B, Arity(4, 4), (DEST_REG, CLAIM, REG, BOUNDARY), side_effect=True, certificate=True),
)

OPCODES_BY_NAME = {spec.name: spec for spec in _OPCODE_SPECS}
OPCODES_BY_CODE = {spec.code: spec for spec in _OPCODE_SPECS}


def opcode_table() -> tuple[OpcodeSpec, ...]:
    """Return the stable dense opcode metadata table in code order."""
    return _OPCODE_SPECS


def opcode_rows() -> tuple[dict[str, Any], ...]:
    """Return deterministic serializable metadata rows."""
    return tuple(spec.to_row() for spec in _OPCODE_SPECS)


def opcode_table_from_rows(rows: Iterable[dict[str, Any]]) -> tuple[OpcodeSpec, ...]:
    """Load opcode metadata rows and enforce name/code uniqueness."""
    logger.debug("opcode_table_from_rows entry")
    specs = tuple(OpcodeSpec.from_row(row) for row in rows)
    _require_unique((spec.name for spec in specs), "opcode name")
    _require_unique((spec.code for spec in specs), "opcode code")
    logger.debug("opcode_table_from_rows exit specs=%d", len(specs))
    return specs


def get_opcode(op: str) -> OpcodeSpec:
    """Return opcode metadata by mnemonic, rejecting unknown operations."""
    logger.debug("get_opcode entry op=%s", op)
    try:
        result = OPCODES_BY_NAME[op.upper()]
    except KeyError as exc:
        logger.error("get_opcode unknown op=%s", op)
        raise OpcodeValidationError(f"unknown VAM opcode: {op}") from exc
    logger.debug("get_opcode exit op=%s code=%d", result.name, result.code)
    return result


def classify_instruction(inst: Instruction) -> InstructionClassification:
    """Validate and classify one existing Instruction row against metadata."""
    logger.debug("classify_instruction entry op=%s line=%d argc=%d", inst.op, inst.line, len(inst.args))
    spec = get_opcode(inst.op)
    classes = spec.expanded_classes(len(inst.args))
    for index, (arg, operand_class) in enumerate(zip(inst.args, classes), start=1):
        if not _matches_class(arg, operand_class):
            raise OpcodeValidationError(
                f"line {inst.line}: {spec.name} operand {index} expected {operand_class}, got {arg!r}"
            )
    result = InstructionClassification(
        spec.name,
        spec.code,
        inst.line,
        len(inst.args),
        classes,
        spec.side_effect,
        spec.certificate,
        spec.obstruction,
    )
    logger.debug("classify_instruction exit op=%s code=%d", result.op, result.code)
    return result


def validate_instruction(inst: Instruction) -> None:
    """Raise if an Instruction row does not match current opcode metadata."""
    classify_instruction(inst)


def classify_program(program: Iterable[Instruction]) -> tuple[InstructionClassification, ...]:
    """Validate and classify a program without executing or re-encoding it."""
    program = tuple(program)
    logger.debug("classify_program entry instructions=%d", len(program))
    result = tuple(classify_instruction(inst) for inst in program)
    logger.debug("classify_program exit classifications=%d", len(result))
    return result


def _matches_class(arg: Any, operand_class: OperandClass) -> bool:
    if operand_class in {DEST_REG, REG}:
        return _is_register(arg)
    if operand_class == LITERAL:
        return _is_literal(arg)
    if operand_class in {LABEL, OBSERVER_KIND, CLAIM, BOUNDARY}:
        return isinstance(arg, str) and not _is_register(arg)
    return False


def _is_register(arg: Any) -> bool:
    return isinstance(arg, str) and arg.startswith("%r") and arg[2:].isdigit()


def _is_literal(arg: Any) -> bool:
    return type(arg) is int or (isinstance(arg, str) and not _is_register(arg))


def _arity_message(op: str, arity: Arity, count: int) -> str:
    expected = f">={arity.minimum}" if arity.maximum is None else str(arity.minimum)
    return f"{op} expected {expected} operands, got {count}"


def _require_unique(values: Iterable[object], label: str) -> None:
    seen: set[object] = set()
    for value in values:
        if value in seen:
            raise OpcodeValidationError(f"duplicate {label}: {value!r}")
        seen.add(value)

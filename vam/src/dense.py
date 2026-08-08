"""Dense VAM bytecode frame encoder/decoder."""
from __future__ import annotations

from collections.abc import Iterable
import logging
import struct
import zlib

from .model import Instruction
from .opcodes import OPCODES_BY_CODE, OpcodeValidationError, get_opcode

logger = logging.getLogger(__name__)

DENSE_MAGIC = b"VAMD"
DENSE_VERSION = 1
_HEADER = struct.Struct(">4sHII")
_U8 = struct.Struct(">B")
_U16 = struct.Struct(">H")
_U32 = struct.Struct(">I")
_I64 = struct.Struct(">q")


class DenseBytecodeError(ValueError):
    """Raised when a dense VAM frame is malformed."""


def _is_register(arg: object) -> bool:
    return isinstance(arg, str) and arg.startswith("%r") and arg[2:].isdigit()


def _fail(message: str, exc: Exception | None = None) -> None:
    logger.error("dense error: %s", message)
    raise DenseBytecodeError(message) from exc


def _require_size(blob: memoryview, pos: int, size: int, label: str) -> None:
    if pos + size > len(blob):
        _fail(f"dense truncated {label}")


def _read(blob: memoryview, pos: int, fmt: struct.Struct, label: str) -> tuple[int, int]:
    _require_size(blob, pos, fmt.size, label)
    return fmt.unpack_from(blob, pos)[0], pos + fmt.size


def _validate_arg(op: str, line: int, operand_class: str, arg: object, index: int) -> bytes:
    if operand_class in {"dest_reg", "reg"}:
        if not _is_register(arg):
            _fail(f"line {line}: opcode {op} register argument {index} expected register, got {arg!r}")
        reg = int(arg[2:])
        if reg > 0xFFFF:
            _fail(f"line {line}: opcode {op} register argument {index} out of range: {arg!r}")
        return _U8.pack(1) + _U16.pack(reg)
    if operand_class == "literal":
        if type(arg) is int:
            return _U8.pack(2) + _I64.pack(arg)
        if isinstance(arg, str) and not _is_register(arg):
            data = arg.encode("utf-8")
            if len(data) > 0xFFFF:
                _fail(f"line {line}: opcode {op} string argument {index} too long")
            return _U8.pack(3) + _U16.pack(len(data)) + data
        _fail(f"line {line}: opcode {op} argument {index} expected int or string, got {arg!r}")
    if operand_class in {"label", "observer_kind", "claim", "boundary"}:
        if not isinstance(arg, str) or _is_register(arg):
            _fail(f"line {line}: opcode {op} string argument {index} expected string, got {arg!r}")
        data = arg.encode("utf-8")
        if len(data) > 0xFFFF:
            _fail(f"line {line}: opcode {op} string argument {index} too long")
        return _U8.pack(3) + _U16.pack(len(data)) + data
    _fail(f"line {line}: opcode {op} argument {index} unsupported metadata class {operand_class!r}")


def _encode_instruction(inst: Instruction) -> bytes:
    try:
        spec = get_opcode(inst.op)
        classes = spec.expanded_classes(len(inst.args))
    except OpcodeValidationError as exc:
        msg = str(exc)
        if "operands" in msg or "arity" in msg:
            _fail(f"line {inst.line}: arity error for opcode {inst.op}: {msg}", exc)
        _fail(f"line {inst.line}: opcode error for {inst.op}: {msg}", exc)
    payload = bytearray()
    payload += _U8.pack(spec.code)
    line = int(inst.line)
    if not 0 <= line <= 0xFFFFFFFF:
        _fail(f"line {inst.line}: opcode {spec.name} line out of range: {line}")
    payload += _U32.pack(line)
    payload += _U8.pack(len(inst.args))
    for index, (arg, operand_class) in enumerate(zip(inst.args, classes), start=1):
        payload += _validate_arg(spec.name, line, operand_class, arg, index)
    return bytes(payload)


def encode_dense(program: Iterable[Instruction]) -> bytes:
    """Encode a validated instruction program into a dense frame."""
    program = list(program)
    logger.debug("encode_dense entry instructions=%d", len(program))
    if len(program) > 0xFFFF:
        _fail(f"instruction_count out of range: {len(program)}")
    payload = bytearray(_U16.pack(len(program)))
    for inst in program:
        payload += _encode_instruction(inst)
    if len(payload) > 0xFFFFFFFF:
        _fail(f"payload length out of range: {len(payload)}")
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    frame = _HEADER.pack(DENSE_MAGIC, DENSE_VERSION, len(payload), checksum) + payload
    logger.debug("encode_dense exit bytes=%d checksum=%08x", len(frame), checksum)
    return frame


def _decode_arg(blob: memoryview, pos: int, label: str) -> tuple[object, int]:
    tag, pos = _read(blob, pos, _U8, f"argument tag ({label})")
    if tag == 1:
        reg, pos = _read(blob, pos, _U16, "register")
        return f"%r{reg}", pos
    if tag == 2:
        value, pos = _read(blob, pos, _I64, "argument")
        return value, pos
    if tag == 3:
        size, pos = _read(blob, pos, _U16, "string length")
        _require_size(blob, pos, size, "string")
        try:
            return blob[pos : pos + size].tobytes().decode("utf-8"), pos + size
        except UnicodeDecodeError as exc:
            _fail("dense string decode failed", exc)
    _fail(f"invalid argument tag: {tag}")


def _validate_decoded(spec_name: str, line: int, args: tuple[object, ...]) -> None:
    spec = get_opcode(spec_name)
    try:
        classes = spec.expanded_classes(len(args))
    except OpcodeValidationError as exc:
        _fail(f"line {line}: arity error for opcode {spec.name}: {exc}", exc)
    for index, (arg, operand_class) in enumerate(zip(args, classes), start=1):
        if operand_class in {"dest_reg", "reg"} and not _is_register(arg):
            _fail(f"line {line}: opcode {spec.name} register argument {index} expected register, got {arg!r}")
        if operand_class == "literal" and not (type(arg) is int or (isinstance(arg, str) and not _is_register(arg))):
            _fail(f"line {line}: opcode {spec.name} argument {index} expected int or string, got {arg!r}")
        if operand_class in {"label", "observer_kind", "claim", "boundary"} and (
            not isinstance(arg, str) or _is_register(arg)
        ):
            _fail(f"line {line}: opcode {spec.name} string argument {index} expected string, got {arg!r}")


def decode_dense(blob: bytes | bytearray | memoryview) -> list[Instruction]:
    """Decode a dense frame back into instruction IR."""
    view = memoryview(blob)
    logger.debug("decode_dense entry bytes=%d", len(view))
    if len(view) < _HEADER.size:
        _fail("dense truncated header")
    magic, version, payload_len, checksum = _HEADER.unpack_from(view, 0)
    if magic != DENSE_MAGIC:
        _fail(f"dense magic mismatch: {magic!r}")
    if version != DENSE_VERSION:
        _fail(f"dense version mismatch: {version}")
    total = _HEADER.size + payload_len
    if len(view) < total:
        _fail("dense truncated payload")
    if len(view) > total:
        _fail("dense length mismatch")
    payload = view[_HEADER.size : total].tobytes()
    if zlib.crc32(payload) & 0xFFFFFFFF != checksum:
        _fail("dense checksum mismatch")
    pview = memoryview(payload)
    pos = 0
    count, pos = _read(pview, pos, _U16, "instruction count")
    program: list[Instruction] = []
    for _ in range(count):
        opcode_code, pos = _read(pview, pos, _U8, "opcode")
        line, pos = _read(pview, pos, _U32, "line")
        argc, pos = _read(pview, pos, _U8, "arity")
        try:
            spec = OPCODES_BY_CODE[opcode_code]
        except KeyError as exc:
            _fail(f"unknown opcode code: {opcode_code}", exc)
        args: list[object] = []
        for i in range(argc):
            arg, pos = _decode_arg(pview, pos, f"{spec.name}:{i + 1}")
            args.append(arg)
        _validate_decoded(spec.name, line, tuple(args))
        program.append(Instruction(spec.name, tuple(args), line))
    if pos != len(pview):
        _fail("dense length mismatch")
    logger.debug("decode_dense exit instructions=%d", len(program))
    return program


def dense_round_trip(program: Iterable[Instruction]) -> list[Instruction]:
    """Encode and decode a program using the dense frame format."""
    program = list(program)
    logger.debug("dense_round_trip entry instructions=%d", len(program))
    result = decode_dense(encode_dense(program))
    logger.debug("dense_round_trip exit instructions=%d", len(result))
    return result


__all__ = [
    "DENSE_MAGIC",
    "DENSE_VERSION",
    "DenseBytecodeError",
    "decode_dense",
    "dense_round_trip",
    "encode_dense",
]

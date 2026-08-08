"""Binary VAM0 frame encoder/decoder for Instruction IR."""
from __future__ import annotations

import json
import logging
import struct
import zlib
from pathlib import Path
from typing import Any, Iterable

from .model import Instruction

logger = logging.getLogger(__name__)
MAGIC = b"VAM0"
VERSION = 1
_HEADER = struct.Struct(">4sHII")


class VamBytecodeError(ValueError):
    """Raised when a binary VAM0 frame is malformed."""


def _arg_to_wire(arg: Any) -> dict[str, Any]:
    if isinstance(arg, int):
        return {"t": "int", "v": arg}
    if isinstance(arg, str) and arg.startswith("%r") and arg[2:].isdigit():
        return {"t": "reg", "v": int(arg[2:])}
    if isinstance(arg, str):
        return {"t": "str", "v": arg}
    raise VamBytecodeError(f"unsupported argument type: {type(arg).__name__}")


def _arg_from_wire(item: dict[str, Any]) -> Any:
    tag = item.get("t")
    value = item.get("v")
    if tag == "int" and isinstance(value, int):
        return value
    if tag == "reg" and isinstance(value, int) and value >= 0:
        return f"%r{value}"
    if tag == "str" and isinstance(value, str):
        return value
    raise VamBytecodeError(f"bad argument item: {item!r}")


def _program_to_payload(program: Iterable[Instruction]) -> bytes:
    rows = [
        {"op": inst.op, "args": [_arg_to_wire(arg) for arg in inst.args], "line": int(inst.line)}
        for inst in program
    ]
    return json.dumps(rows, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _payload_to_program(payload: bytes) -> list[Instruction]:
    try:
        rows = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VamBytecodeError("bad VAM0 payload") from exc
    if not isinstance(rows, list):
        raise VamBytecodeError("VAM0 payload must be a list")
    program = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("op"), str) or not isinstance(row.get("args"), list):
            raise VamBytecodeError(f"bad instruction row: {row!r}")
        args = tuple(_arg_from_wire(item) for item in row["args"])
        program.append(Instruction(row["op"].upper(), args, int(row.get("line", 0))))
    return program


def encode_vmbc(program: Iterable[Instruction]) -> bytes:
    """Encode instruction IR into a VAM0 binary frame."""
    program = list(program)
    logger.debug("encode_vmbc entry instructions=%d", len(program))
    payload = _program_to_payload(program)
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    frame = _HEADER.pack(MAGIC, VERSION, len(payload), checksum) + payload
    logger.debug("encode_vmbc exit bytes=%d checksum=%08x", len(frame), checksum)
    return frame


def decode_vmbc(blob: bytes) -> list[Instruction]:
    """Decode a VAM0 binary frame back into instruction IR."""
    logger.debug("decode_vmbc entry bytes=%d", len(blob))
    if len(blob) < _HEADER.size:
        raise VamBytecodeError("short VAM0 frame")
    magic, version, size, checksum = _HEADER.unpack(blob[: _HEADER.size])
    if magic != MAGIC:
        raise VamBytecodeError("bad VAM0 magic")
    if version != VERSION:
        raise VamBytecodeError(f"unsupported VAM0 version: {version}")
    payload = blob[_HEADER.size :]
    if len(payload) != size:
        raise VamBytecodeError("VAM0 payload length mismatch")
    if (zlib.crc32(payload) & 0xFFFFFFFF) != checksum:
        raise VamBytecodeError("VAM0 checksum mismatch")
    program = _payload_to_program(payload)
    logger.debug("decode_vmbc exit instructions=%d", len(program))
    return program


def write_vmbc(path: str | Path, program: Iterable[Instruction]) -> None:
    """Write a VAM0 binary frame to disk."""
    logger.debug("write_vmbc entry path=%s", path)
    data = encode_vmbc(program)
    Path(path).write_bytes(data)
    logger.debug("write_vmbc exit bytes=%d", len(data))


def read_vmbc(path: str | Path) -> list[Instruction]:
    """Read a VAM0 binary frame from disk."""
    logger.debug("read_vmbc entry path=%s", path)
    program = decode_vmbc(Path(path).read_bytes())
    logger.debug("read_vmbc exit instructions=%d", len(program))
    return program

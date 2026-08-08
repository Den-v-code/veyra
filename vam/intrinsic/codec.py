"""Canonical bounded binary codec for the isolated R12.2 intrinsic IR."""

from __future__ import annotations
import logging
import struct
import zlib
from typing import NoReturn
from vam.src.intrinsic_ir import IntrinsicIRError, validate_intrinsic_ir
from vam.src.intrinsic_ir_types import (
    IntrinsicAnchorIR,
    IntrinsicBlockedIR,
    IntrinsicDomainBlockedIR,
    IntrinsicEchoIR,
    IntrinsicIR,
    IntrinsicMarkIR,
    IntrinsicMarkValueIR,
    IntrinsicMismatchIR,
    IntrinsicObstructionCodeIR,
    IntrinsicObstructionIR,
    IntrinsicPairValueIR,
    IntrinsicPathStepIR,
    IntrinsicReadyIR,
    IntrinsicRecurrenceIR,
    IntrinsicRecurrenceValueIR,
    IntrinsicTactIR,
)
from .validation import decoded_semantic_error

logger = logging.getLogger(__name__)
INTRINSIC_PROFILE = "veyra.vami.intrinsic-r12.4.v1"
MAGIC = b"VAMI"
VERSION = 1
MAX_PAYLOAD_BYTES = 1024 * 1024
MAX_NODES = 4096
MAX_DEPTH = 128
MAX_TACTS = 2047
MAX_OBSTRUCTIONS = 2048
MAX_PATH, _HEADER = 128, struct.Struct(">4sHII")
_STEPS = tuple(IntrinsicPathStepIR)
class IntrinsicCodecError(ValueError):
    """A stable fail-closed VAMI codec rejection."""

    def __init__(self, kind: str, message: str) -> None:
        logger.debug("IntrinsicCodecError.__init__ entry kind=%s", kind)
        self.kind = kind
        super().__init__(message)
        logger.debug("IntrinsicCodecError.__init__ exit")


def _fail(kind: str, message: str) -> NoReturn:
    """Log and raise one stable codec error."""
    logger.error("VAMI codec rejected kind=%s message=%s", kind, message)
    raise IntrinsicCodecError(kind, message)


def _obstruction_body(value: IntrinsicObstructionIR) -> bytes:
    """Encode one already validated obstruction body."""
    logger.debug("_obstruction_body entry path=%d", len(value.path))
    result = b"\x00" + struct.pack(">H", len(value.path)) + bytes(_STEPS.index(step) for step in value.path)
    logger.debug("_obstruction_body exit bytes=%d", len(result))
    return result


def _payload(value: IntrinsicIR) -> bytes:
    """Encode one already validated intrinsic node."""
    logger.debug("_payload entry type=%s", type(value).__name__)
    if type(value) is IntrinsicAnchorIR:
        result = b"\x01"
    elif type(value) is IntrinsicTactIR:
        result = b"\x02"
    elif type(value) is IntrinsicRecurrenceIR:
        result = b"\x03" + struct.pack(">H", len(value.tacts)) + bytes((value.anchor is not None,))
    elif type(value) is IntrinsicMarkIR:
        result = b"\x04" + bytes((value is IntrinsicMarkIR.PULSE,))
    elif type(value) is IntrinsicRecurrenceValueIR:
        result = b"\x05" + _payload(value.recurrence)
    elif type(value) is IntrinsicMarkValueIR:
        result = b"\x06" + bytes((value.mark is IntrinsicMarkIR.PULSE,))
    elif type(value) is IntrinsicPairValueIR:
        result = b"\x07" + _payload(value.left) + _payload(value.right)
    elif type(value) is IntrinsicObstructionIR:
        result = b"\x08" + _obstruction_body(value)
    elif type(value) is IntrinsicReadyIR:
        result = b"\x09" + _payload(value.value)
    elif type(value) is IntrinsicBlockedIR:
        result = b"\x0a" + struct.pack(">H", len(value.obstructions))
        result += b"".join(b"\x08" + _obstruction_body(item) for item in value.obstructions)
    elif type(value) is IntrinsicEchoIR:
        result = b"\x0b" + _payload(value.value)
    elif type(value) is IntrinsicMismatchIR:
        result = b"\x0c" + _payload(value.left) + _payload(value.right)
    elif type(value) is IntrinsicDomainBlockedIR:
        result = b"\x0d" + struct.pack(">H", len(value.left))
        result += b"".join(b"\x08" + _obstruction_body(item) for item in value.left)
        result += struct.pack(">H", len(value.right))
        result += b"".join(b"\x08" + _obstruction_body(item) for item in value.right)
    else:
        _fail("payload", "invalid intrinsic node")
    logger.debug("_payload exit bytes=%d", len(result))
    return result


def encode_intrinsic_frame(value: object) -> bytes:
    """Encode only an exact validated R12.2 IR value as one VAMI frame."""
    logger.debug("encode_intrinsic_frame entry type=%s", type(value).__name__)
    try:
        exact = validate_intrinsic_ir(value)
    except IntrinsicIRError as error:
        _fail("payload", str(error))
    payload = _payload(exact)
    if len(payload) > MAX_PAYLOAD_BYTES:
        _fail("resource", "VAMI payload exceeds 1 MiB")
    checksum = zlib.crc32(payload) & 0xFFFFFFFF
    result = _HEADER.pack(MAGIC, VERSION, len(payload), checksum) + payload
    logger.debug("encode_intrinsic_frame exit bytes=%d crc32=%08x", len(result), checksum)
    return result


class _Reader:
    """Small bounded reader for canonical VAMI payloads."""

    def __init__(self, payload: bytes) -> None:
        logger.debug("_Reader.__init__ entry bytes=%d", len(payload))
        self.payload, self.pos, self.nodes, self.obstructions = payload, 0, 0, 0
        logger.debug("_Reader.__init__ exit")

    def take(self, count: int) -> bytes:
        """Consume exactly ``count`` payload bytes."""
        logger.debug("_Reader.take entry count=%d pos=%d", count, self.pos)
        end = self.pos + count
        if end > len(self.payload):
            _fail("payload", "bad VAMI payload")
        result, self.pos = self.payload[self.pos:end], end
        logger.debug("_Reader.take exit pos=%d", self.pos)
        return result

    def u8(self) -> int:
        """Consume one unsigned byte."""
        logger.debug("_Reader.u8 entry")
        result = self.take(1)[0]
        logger.debug("_Reader.u8 exit value=%d", result)
        return result

    def u16(self) -> int:
        """Consume one big-endian unsigned word."""
        logger.debug("_Reader.u16 entry")
        result = int.from_bytes(self.take(2), "big")
        logger.debug("_Reader.u16 exit value=%d", result)
        return result

    def enter(self, depth: int, count: int = 1) -> None:
        """Account for bounded semantic nodes at one depth."""
        logger.debug("_Reader.enter entry depth=%d count=%d", depth, count)
        if depth > MAX_DEPTH:
            _fail("resource", "VAMI depth exceeds 128")
        self.nodes += count
        if self.nodes > MAX_NODES:
            _fail("resource", "VAMI node count exceeds 4096")
        logger.debug("_Reader.enter exit nodes=%d", self.nodes)

    def mark(self) -> IntrinsicMarkIR:
        """Decode one closed intrinsic mark."""
        logger.debug("_Reader.mark entry")
        raw = self.u8()
        if raw not in (0, 1):
            _fail("payload", "unknown intrinsic mark")
        result = IntrinsicMarkIR.PULSE if raw else IntrinsicMarkIR.SILENT
        logger.debug("_Reader.mark exit mark=%s", result.value)
        return result

    def obstruction(self) -> IntrinsicObstructionIR:
        """Decode one obstruction body after its tag."""
        logger.debug("_Reader.obstruction entry")
        if self.u8() != 0:
            _fail("payload", "unknown obstruction code")
        count = self.u16()
        if count == 0 or count > MAX_PATH:
            _fail("payload", "invalid obstruction path length")
        raw = tuple(self.u8() for _ in range(count))
        if any(step > 3 for step in raw):
            _fail("payload", "unknown obstruction path step")
        result = IntrinsicObstructionIR(IntrinsicObstructionCodeIR.TAIL_OF_SILENCE, tuple(_STEPS[step] for step in raw))
        if error := decoded_semantic_error(result):
            _fail("payload", error)
        self.obstructions += 1
        if self.obstructions > MAX_OBSTRUCTIONS:
            _fail("resource", "too many VAMI obstructions")
        logger.debug("_Reader.obstruction exit path=%d", count)
        return result

    def obstruction_set(self, depth: int, allow_empty: bool) -> tuple[IntrinsicObstructionIR, ...]:
        """Decode one bounded, path-unique obstruction set."""
        logger.debug("_Reader.obstruction_set entry depth=%d allow_empty=%s", depth, allow_empty)
        count = self.u16()
        if count > MAX_OBSTRUCTIONS or (not allow_empty and count == 0):
            _fail("payload", "invalid obstruction count")
        if self.obstructions + count > MAX_OBSTRUCTIONS:
            _fail("resource", "too many VAMI obstructions")
        values = []
        for _ in range(count):
            self.enter(depth + 1)
            if self.u8() != 8:
                _fail("payload", "obstruction set requires obstruction tags")
            values.append(self.obstruction())
        paths = [item.path for item in values]
        if len(set(paths)) != len(paths):
            _fail("payload", "duplicate obstruction path")
        result = tuple(values)
        logger.debug("_Reader.obstruction_set exit count=%d", len(result))
        return result

    def response(self, depth: int) -> IntrinsicIR:
        """Decode one response-value child."""
        logger.debug("_Reader.response entry depth=%d", depth)
        result = self.node(depth)
        if type(result) not in {IntrinsicRecurrenceValueIR, IntrinsicMarkValueIR, IntrinsicPairValueIR}:
            _fail("payload", "response child has non-response tag")
        logger.debug("_Reader.response exit type=%s", type(result).__name__)
        return result

    def node(self, depth: int = 0) -> IntrinsicIR:
        """Decode one recursively bounded intrinsic node."""
        logger.debug("_Reader.node entry depth=%d", depth)
        self.enter(depth)
        tag = self.u8()
        if tag == 1:
            result = IntrinsicAnchorIR()
        elif tag == 2:
            result = IntrinsicTactIR()
        elif tag == 3:
            count, anchor = self.u16(), self.u8()
            if anchor not in (0, 1):
                _fail("payload", "invalid recurrence anchor flag")
            if count > MAX_TACTS or (count == 0) != bool(anchor):
                _fail("payload", "invalid intrinsic recurrence")
            self.enter(depth + 1, count + anchor)
            result = IntrinsicRecurrenceIR((IntrinsicTactIR(),) * count, IntrinsicAnchorIR() if anchor else None)
        elif tag == 4:
            result = self.mark()
        elif tag == 5:
            recurrence = self.node(depth + 1)
            if type(recurrence) is not IntrinsicRecurrenceIR:
                _fail("payload", "recurrence-value requires recurrence")
            result = IntrinsicRecurrenceValueIR(recurrence)
        elif tag == 6:
            result = IntrinsicMarkValueIR(self.mark())
        elif tag == 7:
            result = IntrinsicPairValueIR(self.response(depth + 1), self.response(depth + 1))
        elif tag == 8:
            result = self.obstruction()
        elif tag == 9:
            result = IntrinsicReadyIR(self.response(depth + 1))
        elif tag == 10:
            result = IntrinsicBlockedIR(self.obstruction_set(depth, False))
        elif tag == 11:
            result = IntrinsicEchoIR(self.response(depth + 1))
        elif tag == 12:
            result = IntrinsicMismatchIR(self.response(depth + 1), self.response(depth + 1))
            if error := decoded_semantic_error(result):
                _fail("payload", error)
        elif tag == 13:
            left, right = self.obstruction_set(depth, True), self.obstruction_set(depth, True)
            if not left and not right:
                _fail("payload", "domain-blocked requires an obstruction")
            result = IntrinsicDomainBlockedIR(left, right)
        else:
            _fail("tag", f"unknown VAMI tag: {tag}")
        logger.debug("_Reader.node exit tag=%d type=%s", tag, type(result).__name__)
        return result


def decode_intrinsic_frame(blob: object) -> IntrinsicIR:
    """Decode one exact canonical VAMI frame to validated R12.2 IR."""
    logger.debug("decode_intrinsic_frame entry type=%s", type(blob).__name__)
    if type(blob) is not bytes:
        _fail("payload", "VAMI frame must be exact bytes")
    if len(blob) < _HEADER.size:
        _fail("short_frame", "short VAMI frame")
    magic, version, size, checksum = _HEADER.unpack(blob[: _HEADER.size])
    if magic != MAGIC:
        _fail("magic", "bad VAMI magic")
    if version != VERSION:
        _fail("version", f"unsupported VAMI version: {version}")
    if size > MAX_PAYLOAD_BYTES:
        _fail("resource", "VAMI payload exceeds 1 MiB")
    payload = blob[_HEADER.size :]
    if len(payload) != size:
        _fail("length", "VAMI payload length mismatch")
    if zlib.crc32(payload) & 0xFFFFFFFF != checksum:
        _fail("crc32", "VAMI checksum mismatch")
    reader = _Reader(payload)
    result = reader.node()
    if reader.pos != len(payload):
        _fail("payload", "trailing VAMI payload data")
    if error := decoded_semantic_error(result):
        _fail("payload", error)
    if encode_intrinsic_frame(result) != blob:
        _fail("payload", "noncanonical VAMI payload")
    logger.debug("decode_intrinsic_frame exit nodes=%d obstructions=%d", reader.nodes, reader.obstructions)
    return result

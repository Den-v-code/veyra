"""Small immutable-ish data model for VAM v0.2."""
from __future__ import annotations

from dataclasses import dataclass, field
import logging
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Instruction:
    """One parsed VAM instruction."""

    op: str
    args: tuple[Any, ...]
    line: int = 0

    def comparable(self) -> tuple[str, tuple[Any, ...]]:
        """Return a line-independent comparison key."""
        return (self.op, self.args)


@dataclass(frozen=True)
class VamObject:
    """Runtime object stored in a VAM register."""

    kind: str
    data: dict[str, Any]

    def field(self, name: str, default: Any = None) -> Any:
        """Read an object field without exposing mutation conventions."""
        return self.data.get(name, default)


@dataclass(frozen=True)
class TraceEvent:
    """Append-only execution trace event."""

    pc: int
    op: str
    dst: str
    kind: str
    detail: str


@dataclass
class VamState:
    """Complete VAM v0.2 execution state."""

    pc: int = 0
    registers: dict[str, VamObject] = field(default_factory=dict)
    trace: list[TraceEvent] = field(default_factory=list)
    certs: list[VamObject] = field(default_factory=list)
    obstructions: list[VamObject] = field(default_factory=list)

    def put(self, register: str, obj: VamObject, op: str, detail: str) -> None:
        """Store an object and append a trace row."""
        logger.debug("state put pc=%d op=%s register=%s kind=%s", self.pc, op, register, obj.kind)
        self.registers[register] = obj
        self.trace.append(TraceEvent(self.pc, op, register, obj.kind, detail))
        if obj.kind == "Obstruction":
            self.obstructions.append(obj)
        if obj.kind == "Certificate" and obj.field("accepted") is True:
            self.certs.append(obj)


class VamExecutionError(ValueError):
    """Raised only for malformed programs, not failed Veyra claims."""

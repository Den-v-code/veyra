"""Deterministic canonical reports for VAM execution parity."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import logging
from typing import Any

from .model import Instruction, TraceEvent, VamObject, VamState

logger = logging.getLogger(__name__)

PROFILE = "vam0-ref-v1"
JsonDict = dict[str, Any]


def normalize_value(value: Any) -> Any:
    """Recursively normalize VAM values into stable JSON-compatible data."""
    logger.debug("normalize_value entry type=%s", type(value).__name__)
    result = _normalize(value)
    logger.debug("normalize_value exit normalized_type=%s", type(result).__name__)
    return result


def instruction_rows(program: Sequence[Instruction]) -> list[JsonDict]:
    """Return canonical instruction rows with stable argument encoding."""
    logger.debug("instruction_rows entry instructions=%d", len(program))
    rows = [
        {
            "pc": pc,
            "line": inst.line,
            "op": inst.op,
            "args": [normalize_value(arg) for arg in inst.args],
        }
        for pc, inst in enumerate(program)
    ]
    logger.debug("instruction_rows exit rows=%d", len(rows))
    return rows


def trace_rows(state: VamState) -> list[JsonDict]:
    """Return canonical trace rows from a VAM state."""
    logger.debug("trace_rows entry trace=%d", len(state.trace))
    rows = [_trace_event_row(event) for event in state.trace]
    logger.debug("trace_rows exit rows=%d", len(rows))
    return rows


def register_rows(state: VamState) -> JsonDict:
    """Return registers keyed in lexicographic order with normalized objects."""
    logger.debug("register_rows entry registers=%d", len(state.registers))
    rows = {name: normalize_value(state.registers[name]) for name in sorted(state.registers)}
    logger.debug("register_rows exit rows=%d", len(rows))
    return rows


def canonical_report(program: Sequence[Instruction], state: VamState) -> JsonDict:
    """Build the Python oracle report for future VAM execution parity checks.

    The returned structure contains only JSON-serializable primitives,
    dictionaries, and lists. Register keys and object data keys are sorted so
    repeated runs over the same program/state produce byte-stable JSON when
    dumped with ``sort_keys=True``.
    """
    logger.debug("canonical_report entry instructions=%d pc=%d", len(program), state.pc)
    report = {
        "profile": PROFILE,
        "instructions": instruction_rows(program),
        "trace": trace_rows(state),
        "registers": register_rows(state),
        "certs": [normalize_value(obj) for obj in state.certs],
        "obstructions": [normalize_value(obj) for obj in state.obstructions],
        "final_pc": state.pc,
    }
    logger.debug(
        "canonical_report exit trace=%d registers=%d certs=%d obstructions=%d",
        len(report["trace"]),
        len(report["registers"]),
        len(report["certs"]),
        len(report["obstructions"]),
    )
    return report


def _normalize(value: Any) -> Any:
    if isinstance(value, VamObject):
        return {"kind": value.kind, "data": _normalize_mapping(value.data)}
    if isinstance(value, TraceEvent):
        return _trace_event_row(value)
    if isinstance(value, Instruction):
        return {"line": value.line, "op": value.op, "args": [_normalize(arg) for arg in value.args]}
    if isinstance(value, Mapping):
        return _normalize_mapping(value)
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return {"type": type(value).__qualname__, "data": str(value)}


def _normalize_mapping(mapping: Mapping[Any, Any]) -> JsonDict:
    items = sorted(mapping.items(), key=lambda item: _key_sort_token(item[0]))
    return {str(key): _normalize(value) for key, value in items}


def _key_sort_token(key: Any) -> tuple[str, str]:
    return (type(key).__qualname__, str(key))


def _trace_event_row(event: TraceEvent) -> JsonDict:
    return {
        "pc": event.pc,
        "op": event.op,
        "dst": event.dst,
        "kind": event.kind,
        "detail": event.detail,
    }

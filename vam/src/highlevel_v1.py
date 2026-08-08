"""HL-1 finite-carrier high-level lowering helper.

This isolated helper transports only observer aliases plus one conservative
process/claim block. It never claims theorem/proof semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
import re

from .compiler import SUPPORTED_OBSERVERS

logger = logging.getLogger(__name__)
NO_OVERCLAIM = "HL-1 is syntax transport only; it proves no theorem"
_IDENT = r"[A-Za-z_][A-Za-z0-9_-]*"
_OBS_LABEL = rf"(?:observer:)?{_IDENT}"
_FORBIDDEN = {
    "theorem": "hl.unsupported_theorem",
    "lemma": "hl.unsupported_theorem",
    "verified": "hl.unsupported_verified_status",
    "forall": "hl.unsupported_quantifier",
    "proof": "hl.unsupported_proof",
}


@dataclass(frozen=True)
class HL1Diagnostic:
    error_class: str
    severity: str
    message: str
    line: int
    column: int
    offset: int
    compile_phase: str
    expected: str | None = None
    found: str | None = None
    suggestion: str | None = None
    no_overclaim_note: str = NO_OVERCLAIM


@dataclass(frozen=True)
class HL1Lowering:
    source_kind: str
    name: str
    core_source: str | None = None
    observer_name: str | None = None
    diagnostics: tuple[HL1Diagnostic, ...] = ()
    boundary: str = "HL-1 finite carrier lowering; no theorem acceptance"

    @property
    def ok(self) -> bool:
        return self.core_source is not None and not self.diagnostics

    @property
    def diagnostic(self) -> HL1Diagnostic | None:
        return self.diagnostics[0] if self.diagnostics else None


@dataclass(frozen=True)
class _Observer:
    label: str
    reads_kind: str | None = None
    shadow_kind: str | None = None


def lower_hl1_source(source: str) -> HL1Lowering:
    logger.debug("hl1 lower entry chars=%d", len(source))
    forbidden = _first_forbidden(source)
    if forbidden is not None:
        offset, code = forbidden
        return _error(source, offset, code, _message_for_code(code), "observer declarations plus one process or claim block", source[offset : offset + 16] or "<empty>", "remove theorem/proof/forall/verified forms")

    lines = source.splitlines()
    observers: dict[str, _Observer] = {}
    idx = 0
    while idx < len(lines):
        line = lines[idx].strip()
        if not line:
            idx += 1
            continue
        parsed = _parse_observer(line)
        if parsed is None:
            break
        name, obs = parsed
        if name in observers:
            return _error(source, _line_offset(lines, idx), "hl.duplicate_observer", f"duplicate observer declaration: {name}", "one observer name", name, "rename one of the declarations")
        observers[name] = obs
        idx += 1

    rest = "\n".join(lines[idx:]).strip()
    if not rest:
        return _error(source, len(source), "hl.syntax", "expected one process or claim block", "process NAME { ... } or claim NAME := ...", "<empty>", "add an observer declaration and one block")
    if rest.startswith("process "):
        result = _lower_process_block(source, rest, observers, _line_offset(lines, idx))
    elif rest.startswith("claim "):
        result = _lower_claim_block(source, rest, observers, _line_offset(lines, idx))
    else:
        result = _error(source, _line_offset(lines, idx), "hl.syntax", "expected process or claim block", "process NAME { ... } or claim NAME := ...", rest[:24] or "<empty>", "start the block with process or claim")
    logger.debug("hl1 lower exit ok=%s kind=%s name=%s", result.ok, result.source_kind, result.name)
    return result


def _lower_process_block(source: str, text: str, observers: dict[str, _Observer], offset: int) -> HL1Lowering:
    match = re.fullmatch(rf"process\s+({_IDENT})\s*\{{(?P<body>.*)\}}\s*", text, re.S)
    if not match:
        return _error(source, offset, "hl.syntax", "process NAME { ... }", "matching braces", text[:32] or "<empty>", "close the process block with a final '}'")
    name = match.group(1)
    body = match.group("body").strip()
    if not body:
        return _error(source, offset, "hl.empty_process", "non-empty process body", "at least one step or claim", "<empty>", "add a straight-line step list or one claim")
    if body.startswith("claim ") or body.startswith("echo("):
        return _lower_claim_body(source, body, observers, offset, name)
    return _lower_step_process(source, body, offset, name)


def _lower_claim_block(source: str, text: str, observers: dict[str, _Observer], offset: int) -> HL1Lowering:
    match = re.fullmatch(rf"claim\s+({_IDENT})\s*:=\s*(?P<body>.*)\s*", text, re.S)
    if not match:
        return _error(source, offset, "hl.syntax", "claim NAME := echo(...) under OBS", "assignment form", text[:32] or "<empty>", "use a single claim assignment")
    return _lower_claim_body(source, match.group("body"), observers, offset, match.group(1))


def _lower_claim_body(source: str, body: str, observers: dict[str, _Observer], offset: int, default_name: str) -> HL1Lowering:
    match = re.fullmatch(rf"(?:claim\s+({_IDENT})\s*:=\s*)?echo\s*\((?P<args>.*)\)\s*under\s+(?P<obs>{_OBS_LABEL})\s*", body.strip(), re.S)
    if not match:
        return _error(source, offset, "hl.syntax", "echo(LEFT,RIGHT) under OBS", "echo(...) under ...", body[:32] or "<empty>", "write a single finite echo claim")
    name = match.group(1) or default_name
    args = _split_args(match.group("args"))
    if args is None:
        return _error(source, offset, "hl.syntax", "two top-level echo operands", "LEFT,RIGHT", match.group("args"), "use exactly two operands")
    observer = _resolve_observer(match.group("obs"), observers)
    if isinstance(observer, HL1Diagnostic):
        return HL1Lowering("claim", name, diagnostics=(observer,))
    left, right = args
    return HL1Lowering("claim", name, f"echo({left},{right},{observer})", observer_name=observer)


def _lower_step_process(source: str, body: str, offset: int, name: str) -> HL1Lowering:
    env: dict[str, tuple[str, str]] = {}
    yield_expr: str | None = None
    for stmt in (part.strip() for part in re.split(r"[;\n]", body)):
        if not stmt:
            continue
        if yield_expr is not None:
            return _error(source, offset, "hl.multiple_yield", "exactly one yield", "one yield statement", stmt, "remove the extra statement after yield")
        if m := re.fullmatch(rf"rez\s+({_IDENT})", stmt):
            env[m.group(1)] = ("rez", f"rez:{m.group(1)}")
        elif m := re.fullmatch(rf"nod\s+({_IDENT})\s+from\s+({_IDENT})", stmt):
            src = env.get(m.group(2))
            if src is None:
                return _error(source, offset, "hl.unknown_local", f"unknown local: {m.group(2)}", "earlier local name", m.group(2), "declare the source with rez first")
            if src[0] != "rez":
                return _error(source, offset, "hl.bad_reference", f"nod expects a rez source: {m.group(2)}", "rez local", src[0], "point nod at an earlier rez binding")
            env[m.group(1)] = ("nod", f"nod({src[1]})")
        elif m := re.fullmatch(rf"tact\s+({_IDENT})\s+from\s+({_IDENT})\s*->\s*({_IDENT})", stmt):
            left, right = env.get(m.group(2)), env.get(m.group(3))
            if left is None or right is None:
                missing = m.group(2) if left is None else m.group(3)
                return _error(source, offset, "hl.unknown_local", f"unknown local: {missing}", "earlier local name", missing, "define both tact inputs first")
            env[m.group(1)] = ("tact", f"tact({left[1]},{right[1]})")
        elif m := re.fullmatch(rf"breath\s+({_IDENT})\s+from\s+({_IDENT})", stmt):
            src = env.get(m.group(2))
            if src is None:
                return _error(source, offset, "hl.unknown_local", f"unknown local: {m.group(2)}", "earlier local name", m.group(2), "define the source first")
            env[m.group(1)] = ("breath", f"breath({src[1]})")
        elif m := re.fullmatch(rf"mode\s+({_IDENT})\s+from\s+({_IDENT})", stmt):
            src = env.get(m.group(2))
            if src is None:
                return _error(source, offset, "hl.unknown_local", f"unknown local: {m.group(2)}", "earlier local name", m.group(2), "define the source first")
            env[m.group(1)] = ("mode", f"mode({src[1]})")
        elif m := re.fullmatch(rf"yield\s+({_IDENT})", stmt):
            src = env.get(m.group(1))
            if src is None:
                return _error(source, offset, "hl.unknown_local", f"unknown local: {m.group(1)}", "earlier local name", m.group(1), "yield a previously bound name")
            yield_expr = src[1]
        else:
            return _error(source, offset, "hl.unsupported_statement", "rez/nod/tact/breath/mode/yield only", "straight-line process statement", stmt, "rewrite the process as a finite straight line")
    if yield_expr is None:
        return _error(source, offset, "hl.missing_yield", "exactly one yield", "yield NAME", body[:32] or "<empty>", "end the process with a single yield")
    return HL1Lowering("process", name, yield_expr)


def _parse_observer(line: str) -> tuple[str, _Observer] | None:
    if m := re.fullmatch(rf"observer\s+({_IDENT})\s*:=\s*({_OBS_LABEL})\s*", line):
        return m.group(1), _Observer(m.group(2).removeprefix("observer:"))
    if m := re.fullmatch(rf"observer\s+({_IDENT})\s+reads\s+({_IDENT})\s+as\s+({_IDENT})\s*", line):
        return m.group(1), _Observer(m.group(1), m.group(2), m.group(3))
    return None


def _resolve_observer(text: str, observers: dict[str, _Observer]) -> str | HL1Diagnostic:
    label = observers[text].label if text in observers else text.removeprefix("observer:")
    if label not in SUPPORTED_OBSERVERS:
        return _diagnostic("", 1, 1, "hl.unsupported_observer", f"unsupported observer: {text}", "length/kind/label/trace/boundary", text, "declare or rename to a supported observer")
    return "observer" if label == "kind" else f"observer:{label}"


def _split_args(text: str) -> tuple[str, str] | None:
    depth = 0
    split = None
    for i, ch in enumerate(text):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                return None
        elif ch == "," and depth == 0:
            if split is not None:
                return None
            split = i
    if split is None or depth:
        return None
    left, right = text[:split].strip(), text[split + 1 :].strip()
    return (left, right) if left and right else None


def _first_forbidden(source: str) -> tuple[int, str] | None:
    for token, code in _FORBIDDEN.items():
        if m := re.search(rf"\b{token}\b", source):
            return m.start(), code
    return None


def _message_for_code(code: str) -> str:
    return {
        "hl.unsupported_theorem": "theorem/lemma forms are not supported by HL-1",
        "hl.unsupported_verified_status": "verified theorem cards require a checker; HL-1 carries only open transport",
        "hl.unsupported_quantifier": "forall/exists forms are out of HL-1 scope",
        "hl.unsupported_proof": "proof objects are not accepted as proof semantics in HL-1",
    }.get(code, "unsupported high-level syntax")


def _error(source: str, offset: int, code: str, message: str, expected: str, found: str, suggestion: str) -> HL1Lowering:
    return HL1Lowering("error", "", diagnostics=(_diagnostic(source, _line_from_offset(source, offset), _column_from_offset(source, offset), code, message, expected, found, suggestion),))


def _diagnostic(source: str, line: int, column: int, code: str, message: str, expected: str, found: str, suggestion: str) -> HL1Diagnostic:
    diag = HL1Diagnostic(code, "error", message, line, column, _offset(source, line, column), "hl1-parse", expected, found, suggestion)
    logger.error("hl1 diagnostic class=%s line=%d column=%d", code, line, column)
    return diag


def _line_offset(lines: list[str], idx: int) -> int:
    return sum(len(line) + 1 for line in lines[:idx]) + 1


def _offset(source: str, line: int, column: int) -> int:
    if line <= 1:
        return max(0, column - 1)
    parts = source.splitlines(True)
    return sum(len(part) for part in parts[: line - 1]) + max(0, column - 1)


def _line_from_offset(source: str, offset: int) -> int:
    return source[: max(0, offset)].count("\n") + 1


def _column_from_offset(source: str, offset: int) -> int:
    prefix = source[: max(0, offset)]
    return len(prefix.rsplit("\n", 1)[-1]) + 1

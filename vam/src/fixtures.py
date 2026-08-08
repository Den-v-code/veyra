"""Deterministic golden fixture corpus for VAM0/ref-v1 semantics."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from .compiler import compile_source
from .interpreter import execute
from .model import Instruction
from .optimizer import optimize
from .report import canonical_report
from .assembly import parse_vmasm


@dataclass(frozen=True)
class FixtureCase:
    """One named fixture plus the program used for its canonical report."""

    name: str
    program: tuple[Instruction, ...]
    report_program: tuple[Instruction, ...] | None = None
    valid_vam0: bool = True


def _program(source: str) -> tuple[Instruction, ...]:
    return parse_vmasm(source)


_MINIMAL_ACCEPTED_ECHO = _program(
    """
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r1, "1"
TACT %r4, %r2, %r3, "step"
TACT %r5, %r3, %r2, "step"
BREATH %r6, %r4
BREATH %r7, %r5
MODE %r8, %r6
MODE %r9, %r7
OBSERVER %r10, "length"
ECHO %r11, %r8, %r9, %r10
CERT %r12, "length-echo", %r11, "finite length observer only"
"""
)

_BAD_BREATH_NOD = _program(
    """
REZ %r1, "phase"
NOD %r2, %r1, "0"
BREATH %r3, %r2
NOD %r4, %r3, "1"
OBSERVER %r5, "length"
CERT %r6, "bad-breath-nod", %r4, "obstruction chain"
"""
)

_OBSTRUCTION_NOD_REQUIRES_REZ = _program(
    """
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r2, "1"
"""
)

_OBSTRUCTION_TACT_LEFT = _program(
    """
REZ %r1, "phase"
NOD %r2, %r1, "0"
TACT %r3, %r1, %r2, "left-mismatch"
"""
)

_OBSTRUCTION_TACT_RIGHT = _program(
    """
REZ %r1, "phase"
NOD %r2, %r1, "0"
TACT %r3, %r2, %r1, "right-mismatch"
"""
)

_OBSTRUCTION_BREATH_REQUIRES_TACTS = _program(
    """
REZ %r1, "phase"
BREATH %r2, %r1
"""
)

_OBSTRUCTION_MODE_REQUIRES_BREATH = _program(
    """
REZ %r1, "phase"
MODE %r2, %r1
"""
)

_OBSTRUCTION_OBSERVE_REQUIRES_OBSERVER = _program(
    """
REZ %r1, "phase"
OBSERVE %r2, %r1, %r1
"""
)

_OBSTRUCTION_COMPRESS_NESTED_SHADOW = _program(
    """
REZ %r1, "phase"
COMPRESS %r2, %r1, %r1
"""
)

_OBSTRUCTION_EXPLICIT_MANUAL = _program(
    """
REZ %r1, "phase"
OBSTRUCT %r2, "manual-obstruction", %r1
"""
)

_OBSTRUCTION_MISSING_REGISTER_WITNESS = _program(
    """
OBSTRUCT %r1, "missing-register", %r404
"""
)

_ALL_INSTRUCTION_KINDS = _program(
    """
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r1, "1"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "kind"
OBSERVE %r8, %r6, %r7
COMPRESS %r9, %r6, %r7
ECHO %r10, %r6, %r6, %r7
OBSTRUCT %r11, "manual-obstruction", %r1
CERT %r12, "all-kinds", %r10, "ref-v1"
"""
)

_SHELL_SOURCE = "shell(echo(nod:a,nod:a,observer:length),echo(nod:b,nod:b,observer:kind))"
_SHELL_LOWERING = compile_source(_SHELL_SOURCE, certify=False).program
_SHELL_BLOCKED_SOURCE = "shell(echo(nod:a,nod:bbb,observer:label),echo(nod:c,nod:c,observer:kind))"
_SHELL_BLOCKED_LOWERING = compile_source(_SHELL_BLOCKED_SOURCE, certify=False).program
_SHELL_UNSUPPORTED_SOURCE = "shell(echo(nod:a,nod:a,observer:weight))"
_SHELL_UNSUPPORTED_LOWERING = compile_source(_SHELL_UNSUPPORTED_SOURCE, certify=False).program

_DUPLICATE_COMPRESS_SOURCE = _program(
    """
REZ %r1, "phase"
NOD %r2, %r1, "0"
NOD %r3, %r1, "1"
TACT %r4, %r2, %r3, "step"
BREATH %r5, %r4
MODE %r6, %r5
OBSERVER %r7, "kind"
COMPRESS %r8, %r6, %r7
COMPRESS %r9, %r6, %r7
ECHO %r10, %r8, %r9, %r7
CERT %r11, "compressed-kind", %r10, "same compressed witness"
"""
)
_DUPLICATE_COMPRESS_OPTIMIZED = optimize(_DUPLICATE_COMPRESS_SOURCE).optimized

_FIXTURES: tuple[FixtureCase, ...] = (
    FixtureCase("minimal-accepted-echo-cert", _MINIMAL_ACCEPTED_ECHO),
    FixtureCase("bad-breath-nod-obstruction", _BAD_BREATH_NOD),
    FixtureCase("obstruction-nod-requires-rez", _OBSTRUCTION_NOD_REQUIRES_REZ),
    FixtureCase("obstruction-tact-left", _OBSTRUCTION_TACT_LEFT),
    FixtureCase("obstruction-tact-right", _OBSTRUCTION_TACT_RIGHT),
    FixtureCase("obstruction-breath-requires-tacts", _OBSTRUCTION_BREATH_REQUIRES_TACTS),
    FixtureCase("obstruction-mode-requires-breath", _OBSTRUCTION_MODE_REQUIRES_BREATH),
    FixtureCase("obstruction-observe-requires-observer", _OBSTRUCTION_OBSERVE_REQUIRES_OBSERVER),
    FixtureCase("obstruction-compress-nested-shadow", _OBSTRUCTION_COMPRESS_NESTED_SHADOW),
    FixtureCase("obstruction-explicit-manual", _OBSTRUCTION_EXPLICIT_MANUAL),
    FixtureCase("obstruction-missing-register-witness", _OBSTRUCTION_MISSING_REGISTER_WITNESS),
    FixtureCase("all-instruction-kinds", _ALL_INSTRUCTION_KINDS),
    FixtureCase("shell-lowering", _SHELL_LOWERING),
    FixtureCase("shell-blocked-child-obstruction", _SHELL_BLOCKED_LOWERING),
    FixtureCase("shell-unsupported-child-obstruction", _SHELL_UNSUPPORTED_LOWERING),
    FixtureCase(
        "optimizer-duplicate-compress",
        _DUPLICATE_COMPRESS_SOURCE,
        _DUPLICATE_COMPRESS_OPTIMIZED,
    ),
)


def iter_fixture_programs() -> Iterator[tuple[str, tuple[Instruction, ...]]]:
    """Yield the named golden fixture programs in corpus order."""
    for fixture in _FIXTURES:
        yield fixture.name, fixture.program


def iter_fixture_report_programs() -> Iterator[tuple[str, tuple[Instruction, ...]]]:
    """Yield the exact programs used for canonical report parity."""
    for fixture in _FIXTURES:
        yield fixture.name, fixture.report_program or fixture.program


def iter_valid_vam0_fixture_report_programs() -> Iterator[tuple[str, tuple[Instruction, ...]]]:
    """Yield report programs that are valid VAM0 payload candidates."""
    for fixture in _FIXTURES:
        if fixture.valid_vam0:
            yield fixture.name, fixture.report_program or fixture.program


def iter_fixture_reports() -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield canonical reports for the current executable fixture surface."""
    for name, program in iter_fixture_report_programs():
        yield name, canonical_report(program, execute(program))


def fixture_program(name: str) -> tuple[Instruction, ...]:
    """Return one named fixture program."""
    for fixture_name, program in iter_fixture_programs():
        if fixture_name == name:
            return program
    raise KeyError(name)


def fixture_report_program(name: str) -> tuple[Instruction, ...]:
    """Return the exact program used for this fixture's canonical report."""
    for fixture_name, program in iter_fixture_report_programs():
        if fixture_name == name:
            return program
    raise KeyError(name)


def fixture_report(name: str) -> dict[str, Any]:
    """Return the canonical report for one named fixture."""
    for fixture_name, report in iter_fixture_reports():
        if fixture_name == name:
            return report
    raise KeyError(name)

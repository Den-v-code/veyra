"""Zero-callback constructor-integrity attacks against KPT1 parsing."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from dataclasses import dataclass

import pytest

import src.core.omegaa_kpt1_parser as parser
import src.core.omegaa_kpt1_types as syntax
from src.core.omegaa_kpt1_codec import codec_kernel_proof_term_v1
from src.core.omegaa_kpt1_types import (
    KernelProofTermV1,
    KernelTermTagV1,
    kernel_term_v1,
    zero_level_v1,
)


@dataclass(slots=True)
class _Counter:
    calls: int = 0


class _Bomb:
    def __init__(self, counter: _Counter) -> None:
        self._counter = counter

    def __call__(self, *args: object, **kwargs: object) -> object:
        self._counter.calls += 1
        raise AssertionError("hostile callable executed")

    def __get__(self, instance: object, owner: object) -> object:
        self._counter.calls += 1
        raise AssertionError("hostile descriptor read")

    def __set__(self, instance: object, value: object) -> None:
        self._counter.calls += 1
        raise AssertionError("hostile slot write")


def _term_wire() -> bytes:
    term = kernel_term_v1(KernelTermTagV1.VAR, 0)
    return codec_kernel_proof_term_v1(term)


def _level_wire() -> bytes:
    term = kernel_term_v1(KernelTermTagV1.SORT, zero_level_v1())
    return codec_kernel_proof_term_v1(term)


def _hostile_post_init_code(_self: object) -> None:
    builtins._kpt1_post_code_callbacks += 1  # type: ignore[attr-defined]
    raise AssertionError("mutated post-init code executed")


def _hostile_init_function() -> Callable[..., None]:
    """Return init-shaped hostile code with the generated init's one free cell."""
    marker = object()

    def hostile(_self: object, _tag: object, _fields: object = ()) -> None:
        _ = marker
        builtins._kpt1_init_code_callbacks += 1  # type: ignore[attr-defined]
        raise AssertionError("mutated init code executed")

    return hostile


_ATTACKS = (
    "parser-term-alias",
    "parser-level-alias",
    "syntax-term-alias",
    "syntax-level-alias",
    "term-init",
    "term-post-init",
    "term-tag-slot",
    "term-fields-slot",
    "level-init",
    "level-post-init",
    "level-tag-slot",
    "level-fields-slot",
)


@pytest.mark.parametrize("attack", _ATTACKS)
def test_parser_constructor_drift_rejects_without_hostile_callbacks(
    attack: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _level_wire() if "level" in attack else _term_wire()
    counter = _Counter()
    bomb = _Bomb(counter)
    targets: dict[str, tuple[object, str]] = {
        "parser-term-alias": (parser, "KernelProofTermV1"),
        "parser-level-alias": (parser, "KernelUniverseLevelV1"),
        "syntax-term-alias": (syntax, "KernelProofTermV1"),
        "syntax-level-alias": (syntax, "KernelUniverseLevelV1"),
        "term-init": (KernelProofTermV1, "__init__"),
        "term-post-init": (KernelProofTermV1, "__post_init__"),
        "term-tag-slot": (KernelProofTermV1, "tag"),
        "term-fields-slot": (KernelProofTermV1, "fields"),
        "level-init": (syntax.KernelUniverseLevelV1, "__init__"),
        "level-post-init": (syntax.KernelUniverseLevelV1, "__post_init__"),
        "level-tag-slot": (syntax.KernelUniverseLevelV1, "tag"),
        "level-fields-slot": (syntax.KernelUniverseLevelV1, "fields"),
    }
    target, name = targets[attack]
    monkeypatch.setattr(target, name, bomb)
    with pytest.raises(ValueError, match="kpt1-parser-constructor-integrity"):
        parser.parse_kernel_proof_term_v1(raw)
    assert counter.calls == 0


@pytest.mark.parametrize("kind", ("term", "level"))
def test_parser_rejects_in_place_post_init_code_mutation_without_callback(
    kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _term_wire() if kind == "term" else _level_wire()
    target = (
        KernelProofTermV1.__post_init__
        if kind == "term"
        else syntax.KernelUniverseLevelV1.__post_init__
    )
    monkeypatch.setattr(builtins, "_kpt1_post_code_callbacks", 0, raising=False)
    monkeypatch.setattr(target, "__code__", _hostile_post_init_code.__code__)
    with pytest.raises(ValueError, match="kpt1-parser-constructor-integrity"):
        parser.parse_kernel_proof_term_v1(raw)
    assert builtins._kpt1_post_code_callbacks == 0  # type: ignore[attr-defined]


@pytest.mark.parametrize("kind", ("term", "level"))
def test_parser_rejects_in_place_init_code_mutation_without_callback(
    kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _term_wire() if kind == "term" else _level_wire()
    target = (
        KernelProofTermV1.__init__
        if kind == "term"
        else syntax.KernelUniverseLevelV1.__init__
    )
    hostile = _hostile_init_function()
    assert len(hostile.__code__.co_freevars) == len(target.__code__.co_freevars) == 1
    monkeypatch.setattr(builtins, "_kpt1_init_code_callbacks", 0, raising=False)
    monkeypatch.setattr(target, "__code__", hostile.__code__)
    with pytest.raises(ValueError, match="kpt1-parser-constructor-integrity"):
        parser.parse_kernel_proof_term_v1(raw)
    assert builtins._kpt1_init_code_callbacks == 0  # type: ignore[attr-defined]

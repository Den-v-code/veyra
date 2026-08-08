"""Hostile graph, resource and zero-callback pressure for private KCF1."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from dataclasses import dataclass

import pytest

import src.core.omegaa_kcf1_parser as parser
import src.core.omegaa_kcf1_types as syntax
import src.core.omegaa_kcf1_codec as codec_module
import src.core.omegaa_kpt1_codec as kpt_codec
import src.core.omegaa_kpt1_parser as kpt_parser
import src.core.omegaa_kpt1_types as kpt_syntax
from src.core.omegaa_kcf1_codec import codec_kernel_continuation_frame_v1
from src.core.omegaa_kcf1_common import (
    KCF1LimitsV1, KCF1ResourceKindV1, KCF1ResourceLimit,
)
from src.core.omegaa_kcf1_types import (
    KernelContinuationFrameV1, KernelContinuationTagV1,
    kernel_continuation_frame_v1,
)
from src.core.omegaa_kpt1_types import (
    KernelProofTermV1, KernelTermTagV1, kernel_term_v1,
)

def _var(index: int = 0) -> KernelProofTermV1:
    return kernel_term_v1(KernelTermTagV1.VAR, index)


def _parse_frame() -> KernelContinuationFrameV1:
    return kernel_continuation_frame_v1(
        KernelContinuationTagV1.PARSE_TERM, b"opaque", _var(),
    )


def _wire() -> bytes:
    return codec_kernel_continuation_frame_v1(_parse_frame())


def _resource_kind(call: Callable[[], object], kind: KCF1ResourceKindV1) -> None:
    with pytest.raises(KCF1ResourceLimit) as caught:
        call()
    assert type(caught.value) is KCF1ResourceLimit
    assert caught.value.kind is kind
    assert not hasattr(caught.value, "code")


def test_exact_resource_equations_charge_root_once_and_nested_wire_once() -> None:
    frame = _parse_frame()
    raw = codec_kernel_continuation_frame_v1(frame)
    nested = len(raw) - (6 + 8 + len(b"opaque") + 8)
    exact = KCF1LimitsV1(
        max_input_bytes=len(raw), max_output_bytes=len(raw), max_depth=2,
        max_nodes=2, max_nested_kpt_bytes=nested,
    )
    assert codec_kernel_continuation_frame_v1(frame, exact) == raw
    assert codec_kernel_continuation_frame_v1(
        parser.parse_kernel_continuation_frame_v1(raw, exact), exact,
    ) == raw
    no_nested = kernel_continuation_frame_v1(
        KernelContinuationTagV1.RETURN_TYPED, b"d" * 32,
    )
    assert codec_kernel_continuation_frame_v1(no_nested, KCF1LimitsV1(max_depth=1))


def test_input_output_nested_node_and_depth_caps_are_distinct_refusals() -> None:
    raw = _wire()
    nested_start = 6 + 8 + len(b"opaque") + 8
    nested = len(raw) - nested_start
    _resource_kind(
        lambda: parser.parse_kernel_continuation_frame_v1(
            raw, KCF1LimitsV1(max_input_bytes=len(raw) - 1),
        ), KCF1ResourceKindV1.INPUT_BYTES,
    )
    _resource_kind(
        lambda: parser.parse_kernel_continuation_frame_v1(
            raw, KCF1LimitsV1(max_output_bytes=len(raw) - 1),
        ), KCF1ResourceKindV1.OUTPUT_BYTES,
    )
    _resource_kind(
        lambda: parser.parse_kernel_continuation_frame_v1(
            raw, KCF1LimitsV1(max_nested_kpt_bytes=nested - 1),
        ), KCF1ResourceKindV1.NESTED_KPT_BYTES,
    )
    two = kernel_continuation_frame_v1(
        KernelContinuationTagV1.INFER_TERM, _var(1), _var(2),
    )
    _resource_kind(
        lambda: codec_kernel_continuation_frame_v1(two, KCF1LimitsV1(max_nodes=2)),
        KCF1ResourceKindV1.COMPOSITE_NODES,
    )
    two_raw = codec_kernel_continuation_frame_v1(two)
    _resource_kind(
        lambda: parser.parse_kernel_continuation_frame_v1(
            two_raw, KCF1LimitsV1(max_nodes=2),
        ), KCF1ResourceKindV1.COMPOSITE_NODES,
    )
    deep = kernel_continuation_frame_v1(
        KernelContinuationTagV1.INFER_TERM,
        kernel_term_v1(KernelTermTagV1.FST, _var(3)), _var(4),
    )
    _resource_kind(
        lambda: codec_kernel_continuation_frame_v1(deep, KCF1LimitsV1(max_depth=2)),
        KCF1ResourceKindV1.COMPOSITE_DEPTH,
    )


def test_kpt_list_and_nat_caps_map_to_exact_kcf_resource_kinds() -> None:
    listed = kernel_term_v1(
        KernelTermTagV1.CTOR, b"c" * 32, 0, (_var(1), _var(2)),
    )
    list_frame = kernel_continuation_frame_v1(
        KernelContinuationTagV1.INFER_TERM, listed, _var(3),
    )
    _resource_kind(
        lambda: codec_kernel_continuation_frame_v1(
            list_frame, KCF1LimitsV1(max_kpt_list_items=1),
        ), KCF1ResourceKindV1.KPT_LIST_ITEMS,
    )
    _resource_kind(
        lambda: parser.parse_kernel_continuation_frame_v1(
            codec_kernel_continuation_frame_v1(list_frame),
            KCF1LimitsV1(max_kpt_list_items=1),
        ), KCF1ResourceKindV1.KPT_LIST_ITEMS,
    )
    nat_frame = kernel_continuation_frame_v1(
        KernelContinuationTagV1.INFER_TERM, _var(256), _var(),
    )
    _resource_kind(
        lambda: codec_kernel_continuation_frame_v1(
            nat_frame, KCF1LimitsV1(max_kpt_nat_bytes=1),
        ), KCF1ResourceKindV1.KPT_NAT_BYTES,
    )
    _resource_kind(
        lambda: parser.parse_kernel_continuation_frame_v1(
            codec_kernel_continuation_frame_v1(nat_frame),
            KCF1LimitsV1(max_kpt_nat_bytes=1),
        ), KCF1ResourceKindV1.KPT_NAT_BYTES,
    )


def test_bool_subclass_partial_and_non_digest_hosts_are_rejected() -> None:
    with pytest.raises(ValueError):
        KCF1LimitsV1(max_nodes=True)
    with pytest.raises(ValueError, match=r"type[_-]id"):
        kernel_continuation_frame_v1(KernelContinuationTagV1.RETURN_TYPED, b"x" * 31)
    class SubFrame(KernelContinuationFrameV1):
        pass
    sub = SubFrame(KernelContinuationTagV1.RETURN_TYPED, (b"x" * 32,))
    with pytest.raises(ValueError, match="frame-host-shape"):
        codec_kernel_continuation_frame_v1(sub)
    partial = object.__new__(KernelContinuationFrameV1)
    object.__setattr__(partial, "tag", KernelContinuationTagV1.RETURN_TYPED)
    with pytest.raises(ValueError, match="invalid-frame-fields"):
        codec_kernel_continuation_frame_v1(partial)


def test_cross_field_and_nested_container_sharing_and_cycles_fail_closed() -> None:
    shared = _var()
    frame = kernel_continuation_frame_v1(
        KernelContinuationTagV1.INFER_TERM, shared, shared,
    )
    with pytest.raises(ValueError, match="shared-host-graph"):
        codec_kernel_continuation_frame_v1(frame)
    items = (_var(1),)
    left = kernel_term_v1(KernelTermTagV1.CTOR, b"a" * 32, 0, items)
    right = kernel_term_v1(KernelTermTagV1.CTOR, b"b" * 32, 0, items)
    with pytest.raises(ValueError, match="shared-host-graph"):
        codec_kernel_continuation_frame_v1(kernel_continuation_frame_v1(
            KernelContinuationTagV1.INFER_TERM, left, right,
        ))
    cyclic = object.__new__(KernelProofTermV1)
    object.__setattr__(cyclic, "tag", KernelTermTagV1.FST)
    object.__setattr__(cyclic, "fields", (cyclic,))
    partial = object.__new__(KernelContinuationFrameV1)
    object.__setattr__(partial, "tag", KernelContinuationTagV1.INFER_TERM)
    object.__setattr__(partial, "fields", (cyclic, _var()))
    with pytest.raises(ValueError, match="cyclic-host-graph"):
        codec_kernel_continuation_frame_v1(partial)


def test_shared_immutable_digest_bytes_are_scalar_not_graph_sharing() -> None:
    digest = b"z" * 32
    terms = tuple(kernel_term_v1(KernelTermTagV1.CONST, digest) for _ in range(3))
    frame = kernel_continuation_frame_v1(KernelContinuationTagV1.COMPARE_TYPES, *terms)
    assert parser.parse_kernel_continuation_frame_v1(
        codec_kernel_continuation_frame_v1(frame),
    ).tag is KernelContinuationTagV1.COMPARE_TYPES


@dataclass(slots=True)
class _Counter:
    calls: int = 0


class _Bomb:
    def __init__(self, counter: _Counter) -> None:
        self.counter = counter

    def __call__(self, *args: object, **kwargs: object) -> object:
        self.counter.calls += 1
        raise AssertionError("hostile callback executed")

    def __get__(self, instance: object, owner: object) -> object:
        self.counter.calls += 1
        raise AssertionError("hostile descriptor executed")

    def __set__(self, instance: object, value: object) -> None:
        self.counter.calls += 1
        raise AssertionError("hostile slot executed")


@pytest.mark.parametrize("attack", ("init", "post", "tag", "fields", "syntax-alias", "parser-alias", "parser-build", "parser-codec", "kpt-parser", "kpt-wire", "kpt-decode-catch", "kpt-resource-catch", "codec-kpt-resource-catch", "kpt-init", "kpt-post", "kpt-syntax"))
def test_replacement_hooks_slots_and_aliases_refuse_with_zero_callbacks(
    attack: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _wire()
    counter = _Counter()
    bomb = _Bomb(counter)
    targets: dict[str, tuple[object, str]] = {
        "init": (KernelContinuationFrameV1, "__init__"),
        "post": (KernelContinuationFrameV1, "__post_init__"),
        "tag": (KernelContinuationFrameV1, "tag"),
        "fields": (KernelContinuationFrameV1, "fields"),
        "syntax-alias": (syntax, "KernelContinuationFrameV1"),
        "parser-alias": (parser, "KernelContinuationFrameV1"),
        "parser-build": (parser, "build_frame_v1"),
        "parser-codec": (parser, "codec_kernel_continuation_frame_v1"),
        "kpt-parser": (kpt_parser, "parse_kernel_proof_term_v1"),
        "kpt-init": (KernelProofTermV1, "__init__"),
        "kpt-post": (KernelProofTermV1, "__post_init__"),
        "kpt-syntax": (kpt_syntax, "KernelProofTermV1"),
    }
    target, name = (kpt_parser, "_wire_preflight") if attack == "kpt-wire" else (parser, "KPT1DecodeError") if attack == "kpt-decode-catch" else (parser, "KPT1ResourceLimit") if attack == "kpt-resource-catch" else (codec_module, "KPT1ResourceLimit") if attack == "codec-kpt-resource-catch" else targets[attack]
    monkeypatch.setattr(target, name, bomb)
    with pytest.raises(ValueError, match="integrity"):
        parser.parse_kernel_continuation_frame_v1(raw)
    assert counter.calls == 0


def test_codec_builder_alias_refuses_without_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    counter = _Counter()
    monkeypatch.setattr(codec_module, "validate_kcf1_builder_integrity_v1", _Bomb(counter))
    with pytest.raises(ValueError, match="codec-alias-integrity"):
        codec_kernel_continuation_frame_v1(_parse_frame())
    assert counter.calls == 0


def _hostile_post(_self: object) -> None:
    builtins._kcf_post_calls += 1  # type: ignore[attr-defined]
    raise AssertionError("mutated post-init executed")


def _hostile_init() -> Callable[..., None]:
    marker = object()
    def hostile(_self: object, _tag: object, _fields: object) -> None:
        _ = marker
        builtins._kcf_init_calls += 1  # type: ignore[attr-defined]
        raise AssertionError("mutated init executed")
    return hostile


@pytest.mark.parametrize("kind", ("init", "post"))
def test_in_place_generated_hook_code_mutation_refuses_with_zero_callbacks(
    kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _wire()
    target = KernelContinuationFrameV1.__init__ if kind == "init" else KernelContinuationFrameV1.__post_init__
    hostile = _hostile_init() if kind == "init" else _hostile_post
    assert len(hostile.__code__.co_freevars) == len(target.__code__.co_freevars)
    name = f"_kcf_{kind}_calls"
    monkeypatch.setattr(builtins, name, 0, raising=False)
    monkeypatch.setattr(target, "__code__", hostile.__code__)
    with pytest.raises(ValueError, match="kcf1-parser-constructor-integrity"):
        parser.parse_kernel_continuation_frame_v1(raw)
    assert getattr(builtins, name) == 0


@pytest.mark.parametrize("kind", ("init", "post", "codec"))
def test_nested_kpt_in_place_hook_code_refuses_before_callback(
    kind: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _wire()
    target = (
        KernelProofTermV1.__init__ if kind == "init" else
        KernelProofTermV1.__post_init__ if kind == "post" else
        kpt_codec.codec_kernel_proof_term_v1
    )
    hostile = _hostile_init() if kind == "init" else _hostile_post
    assert len(hostile.__code__.co_freevars) == len(target.__code__.co_freevars)
    name = "_kcf_post_calls" if kind == "codec" else f"_kcf_{kind}_calls"
    monkeypatch.setattr(builtins, name, 0, raising=False)
    monkeypatch.setattr(target, "__code__", hostile.__code__)
    pattern = "kpt1-parser-constructor-integrity" if kind != "codec" else "kcf1-kpt-dependency-integrity"
    with pytest.raises(ValueError, match=pattern):
        parser.parse_kernel_continuation_frame_v1(raw)
    assert getattr(builtins, name) == 0

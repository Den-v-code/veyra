"""Hostile graphs, exact sums, deterministic limits, freshness and roots for KEC1."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from src.core.omegaa_kcc1_codec import kcc1_empty_config_id_v1, kcc1_source_root_v1
from src.core.omegaa_kec1_types import (
    DEFAULT_KEC1_LIMITS_V1,
    KEC1ApiV1,
    KEC1_EQUATION_BYTES_V1,
    KEC1_EQUATION_ROWS_V1,
    KEC1IntegrityCodeV1,
    KEC1OffsetSpaceV1,
    KEC1OriginTagV1,
    KEC1OriginV1,
    KEC1LocusV1,
    KEC1ResourceKindV1,
    KEC1ResultTagV1,
    KEC1ResultV1,
)
from src.core.omegaa_kec1_typing import (
    KEC1_SOURCE_PATHS_V1,
    InferV1,
    NFβ0V1,
    ReduceOneβ0V1,
    RequireNormalβ0V1,
    WHNFβ0V1,
    empty_core_calculus_id_v1,
    empty_core_calculus_source_root_v1,
)
from src.core.omegaa_kpt1_types import (
    KPT1_FIELD_KINDS,
    KernelLevelTagV1 as LT,
    KernelProofTermV1 as T,
    KernelTermTagV1 as TT,
    KernelUniverseLevelV1 as L,
)


def zero() -> L:
    return L(LT.ZERO)


def sort0() -> T:
    return T(TT.SORT, (zero(),))


def var(index: int = 0) -> T:
    return T(TT.VAR, (index,))


def frame(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def app_identity(argument: T | None = None) -> T:
    return T(TT.APP, (T(TT.LAM, (sort0(), var())), sort0() if argument is None else argument))


def limit(**changes: int):
    return replace(DEFAULT_KEC1_LIMITS_V1, **changes)


def test_exact_enums_equations_and_six_default_identity() -> None:
    assert len(KEC1_EQUATION_ROWS_V1) == 43
    expected = b"KEC1EQ\x00" + (43).to_bytes(8, "big") + b"".join(frame(row.encode()) for row in KEC1_EQUATION_ROWS_V1)
    assert KEC1_EQUATION_BYTES_V1 == expected
    from src.core import omegaa_kec1_typing as typing

    publics = (
        typing.InferV1,
        typing.CheckV1,
        typing.ReduceOneβ0V1,
        typing.WHNFβ0V1,
        typing.NFβ0V1,
        typing.RequireNormalβ0V1,
    )
    assert all(fn.__defaults__ == (DEFAULT_KEC1_LIMITS_V1,) for fn in publics)
    assert all(fn.__defaults__[0] is DEFAULT_KEC1_LIMITS_V1 for fn in publics)
    assert [member.value for member in KEC1ResourceKindV1] == list(range(17))


def test_exact_result_sum_rejects_cross_api_and_payload() -> None:
    with pytest.raises(ValueError):
        KEC1ResultV1(KEC1ApiV1.INFER, KEC1ResultTagV1.CHECKED, None)
    with pytest.raises(TypeError):
        KEC1ResultV1(KEC1ApiV1.INFER, KEC1ResultTagV1.INFERRED, object())

    class AlienOrigin(KEC1OriginV1):
        pass

    with pytest.raises(TypeError):
        AlienOrigin(KEC1OriginTagV1.TERM, 0)
    with pytest.raises(ValueError):
        KEC1LocusV1(KEC1OriginV1(KEC1OriginTagV1.OUTPUT, 0), (), KEC1OffsetSpaceV1.ORIGIN_FRAME, 0)


def test_host_shape_cycle_shared_and_hostile_subclass() -> None:
    malformed = object.__new__(T)
    vars(T)["tag"].__set__(malformed, TT.VAR)
    vars(T)["fields"].__set__(malformed, [])
    result = InferV1((), malformed)
    assert result.tag is KEC1ResultTagV1.INTEGRITY
    assert result.payload.code is KEC1IntegrityCodeV1.HOST_SHAPE

    cyclic = object.__new__(T)
    vars(T)["tag"].__set__(cyclic, TT.FST)
    vars(T)["fields"].__set__(cyclic, (cyclic,))
    result = ReduceOneβ0V1(cyclic)
    assert result.payload.code is KEC1IntegrityCodeV1.GRAPH_CYCLE

    child = var()
    shared = T(TT.APP, (child, child))
    result = ReduceOneβ0V1(shared)
    assert result.payload.code is KEC1IntegrityCodeV1.GRAPH_SHARED

    class Hostile(T):
        callbacks = 0

        def __getattribute__(self, name: str):
            type(self).callbacks += 1
            return super().__getattribute__(name)

    hostile = Hostile(TT.VAR, (0,))
    Hostile.callbacks = 0
    result = InferV1((), hostile)
    assert result.payload.code is KEC1IntegrityCodeV1.HOST_SHAPE
    assert Hostile.callbacks == 0


def test_codec_table_default_and_code_drift_are_integrity_first(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core import omegaa_kec1_types as types_module
    from src.core import omegaa_kec1_typing as typing_module
    from src.core import omegaa_kpt1_codec as codec_module
    from src.core import omegaa_kpt1_types as kpt_types

    original_codec = codec_module.codec_kernel_proof_term_v1
    monkeypatch.setattr(codec_module, "codec_kernel_proof_term_v1", lambda *_: b"")
    result = InferV1((), sort0(), limit(max_input_bytes=1))
    assert result.payload.code is KEC1IntegrityCodeV1.CODEC_DRIFT
    monkeypatch.setattr(codec_module, "codec_kernel_proof_term_v1", original_codec)

    original_table = kpt_types.KPT1_FIELD_KINDS
    monkeypatch.setattr(kpt_types, "KPT1_FIELD_KINDS", {})
    result = InferV1((), sort0(), limit(max_input_bytes=1))
    assert result.payload.code is KEC1IntegrityCodeV1.TABLE_DRIFT
    monkeypatch.setattr(kpt_types, "KPT1_FIELD_KINDS", original_table)

    monkeypatch.setattr(types_module, "DEFAULT_KEC1_LIMITS_V1", limit())
    result = InferV1((), sort0())
    assert result.payload.code is KEC1IntegrityCodeV1.LIMIT_DRIFT
    monkeypatch.setattr(types_module, "DEFAULT_KEC1_LIMITS_V1", DEFAULT_KEC1_LIMITS_V1)

    original_infer = typing_module._infer_task
    monkeypatch.setattr(typing_module, "_infer_task", lambda *_: sort0())
    result = InferV1((), sort0())
    assert result.payload.code is KEC1IntegrityCodeV1.CODE_DRIFT
    monkeypatch.setattr(typing_module, "_infer_task", original_infer)

    origin_slot = types_module.KEC1OriginV1.tag
    monkeypatch.setattr(types_module.KEC1OriginV1, "tag", object())
    result = InferV1((), sort0())
    assert result.payload.code is KEC1IntegrityCodeV1.SLOT_DRIFT
    monkeypatch.setattr(types_module.KEC1OriginV1, "tag", origin_slot)


def test_input_resource_ordinals_offsets_and_origins() -> None:
    bytes_frame = InferV1((), sort0(), limit(max_input_bytes=4))
    assert bytes_frame.payload.kind is KEC1ResourceKindV1.INPUT_BYTES
    assert bytes_frame.payload.current == 5
    assert bytes_frame.payload.locus.space is KEC1OffsetSpaceV1.ORIGIN_FRAME
    assert bytes_frame.payload.locus.offset == 4

    bytes_wire = InferV1((), sort0(), limit(max_input_bytes=8))
    assert bytes_wire.payload.locus.space is KEC1OffsetSpaceV1.KPT_WIRE
    assert bytes_wire.payload.locus.offset == 0

    nodes = InferV1((), sort0(), limit(max_input_nodes=1))
    assert nodes.payload.kind is KEC1ResourceKindV1.INPUT_NODES
    assert nodes.payload.current == 2
    assert nodes.payload.locus.path == (0,)

    deep = T(TT.FST, (T(TT.FST, (var(),)),))
    depth = ReduceOneβ0V1(deep, limit(max_input_depth=1))
    assert depth.payload.kind is KEC1ResourceKindV1.INPUT_DEPTH
    assert depth.payload.current == 2

    large_nat = InferV1((), var(256), limit(max_input_nat_bytes=1))
    assert large_nat.payload.kind is KEC1ResourceKindV1.INPUT_NAT_BYTES
    assert large_nat.payload.locus.offset == 22

    ctor = T(TT.CTOR, (b"d" * 32, 0, (var(), var(1))))
    listed = InferV1((), ctor, limit(max_input_list_items=1))
    assert listed.payload.kind is KEC1ResourceKindV1.INPUT_LIST_ITEMS
    assert listed.payload.current == 2
    assert listed.payload.locus.offset == 70
    assert listed.payload.locus.origin.tag is KEC1OriginTagV1.TERM


def test_work_step_generated_and_output_resources() -> None:
    work = InferV1((), sort0(), limit(max_work_depth=1))
    assert work.payload.kind is KEC1ResourceKindV1.WORK_DEPTH

    generated_tie = InferV1((), sort0(), limit(max_generated_nodes=1, max_generated_bytes=1))
    assert generated_tie.payload.kind is KEC1ResourceKindV1.GENERATED_NODES
    assert generated_tie.payload.current == 2
    assert generated_tie.payload.locus.origin.tag is KEC1OriginTagV1.SYNTHETIC
    assert generated_tie.payload.locus.path == (0,)

    generated_depth = InferV1((), sort0(), limit(max_generated_depth=1))
    assert generated_depth.payload.kind is KEC1ResourceKindV1.GENERATED_DEPTH

    nested = app_identity(app_identity())
    steps = NFβ0V1(nested, limit(max_normalize_steps=1))
    assert steps.payload.kind is KEC1ResourceKindV1.NORMALIZE_STEPS
    assert steps.payload.current == 2

    output = WHNFβ0V1(sort0(), limit(max_output_nodes=1))
    assert output.payload.kind is KEC1ResourceKindV1.OUTPUT_NODES
    assert output.payload.locus.origin.tag is KEC1OriginTagV1.OUTPUT


def test_output_freshening_generated_resource_precedes_output_resource() -> None:
    result = WHNFβ0V1(sort0(), limit(max_generated_nodes=1, max_output_nodes=1))
    assert result.tag is KEC1ResultTagV1.RESOURCE
    assert result.payload.kind is KEC1ResourceKindV1.GENERATED_NODES
    assert result.payload.locus.origin.tag is KEC1OriginTagV1.SYNTHETIC


def _ids(root: T) -> set[int]:
    result: set[int] = set()
    stack: list[object] = [root]
    while stack:
        node = stack.pop()
        assert id(node) not in result
        result.add(id(node))
        if type(node) is L:
            stack.extend(reversed(node.fields))
            continue
        assert type(node) is T
        for kind, value in zip(KPT1_FIELD_KINDS[node.tag], node.fields, strict=True):
            if kind in {"term", "level"}:
                stack.append(value)
            elif kind == "terms":
                stack.extend(reversed(value))
    return result


def test_positive_payload_is_fresh_deep_unshared_snapshot() -> None:
    source = sort0()
    source_ids = _ids(source)
    first = WHNFβ0V1(source)
    second = WHNFβ0V1(sort0())
    assert first.tag is second.tag is KEC1ResultTagV1.NORMAL
    first_ids = _ids(first.payload)
    second_ids = _ids(second.payload)
    assert source_ids.isdisjoint(first_ids)
    assert first_ids.isdisjoint(second_ids)


def test_require_normal_resource_precedes_semantic_refusal() -> None:
    result = RequireNormalβ0V1(var(256), limit(max_input_nat_bytes=1))
    assert result.tag is KEC1ResultTagV1.RESOURCE
    assert result.payload.kind is KEC1ResourceKindV1.INPUT_NAT_BYTES


def test_exact_source_root_dag_and_manifest_order() -> None:
    assert KEC1_SOURCE_PATHS_V1 == tuple(sorted(KEC1_SOURCE_PATHS_V1))
    assert len(KEC1_SOURCE_PATHS_V1) == 8 == len(set(KEC1_SOURCE_PATHS_V1))
    root = Path(__file__).parents[1]
    manifest = len(KEC1_SOURCE_PATHS_V1).to_bytes(8, "big") + b"".join(
        frame(name.encode()) + frame((root / name).read_bytes()) for name in KEC1_SOURCE_PATHS_V1
    )
    kpt = bytes.fromhex("55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a")
    source = sha256(
        frame(b"omegaa.empty-core-calculus-source.v1") + frame(kpt) + frame(kcc1_source_root_v1()) + frame(manifest)
    ).digest()
    assert empty_core_calculus_source_root_v1() == source
    identity = sha256(
        frame(b"omegaa.empty-core-calculus.v1")
        + frame(source)
        + frame(kcc1_empty_config_id_v1())
        + frame(KEC1_EQUATION_BYTES_V1)
    ).digest()
    assert empty_core_calculus_id_v1() == identity

"""Strict B/H repair regressions for the explicit KEC1 machine."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from src.core.omegaa_kec1_builder import Builder
from src.core.omegaa_kec1_common import Engine, WorkFactory, WorkGenerator, WorkMachine, locus, origin_v1, work_request
from src.core.omegaa_kec1_context import prepare_inputs
from src.core.omegaa_kec1_shift import shift_task
from src.core.omegaa_kec1_types import (
    DEFAULT_KEC1_LIMITS_V1,
    KEC1ApiV1,
    KEC1OffsetSpaceV1,
    KEC1OriginTagV1,
    KEC1RefusalCodeV1,
    KEC1ResourceKindV1,
    KEC1ResultTagV1,
)
from src.core.omegaa_kec1_typing import CheckV1, InferV1, NFβ0V1, ReduceOneβ0V1, WHNFβ0V1
from src.core.omegaa_kpt1_codec import codec_kernel_proof_term_v1
from src.core.omegaa_kpt1_types import (
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


def limits(**changes: int):
    return replace(DEFAULT_KEC1_LIMITS_V1, **changes)


def same(left: T, right: T) -> bool:
    return codec_kernel_proof_term_v1(left) == codec_kernel_proof_term_v1(right)


def test_refusal_loci_expected_sort_pi_sigma_and_mismatch() -> None:
    bad_sort = InferV1((), T(TT.PI, (T(TT.REFL, (sort0(),)), sort0())))
    assert bad_sort.payload.code is KEC1RefusalCodeV1.EXPECTED_SORT
    assert bad_sort.payload.locus.origin.tag is KEC1OriginTagV1.TERM
    assert bad_sort.payload.locus.path == (0,)
    assert bad_sort.payload.locus.space is KEC1OffsetSpaceV1.KPT_WIRE

    bad_pi = InferV1((), T(TT.APP, (sort0(), sort0())))
    assert bad_pi.payload.code is KEC1RefusalCodeV1.EXPECTED_PI
    assert bad_pi.payload.locus.path == () and bad_pi.payload.locus.offset == 4

    bad_sigma = InferV1((), T(TT.FST, (sort0(),)))
    assert bad_sigma.payload.code is KEC1RefusalCodeV1.EXPECTED_SIGMA
    assert bad_sigma.payload.locus.path == () and bad_sigma.payload.locus.offset == 4

    mismatch = CheckV1((), sort0(), sort0())
    assert mismatch.payload.code is KEC1RefusalCodeV1.TYPE_MISMATCH
    assert mismatch.payload.locus.origin.tag is KEC1OriginTagV1.TERM
    assert mismatch.payload.locus.path == () and mismatch.payload.locus.offset == 4


def _binder(tag: TT) -> T:
    if tag is TT.LET:
        return T(tag, (var(), var(), var(1)))
    return T(tag, (var(), var(1)))


def _expected_binder(tag: TT, low: int, high: int) -> T:
    if tag is TT.LET:
        return T(tag, (var(low), var(low), var(high)))
    return T(tag, (var(low), var(high)))


@pytest.mark.parametrize("tag", (TT.PI, TT.LAM, TT.SIGMA, TT.LET))
def test_every_binder_shift_uses_cutoff_and_exact_paths(tag: TT) -> None:
    source = _binder(tag)
    values = tuple(getattr(DEFAULT_KEC1_LIMITS_V1, name) for name in DEFAULT_KEC1_LIMITS_V1.__slots__)
    prepared = prepare_inputs(KEC1ApiV1.REDUCE_ONE, (), source, None, values)
    engine = Engine(values)
    builder = Builder(engine)
    origin = engine.begin()
    machine: WorkMachine[T] = WorkMachine(engine)
    shifted = machine.run(
        lambda: shift_task(0, 2, prepared.term, builder, origin, prepared.where(prepared.term)),
        prepared.where(prepared.term),
    )
    assert same(shifted, _expected_binder(tag, 2, 3))
    assert builder.loci[id(shifted)].origin == origin
    assert builder.loci[id(shifted)].path == ()


@pytest.mark.parametrize("tag", (TT.PI, TT.LAM, TT.SIGMA, TT.LET))
def test_every_binder_substitution_shifts_capture_avoiding(tag: TT) -> None:
    redex = T(TT.APP, (T(TT.LAM, (sort0(), _binder(tag))), var(2)))
    result = ReduceOneβ0V1(redex)
    assert result.tag is KEC1ResultTagV1.STEP
    assert same(cast(T, result.payload), _expected_binder(tag, 2, 3))


def _listed_redex(nat: int = 0) -> T:
    chosen = T(TT.CTOR, (b"d" * 32, nat, (var(), var(1))))
    return T(TT.FST, (T(TT.PAIR, (chosen, sort0())),))


def _nat_redex() -> T:
    return T(TT.FST, (T(TT.PAIR, (var(256), sort0())),))


def test_generated_and_output_list_nat_caps_and_ties() -> None:
    generated_list = ReduceOneβ0V1(_listed_redex(), limits(max_generated_list_items=1))
    assert generated_list.payload.kind is KEC1ResourceKindV1.GENERATED_LIST_ITEMS
    assert generated_list.payload.current == 2

    generated_nat = ReduceOneβ0V1(_nat_redex(), limits(max_generated_nat_bytes=1))
    assert generated_nat.payload.kind is KEC1ResourceKindV1.GENERATED_NAT_BYTES
    assert generated_nat.payload.current == 2

    generated_tie = ReduceOneβ0V1(_listed_redex(256), limits(max_generated_list_items=1, max_generated_nat_bytes=1))
    assert generated_tie.payload.kind is KEC1ResourceKindV1.GENERATED_LIST_ITEMS

    output_list = ReduceOneβ0V1(_listed_redex(), limits(max_output_list_items=1))
    assert output_list.payload.kind is KEC1ResourceKindV1.OUTPUT_LIST_ITEMS
    assert output_list.payload.locus.origin.tag is KEC1OriginTagV1.OUTPUT

    output_nat = ReduceOneβ0V1(_nat_redex(), limits(max_output_nat_bytes=1))
    assert output_nat.payload.kind is KEC1ResourceKindV1.OUTPUT_NAT_BYTES

    output_tie = ReduceOneβ0V1(_listed_redex(256), limits(max_output_list_items=1, max_output_nat_bytes=1))
    assert output_tie.payload.kind is KEC1ResourceKindV1.OUTPUT_LIST_ITEMS

    input_tie = InferV1(
        (), T(TT.CTOR, (b"d" * 32, 256, (var(), var(1)))), limits(max_input_list_items=1, max_input_nat_bytes=1)
    )
    assert input_tie.payload.kind is KEC1ResourceKindV1.INPUT_LIST_ITEMS


def test_remaining_generated_and_output_phase_caps() -> None:
    generated_bytes = WHNFβ0V1(sort0(), limits(max_generated_bytes=1))
    assert generated_bytes.payload.kind is KEC1ResourceKindV1.GENERATED_BYTES

    deep = T(TT.FST, (T(TT.FST, (var(),)),))
    output_depth = WHNFβ0V1(deep, limits(max_output_depth=1))
    assert output_depth.payload.kind is KEC1ResourceKindV1.OUTPUT_DEPTH

    output_bytes = WHNFβ0V1(sort0(), limits(max_output_bytes=1))
    assert output_bytes.payload.kind is KEC1ResourceKindV1.OUTPUT_BYTES


def test_input_gate_precedes_owned_snapshot_allocation(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core import omegaa_kec1_context as context_module

    calls = 0

    def counted(*_args: object) -> T:
        nonlocal calls
        calls += 1
        return var()

    monkeypatch.setattr(context_module, "snapshot_term", counted)
    values = list(getattr(DEFAULT_KEC1_LIMITS_V1, name) for name in DEFAULT_KEC1_LIMITS_V1.__slots__)
    values[1] = 1
    with pytest.raises(Exception) as caught:
        prepare_inputs(KEC1ApiV1.INFER, (), sort0(), None, tuple(values))
    assert type(caught.value).__name__ == "_Resource"
    assert calls == 0

    monkeypatch.undo()
    byte_first = InferV1((), sort0(), limits(max_input_bytes=1, max_input_nodes=1, max_input_depth=1))
    assert byte_first.payload.kind is KEC1ResourceKindV1.INPUT_BYTES


def test_second_normalization_step_retains_synthetic_redex_locus() -> None:
    inner = T(TT.APP, (T(TT.LAM, (sort0(), var())), sort0()))
    outer = T(TT.APP, (T(TT.LAM, (sort0(), var())), inner))
    result = NFβ0V1(outer, limits(max_normalize_steps=1))
    assert result.payload.kind is KEC1ResourceKindV1.NORMALIZE_STEPS
    assert result.payload.current == 2
    assert result.payload.locus.origin.tag is KEC1OriginTagV1.SYNTHETIC
    assert result.payload.locus.origin.index > 0
    assert result.payload.locus.path == ()


def test_prepared_snapshot_ignores_post_capture_caller_mutation() -> None:
    from src.core.omegaa_kec1_typing import _public_nf_task

    caller = T(TT.FST, (sort0(),))
    values = tuple(getattr(DEFAULT_KEC1_LIMITS_V1, name) for name in DEFAULT_KEC1_LIMITS_V1.__slots__)
    prepared = prepare_inputs(KEC1ApiV1.NF, (), caller, None, values)
    vars(T)["tag"].__set__(caller, TT.VAR)
    vars(T)["fields"].__set__(caller, (999,))
    engine = Engine(values)
    builder = Builder(engine)
    machine: WorkMachine[object] = WorkMachine(engine)
    result = machine.run(
        lambda: _public_nf_task(prepared, builder),
        prepared.where(prepared.term),
    )
    assert result.tag is KEC1ResultTagV1.NORMAL
    assert cast(T, result.payload).tag is TT.FST


def test_imported_helper_and_builder_method_drift_fail_before_semantics(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core import omegaa_kec1_builder as builder_module
    from src.core import omegaa_kec1_context as context_module
    from src.core import omegaa_kec1_normalize as normalize_module
    from src.core import omegaa_kec1_typing as typing_module

    monkeypatch.setattr(normalize_module, "term_slot", lambda *_: (TT.VAR, (0,)))
    drift = InferV1((), sort0())
    assert drift.payload.code.name == "CODE_DRIFT"
    monkeypatch.undo()

    monkeypatch.setattr(builder_module.Builder, "term", lambda *_: var())
    method_drift = InferV1((), sort0())
    assert method_drift.payload.code.name == "CODE_DRIFT"
    monkeypatch.undo()

    monkeypatch.setattr(context_module, "KPT1_FIELD_KINDS", {})
    alias_drift = InferV1((), sort0())
    assert alias_drift.payload.code.name == "CODE_DRIFT"
    monkeypatch.undo()

    monkeypatch.setattr(typing_module, "_ALL_BINDINGS", ())
    seal_drift = InferV1((), sort0())
    assert seal_drift.payload.code.name == "CODE_DRIFT"


def test_lifo_gate_precedes_batch_allocation_and_public_depth_is_exact() -> None:
    values = list(getattr(DEFAULT_KEC1_LIMITS_V1, name) for name in DEFAULT_KEC1_LIMITS_V1.__slots__)
    values[5] = 1
    engine = Engine(tuple(values))
    machine: WorkMachine[object] = WorkMachine(engine)
    calls = 0
    where = locus(origin_v1(KEC1OriginTagV1.TERM))

    def root() -> WorkGenerator[object]:
        def allocate() -> tuple[WorkFactory, ...]:
            nonlocal calls
            calls += 1
            return ()

        yield work_request(2, where, allocate)
        return None

    with pytest.raises(Exception) as caught:
        machine.run(root, where)
    assert type(caught.value).__name__ == "_Resource"
    assert calls == 0

    for allowed in range(1, 5):
        result = InferV1((), sort0(), limits(max_work_depth=allowed))
        assert result.payload.kind is KEC1ResourceKindV1.WORK_DEPTH
        assert result.payload.allowed == allowed
        assert result.payload.current == allowed + 1
    assert InferV1((), sort0(), limits(max_work_depth=5)).tag is KEC1ResultTagV1.INFERRED


def test_semantic_lifo_exposes_exact_frame_kinds_and_real_batch() -> None:
    from src.core.omegaa_kec1_typing import _public_infer_task

    term = T(TT.PI, (sort0(), sort0()))
    values = tuple(getattr(DEFAULT_KEC1_LIMITS_V1, name) for name in DEFAULT_KEC1_LIMITS_V1.__slots__)
    prepared = prepare_inputs(KEC1ApiV1.INFER, (), term, None, values)
    engine = Engine(values)
    builder = Builder(engine)
    machine: WorkMachine[object] = WorkMachine(engine)
    result = machine.run(
        lambda: _public_infer_task(prepared, builder),
        prepared.where(prepared.term),
    )
    assert result.tag is KEC1ResultTagV1.INFERRED
    kinds = {kind for kind, _depth in machine.trace}
    assert {"WF", "INFER", "HEAD", "REBUILD", "OUTPUT"} <= kinds
    assert all(kind in {"WF", "INFER", "CHECK", "HEAD", "REDUCE", "REBUILD", "OUTPUT"} for kind in kinds)
    assert any(count == 2 for _depth, count in machine.batches)


def test_manifest_component_symlink_and_parent_path_fail_closed(tmp_path: Path) -> None:
    from src.core.omegaa_kec1_typing import _manifest_from

    real = tmp_path / "real"
    real.mkdir()
    (real / "x.py").write_text("x=1\n")
    (tmp_path / "link").symlink_to(real, target_is_directory=True)
    with pytest.raises(OSError):
        _manifest_from(("link/x.py",), tmp_path)
    with pytest.raises(ValueError):
        _manifest_from(("../real/x.py",), tmp_path)

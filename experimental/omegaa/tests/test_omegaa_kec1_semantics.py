"""Focused exact bidirectional and beta-zero behavior for KEC1."""

from __future__ import annotations

from src.core.omegaa_kec1_types import (
    KEC1RefusalCodeV1,
    KEC1ResultTagV1,
)
from src.core.omegaa_kec1_typing import (
    CheckV1,
    InferV1,
    NFβ0V1,
    ReduceOneβ0V1,
    RequireNormalβ0V1,
    WHNFβ0V1,
)
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


def app_identity() -> T:
    return T(TT.APP, (T(TT.LAM, (sort0(), var())), sort0()))


def wire(term: T) -> bytes:
    return codec_kernel_proof_term_v1(term)


def test_infer_var_sort_pi_sigma_lambda_and_app() -> None:
    inferred_var = InferV1((sort0(),), var())
    assert inferred_var.tag is KEC1ResultTagV1.INFERRED
    assert wire(inferred_var.payload) == wire(sort0())

    inferred_sort = InferV1((), sort0())
    assert inferred_sort.tag is KEC1ResultTagV1.INFERRED
    assert inferred_sort.payload.tag is TT.SORT
    assert inferred_sort.payload.fields[0].tag is LT.SUCC

    for tag in (TT.PI, TT.SIGMA):
        result = InferV1((), T(tag, (sort0(), sort0())))
        assert result.tag is KEC1ResultTagV1.INFERRED
        assert result.payload.tag is TT.SORT
        assert result.payload.fields[0].tag is LT.MAX

    lam = T(TT.LAM, (sort0(), var()))
    inferred_lam = InferV1((), lam)
    assert inferred_lam.tag is KEC1ResultTagV1.INFERRED
    assert inferred_lam.payload.tag is TT.PI

    typed_app = T(TT.APP, (T(TT.LAM, (sort0(), var())), var()))
    inferred_app = InferV1((sort0(),), typed_app)
    assert inferred_app.tag is KEC1ResultTagV1.INFERRED
    assert wire(inferred_app.payload) == wire(sort0())


def test_dependent_fst_snd_let_eq_and_refl_rules() -> None:
    sigma_context = (T(TT.SIGMA, (sort0(), sort0())),)
    fst = InferV1(sigma_context, T(TT.FST, (var(),)))
    snd = InferV1((T(TT.SIGMA, (sort0(), sort0())),), T(TT.SND, (var(),)))
    assert fst.tag is snd.tag is KEC1ResultTagV1.INFERRED
    assert wire(fst.payload) == wire(sort0()) == wire(snd.payload)

    let = T(TT.LET, (sort0(), var(), var()))
    inferred_let = InferV1((sort0(),), let)
    assert inferred_let.tag is KEC1ResultTagV1.INFERRED
    assert wire(inferred_let.payload) == wire(sort0())

    equality = T(TT.EQ, (sort0(), var(), var()))
    inferred_eq = InferV1((sort0(),), equality)
    assert inferred_eq.tag is KEC1ResultTagV1.INFERRED
    assert wire(inferred_eq.payload) == wire(sort0())

    refl = T(TT.REFL, (var(),))
    inferred_refl = InferV1((sort0(),), refl)
    assert inferred_refl.tag is KEC1ResultTagV1.INFERRED
    assert inferred_refl.payload.tag is TT.EQ


def test_check_lambda_pair_and_generic() -> None:
    expected_pi = T(TT.PI, (sort0(), sort0()))
    checked_lam = CheckV1((), T(TT.LAM, (sort0(), var())), expected_pi)
    assert checked_lam.tag is KEC1ResultTagV1.CHECKED
    expected_sigma = T(TT.SIGMA, (sort0(), sort0()))
    checked_pair = CheckV1((sort0(),), T(TT.PAIR, (var(), var())), expected_sigma)
    assert checked_pair.tag is KEC1ResultTagV1.CHECKED
    checked_generic = CheckV1((sort0(),), var(), sort0())
    assert checked_generic.tag is KEC1ResultTagV1.CHECKED


def test_refusal_rules_and_ownership_classes() -> None:
    unscoped = InferV1((), var())
    assert unscoped.tag is KEC1ResultTagV1.REFUSAL
    assert unscoped.payload.code is KEC1RefusalCodeV1.UNSCOPED
    pair = InferV1((), T(TT.PAIR, (sort0(), sort0())))
    assert pair.payload.code is KEC1RefusalCodeV1.CANNOT_INFER
    for tag, code, fields in (
        (TT.CONST, KEC1RefusalCodeV1.EMPTY_DEPENDENCY, (b"x" * 32,)),
        (TT.CTOR, KEC1RefusalCodeV1.EMPTY_DEPENDENCY, (b"x" * 32, 0, ())),
        (TT.REC, KEC1RefusalCodeV1.EMPTY_DEPENDENCY, (b"x" * 32, sort0(), (), sort0())),
        (TT.J, KEC1RefusalCodeV1.J_RULE_UNFROZEN, tuple(sort0() for _ in range(6))),
    ):
        result = InferV1((), T(tag, fields))
        assert result.tag is KEC1ResultTagV1.REFUSAL
        assert result.payload.code is code


def test_reduce_root_then_children_and_whnf_head_only() -> None:
    beta = ReduceOneβ0V1(app_identity())
    assert beta.tag is KEC1ResultTagV1.STEP
    assert wire(beta.payload) == wire(sort0())
    zeta = ReduceOneβ0V1(T(TT.LET, (sort0(), sort0(), var())))
    assert zeta.tag is KEC1ResultTagV1.STEP
    assert wire(zeta.payload) == wire(sort0())
    fst = ReduceOneβ0V1(T(TT.FST, (T(TT.PAIR, (sort0(), sort0())),)))
    snd = ReduceOneβ0V1(T(TT.SND, (T(TT.PAIR, (sort0(), sort0())),)))
    assert wire(fst.payload) == wire(sort0()) == wire(snd.payload)

    nested = T(TT.APP, (T(TT.LAM, (sort0(), var())), app_identity()))
    root_first = ReduceOneβ0V1(nested)
    assert root_first.tag is KEC1ResultTagV1.STEP
    assert root_first.payload.tag is TT.APP
    full = NFβ0V1(nested)
    assert full.tag is KEC1ResultTagV1.NORMAL
    assert wire(full.payload) == wire(sort0())

    neutral = T(TT.APP, (var(), app_identity()))
    whnf = WHNFβ0V1(neutral)
    assert whnf.tag is KEC1ResultTagV1.NORMAL
    assert wire(whnf.payload) == wire(neutral)


def test_substitution_capture_and_left_child_order() -> None:
    under_binder = T(
        TT.APP,
        (T(TT.LAM, (sort0(), T(TT.LAM, (sort0(), var(1))))), var()),
    )
    captured = ReduceOneβ0V1(under_binder)
    assert captured.tag is KEC1ResultTagV1.STEP
    assert wire(captured.payload) == wire(T(TT.LAM, (sort0(), var(1))))

    decremented = ReduceOneβ0V1(T(TT.APP, (T(TT.LAM, (sort0(), var(2))), var())))
    assert wire(decremented.payload) == wire(var(1))

    pair = T(TT.PAIR, (app_identity(), app_identity()))
    left = ReduceOneβ0V1(pair)
    assert left.tag is KEC1ResultTagV1.STEP
    first, second = left.payload.fields
    assert wire(first) == wire(sort0())
    assert wire(second) == wire(app_identity())


def test_require_normal_uses_first_unsigned_difference() -> None:
    rejected = RequireNormalβ0V1(app_identity())
    assert rejected.tag is KEC1ResultTagV1.REFUSAL
    assert rejected.payload.code is KEC1RefusalCodeV1.NOT_NORMAL
    original = wire(app_identity())
    normal = wire(sort0())
    expected = next(
        (i for i in range(min(len(original), len(normal))) if original[i] != normal[i]), min(len(original), len(normal))
    )
    assert rejected.payload.locus.offset == expected
    assert RequireNormalβ0V1(sort0()).tag is KEC1ResultTagV1.CHECKED


def test_bounded_differential_identity_evaluator() -> None:
    for depth in range(1, 7):
        term = sort0()
        for _ in range(depth):
            term = T(TT.APP, (T(TT.LAM, (sort0(), var())), term))
        result = NFβ0V1(term)
        assert result.tag is KEC1ResultTagV1.NORMAL
        assert wire(result.payload) == wire(sort0())

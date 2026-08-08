"""Hostile KIE1 class, slot, alias, callback, forgery, and boundary tests."""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import Callable, cast

import pytest

import src.core.omegaa_kci1_types as kci_types
import src.core.omegaa_kie1_binding as binding_module
import src.core.omegaa_kie1_common as common_module
import src.core.omegaa_kie1_offsets as offsets_module
import src.core.omegaa_kie1_prepare as prepare_module
import src.core.omegaa_kie1_types as types_module
from src.core.omegaa_kci1_builder import build_checker_input_syntax_v1
from src.core.omegaa_kci1_types import CheckerInputSyntaxV1
from src.core.omegaa_keb1_builder import expected_binding_v1
from src.core.omegaa_keb1_types import ExpectedBindingSyntaxV1
from src.core.omegaa_kie1_binding import BindExpectedInputV1
from src.core.omegaa_kie1_common import (
    KIE1IntegrityErrorV1,
    KIEPayloadOriginV1,
    KIEPrepareCodeV1,
)
from src.core.omegaa_kie1_prepare import InspectKIEPrepareResultV1
from src.core.omegaa_kie1_types import (
    BoundExpectedInputV1,
    KIEKPTDecodeAtInputV1,
    KIEPrepareErrorV1,
    _KIEBoundResultV1,
    _KIEBoundViewV1,
    _KIEErrorViewV1,
    _KIEInitErrorResultV1,
)
from src.core.omegaa_kpt1_common import KPT1DecodeCodeV1
from src.core.omegaa_kpt1_types import KernelTermTagV1, kernel_term_v1

ROOT = Path(__file__).parents[1]


def _binding() -> ExpectedBindingSyntaxV1:
    return expected_binding_v1(kernel_term_v1(KernelTermTagV1.VAR, 0))


def _input(expected: bytes) -> CheckerInputSyntaxV1:
    return build_checker_input_syntax_v1(expected, b"opaque")


def _bound_result() -> _KIEBoundResultV1:
    binding = _binding()
    result = BindExpectedInputV1(_input(binding.expected_wire), binding)
    assert type(result) is _KIEBoundResultV1
    return result


class _Bomb:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, *_args: object, **_kwargs: object) -> object:
        self.calls += 1
        raise AssertionError("hostile callback executed")


def test_wrong_outer_types_and_subclasses_refuse_before_field_access() -> None:
    binding = _binding()
    with pytest.raises(KIE1IntegrityErrorV1):
        BindExpectedInputV1(object(), binding)
    with pytest.raises(KIE1IntegrityErrorV1):
        BindExpectedInputV1(_input(binding.expected_wire), object())

    class InputSubclass(CheckerInputSyntaxV1):  # type: ignore[misc]
        pass

    forged = object.__new__(InputSubclass)
    object.__setattr__(forged, "expected_bytes", binding.expected_wire)
    object.__setattr__(forged, "term_bytes", b"opaque")
    with pytest.raises(KIE1IntegrityErrorV1):
        BindExpectedInputV1(forged, binding)

    class BindingSubclass(ExpectedBindingSyntaxV1):  # type: ignore[misc]
        pass

    forged_binding = object.__new__(BindingSubclass)
    object.__setattr__(forged_binding, "expected_term", binding.expected_term)
    object.__setattr__(forged_binding, "expected_wire", binding.expected_wire)
    with pytest.raises(KIE1IntegrityErrorV1):
        BindExpectedInputV1(_input(binding.expected_wire), forged_binding)


def test_forged_exact_bound_is_nominal_and_revalidated_not_trusted() -> None:
    binding = _binding()
    bad_input = _input(b"not-the-wire")
    forged_bound = object.__new__(BoundExpectedInputV1)
    object.__setattr__(forged_bound, "input", bad_input)
    object.__setattr__(forged_bound, "binding", binding)
    forged_result = object.__new__(_KIEBoundResultV1)
    object.__setattr__(forged_result, "bound", forged_bound)
    with pytest.raises(KIE1IntegrityErrorV1, match="bound-mismatch"):
        InspectKIEPrepareResultV1(forged_result)


def test_forged_error_shape_is_not_authority_and_preserves_identity() -> None:
    error = object.__new__(KIEPrepareErrorV1)
    object.__setattr__(error, "code", KIEPrepareCodeV1.EXPECTED_WIRE_MISMATCH)
    object.__setattr__(error, "absolute_kci_offset", 14)
    result = object.__new__(_KIEInitErrorResultV1)
    object.__setattr__(result, "error", error)
    view = InspectKIEPrepareResultV1(result)
    error_view = cast(types_module._KIEErrorViewV1, view)
    assert error_view.original_error is error
    assert not hasattr(error_view, "authority")
    object.__setattr__(error, "absolute_kci_offset", True)
    with pytest.raises(KIE1IntegrityErrorV1):
        InspectKIEPrepareResultV1(result)


def test_result_subclasses_are_refused_and_views_are_never_reused() -> None:
    class ResultSubclass(_KIEBoundResultV1):  # type: ignore[misc]
        pass

    legitimate = _bound_result()
    forged = object.__new__(ResultSubclass)
    object.__setattr__(forged, "bound", legitimate.bound)
    with pytest.raises(KIE1IntegrityErrorV1):
        InspectKIEPrepareResultV1(forged)
    first = InspectKIEPrepareResultV1(legitimate)
    second = InspectKIEPrepareResultV1(legitimate)
    assert type(first) is type(second) is _KIEBoundViewV1
    assert first is not second


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("module", "name", "operation"),
    (
        (binding_module, "_FIRST_DIFF", lambda: BindExpectedInputV1(_input(b"x"), _binding())),
        (binding_module, "_READ_INPUTS", _bound_result),
        (offsets_module, "_BASE", lambda: offsets_module.RebaseSuppliedSemanticOriginV1(KIEPayloadOriginV1.EXPECTED, 0, b"")),
        (prepare_module, "_VALIDATE_BOUND", lambda: InspectKIEPrepareResultV1(_bound_result())),
    ),
)
def test_mutable_alias_drift_refuses_with_zero_hostile_callbacks(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    name: str,
    operation: Callable[[], object],
) -> None:
    bomb = _Bomb()
    monkeypatch.setattr(module, name, bomb)
    with pytest.raises(KIE1IntegrityErrorV1):
        operation()
    assert bomb.calls == 0


def test_dependency_class_alias_drift_refuses_before_hostile_descriptor(monkeypatch: pytest.MonkeyPatch) -> None:
    legitimate = _bound_result()
    bomb = _Bomb()
    monkeypatch.setattr(kci_types, "CheckerInputSyntaxV1", bomb)
    with pytest.raises(KIE1IntegrityErrorV1):
        InspectKIEPrepareResultV1(legitimate)
    assert bomb.calls == 0


def test_private_result_class_alias_drift_refuses_before_allocation(monkeypatch: pytest.MonkeyPatch) -> None:
    binding = _binding()
    bomb = _Bomb()
    monkeypatch.setattr(types_module, "_KIEBoundResultV1", bomb)
    with pytest.raises(KIE1IntegrityErrorV1):
        BindExpectedInputV1(_input(binding.expected_wire), binding)
    assert bomb.calls == 0


def _binding_operation() -> object:
    return BindExpectedInputV1(_input(_binding().expected_wire), _binding())


def _offset_operation() -> object:
    return offsets_module.RebaseKPTV1(
        KIEPayloadOriginV1.EXPECTED,
        (KPT1DecodeCodeV1.BAD_TAG, 0),
        b"",
    )


def _prepare_operation() -> object:
    return InspectKIEPrepareResultV1(_bound_result())


_STRUCTURAL_TABLES = (
    *(
        (binding_module, name, _binding_operation)
        for name in (
            "_INPUT_SLOTS",
            "_INPUT_DESCRIPTORS",
            "_BINDING_SLOTS",
            "_BINDING_DESCRIPTORS",
            "_OUTPUT_CLASSES",
            "_OUTPUT_SLOTS",
            "_OUTPUT_DESCRIPTORS",
            "_ALL_CLASSES",
            "_CLASS_KEYS",
            "_CLASS_INITS",
            "_CLASS_INIT_CODES",
            "_CLASS_POSTS",
            "_CLASS_POST_CODES",
            "_CLASS_FINALS",
        )
    ),
    *(
        (offsets_module, name, _offset_operation)
        for name in ("_REBASED_SLOTS", "_REBASED_DESCRIPTORS")
    ),
    *(
        (prepare_module, name, _prepare_operation)
        for name in (
            "_INPUT_DESCRIPTORS",
            "_BINDING_DESCRIPTORS",
            "_BOUND_DESCRIPTORS",
            "_ERROR_DESCRIPTORS",
            "_RESULT_CLASSES",
            "_RESULT_DESCRIPTORS",
            "_VIEW_CLASSES",
            "_VIEW_DESCRIPTORS",
            "_PROFILE_CLASSES",
            "_PROFILE_KEYS",
            "_PROFILE_INITS",
            "_PROFILE_INIT_CODES",
            "_PROFILE_POSTS",
            "_PROFILE_POST_CODES",
            "_PROFILE_FINALS",
            "_PROFILE_SLOTS",
            "_PROFILE_DESCRIPTORS",
        )
    ),
)


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("module", "name", "operation"),
    _STRUCTURAL_TABLES,
    ids=(f"{module.__name__.rsplit('.', 1)[-1]}:{name}" for module, name, _ in _STRUCTURAL_TABLES),
)
@pytest.mark.parametrize("mutation", ("empty", "short", "reversed"))  # type: ignore[untyped-decorator]
def test_every_structural_sequence_refuses_empty_length_and_order_drift(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    name: str,
    operation: Callable[[], object],
    mutation: str,
) -> None:
    original = vars(module)[name]
    assert type(original) is tuple and len(original) >= 2
    replacements = {
        "empty": (),
        "short": original[:-1],
        "reversed": tuple(reversed(original)),
    }
    monkeypatch.setattr(module, name, replacements[mutation])
    with pytest.raises(KIE1IntegrityErrorV1):
        operation()


def test_rebased_key_profile_refuses_empty_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(offsets_module, "_REBASED_KEYS", frozenset())
    with pytest.raises(KIE1IntegrityErrorV1):
        _offset_operation()


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("name", "replacement"),
    (
        ("_PREPARE_CODES", ()),
        ("_PREPARE_CODES", (KIEPrepareCodeV1.EXPECTED_WIRE_MISMATCH,) * 2),
        ("_ORIGINS", ()),
        ("_ORIGINS", common_module._ORIGINS[:-1]),
        ("_ORIGINS", tuple(reversed(common_module._ORIGINS))),
    ),
)
def test_common_enum_tables_refuse_empty_length_and_order_drift(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    replacement: tuple[object, ...],
) -> None:
    monkeypatch.setattr(common_module, name, replacement)
    with pytest.raises(KIE1IntegrityErrorV1):
        _offset_operation()


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("name", "replacement"),
    (
        ("_KPT_CODES", ()),
        ("_KPT_CODES", offsets_module._KPT_CODES[:-1]),
        ("_KPT_CODES", tuple(reversed(offsets_module._KPT_CODES))),
    ),
)
def test_kpt_enum_table_refuses_empty_length_and_order_drift(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    replacement: tuple[object, ...],
) -> None:
    monkeypatch.setattr(offsets_module, name, replacement)
    with pytest.raises(KIE1IntegrityErrorV1):
        _offset_operation()


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("module", "name"),
    (
        (common_module, "U64_LIMIT"),
        (prepare_module, "U64_LIMIT"),
        (types_module, "U64_LIMIT"),
    ),
)
def test_u64_drift_refuses_forged_error_before_acceptance(
    monkeypatch: pytest.MonkeyPatch,
    module: ModuleType,
    name: str,
) -> None:
    error = object.__new__(KIEPrepareErrorV1)
    object.__setattr__(error, "code", KIEPrepareCodeV1.EXPECTED_WIRE_MISMATCH)
    object.__setattr__(error, "absolute_kci_offset", 2**64 - 1)
    result = object.__new__(_KIEInitErrorResultV1)
    object.__setattr__(result, "error", error)
    monkeypatch.setattr(module, name, 2**64 + 1)
    with pytest.raises(KIE1IntegrityErrorV1):
        InspectKIEPrepareResultV1(result)


def test_types_constructor_refuses_u64_alias_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(types_module, "U64_LIMIT", 2**64 + 1)
    with pytest.raises(TypeError, match="kie1-prepare-error-host-shape"):
        KIEPrepareErrorV1(KIEPrepareCodeV1.EXPECTED_WIRE_MISMATCH, 0)


@pytest.mark.parametrize("index", range(11))  # type: ignore[untyped-decorator]
def test_every_kpt_decode_ordinal_drift_is_refused(index: int) -> None:
    code = KPT1DecodeCodeV1(index)
    original = object.__getattribute__(code, "_value_")
    try:
        object.__setattr__(code, "_value_", index + 100)
        with pytest.raises(KIE1IntegrityErrorV1):
            _offset_operation()
    finally:
        object.__setattr__(code, "_value_", original)


def test_forged_exact_kpt_enum_nonmember_is_refused_before_rebased_allocation() -> None:
    forged = int.__new__(KPT1DecodeCodeV1, 99)
    assert type(forged) is KPT1DecodeCodeV1
    assert all(forged is not KPT1DecodeCodeV1(index) for index in range(11))
    with pytest.raises(KIE1IntegrityErrorV1, match="kpt-code-host-shape"):
        offsets_module.RebaseKPTV1(
            KIEPayloadOriginV1.EXPECTED,
            (forged, 0),
            b"",
        )
    with pytest.raises(TypeError, match="kie1-kpt-origin-host-shape"):
        KIEKPTDecodeAtInputV1(forged, 0)


def test_no_production_codec_parser_navigation_or_memoryerror_sanitization() -> None:
    source = b"".join(
        (ROOT / name).read_bytes()
        for name in (
            "src/core/omegaa_kie1_binding.py",
            "src/core/omegaa_kie1_offsets.py",
            "src/core/omegaa_kie1_prepare.py",
        )
    ).lower()
    for forbidden in (
        b"codec_kernel_proof_term",
        b"parse_kernel_proof_term",
        b"kernelprooftermv1.fields",
        b"run(",
        b"registry",
        b"authority =",
        b"except memoryerror",
        b"except exception",
    ):
        assert forbidden not in source


def test_exact_slots_have_no_proof_tag_resource_or_capability_cells() -> None:
    assert BoundExpectedInputV1.__slots__ == ("input", "binding")
    assert KIEPrepareErrorV1.__slots__ == ("code", "absolute_kci_offset")
    assert _KIEBoundResultV1.__slots__ == ("bound",)
    assert _KIEInitErrorResultV1.__slots__ == ("error",)
    assert _KIEBoundViewV1.__slots__ == ("input", "binding")
    assert _KIEErrorViewV1.__slots__ == ("original_error",)
    assert KIEKPTDecodeAtInputV1.__slots__ == ("code", "absolute_kci_offset")

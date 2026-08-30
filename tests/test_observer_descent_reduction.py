from __future__ import annotations

from pathlib import Path

import pytest

from src.core.observer_descent_reduction import (
    best_lower_approximation,
    descent_reduces_to_best_lower,
    z4_reduction_audit,
)
from src.core.observer_descent_examples import z4_doctrine, z4_shift
from src.core.observer_descent import (
    observer_by_name,
    observer_descent,
    observer_response_map,
    transition_map,
    validate_doctrine,
)
from src.core.observer_descent_types import (
    FiniteObserver,
    FiniteObserverDoctrine,
    FiniteTransition,
)


@pytest.mark.parametrize("shift", range(4))
@pytest.mark.parametrize(
    "target_name",
    ("silence", "parity", "threshold", "phase-pair"),
)
def test_each_z4_descent_is_the_best_admitted_lower_approximation(
    shift: int,
    target_name: str,
):
    doctrine = z4_doctrine()
    assert descent_reduces_to_best_lower(
        doctrine,
        z4_shift(shift),
        observer_by_name(doctrine, target_name),
        target_doctrine=doctrine,
    )


def test_best_lower_rejects_relations_outside_the_carrier():
    doctrine = z4_doctrine()
    with pytest.raises(ValueError, match="relation-outside-carrier"):
        best_lower_approximation(doctrine, frozenset({(0, 99)}))
    with pytest.raises(TypeError, match="exact-frozenset"):
        best_lower_approximation(doctrine, {(0, 1)})  # type: ignore[arg-type]


def test_r16_finite_audit_rejects_novelty_promotion_after_reduction():
    report = z4_reduction_audit()
    assert (report.descents, report.exact_best_approximations) == (16, 16)
    assert (report.composition_rows, report.exact_precision_gaps) == (64, 64)
    assert report.promotion_status == "reduced-no-novelty-promotion"



def _five_state_partiality_fixture():
    carrier = (0, 1, 2, 3, 4)

    def observer(name: str, labels: tuple[int, ...]) -> FiniteObserver:
        return FiniteObserver(name, tuple(zip(carrier, labels, strict=True)), 0)

    doctrine = FiniteObserverDoctrine(
        "internal-diamond",
        carrier,
        (
            observer("bottom", (0, 0, 0, 0, 0)),
            observer("a", (0, 0, 1, 1, 1)),
            observer("b", (0, 1, 0, 1, 1)),
            observer("top", carrier),
        ),
    )
    raw_ambient_join = observer("ambient-join", (0, 1, 2, 3, 3))
    target_doctrine = FiniteObserverDoctrine(
        "ambient-target-chain",
        carrier,
        (
            observer("target-bottom", (0, 0, 0, 0, 0)),
            raw_ambient_join,
        ),
    )
    identity = FiniteTransition(
        "id",
        carrier,
        carrier,
        tuple(zip(carrier, carrier, strict=True)),
    )
    return carrier, doctrine, raw_ambient_join, target_doctrine, identity


def _lean_def_block(source: str, name: str) -> str:
    marker = f"def {name} "
    start = source.index(marker)
    tail = source[start:]
    ends = [
        position
        for token in ("\ndef ", "\ninductive ", "\ntheorem ", "\n#print ")
        if (position := tail.find(token, 1)) >= 0
    ]
    return tail[: min(ends)] if ends else tail


def _assert_unary_label_definition(
    lean_source: str,
    name: str,
    labels: tuple[int, ...],
) -> None:
    block = _lean_def_block(lean_source, name)
    groups: dict[int, list[int]] = {}
    for state, label in enumerate(labels):
        groups.setdefault(label, []).append(state)
    if len(groups) == 1:
        label = next(iter(groups))
        assert f"| _ => {label}" in block
        return
    for label, states in groups.items():
        pattern = " | ".join(f".s{state}" for state in states)
        assert f"| {pattern} => {label}" in block


def test_internal_join_semilattice_does_not_make_descent_total():
    _, doctrine, raw_ambient_join, target_doctrine, identity = (
        _five_state_partiality_fixture()
    )
    validate_doctrine(doctrine)
    validate_doctrine(target_doctrine)
    with pytest.raises(ValueError, match="descent-not-unique"):
        observer_descent(
            doctrine,
            identity,
            raw_ambient_join,
            target_doctrine=target_doctrine,
        )


def test_z4_exact_best_table_matches_research_lean_audit():
    doctrine = z4_doctrine()
    expected = {
        0: {
            "silence": "silence",
            "parity": "parity",
            "threshold": "threshold",
            "phase-pair": "phase-pair",
        },
        1: {
            "silence": "silence",
            "parity": "parity",
            "threshold": "silence",
            "phase-pair": "phase-pair",
        },
        2: {
            "silence": "silence",
            "parity": "parity",
            "threshold": "threshold",
            "phase-pair": "phase-pair",
        },
        3: {
            "silence": "silence",
            "parity": "parity",
            "threshold": "silence",
            "phase-pair": "phase-pair",
        },
    }
    for shift, rows in expected.items():
        for target_name, expected_name in rows.items():
            descent = observer_descent(
                doctrine,
                z4_shift(shift),
                observer_by_name(doctrine, target_name),
                target_doctrine=doctrine,
            )
            assert descent.descended_observer == expected_name

    lean_source = Path(
        "experimental/research_lean/VeyraResearchR16Z4Audit.lean"
    ).read_text(encoding="utf-8")
    assert "def z4ExpectedBest : Z4Shift → Z4Observer → Z4Observer" in lean_source
    assert "| .k0, .threshold => .threshold" in lean_source
    assert "| .k1, .threshold => .silence" in lean_source
    assert "| .k2, .threshold => .threshold" in lean_source
    assert "| .k3, .threshold => .silence" in lean_source
    assert "z4Shifts.length * z4Observers.length = 16" in lean_source
    assert "z5NoGreatestB = true" in lean_source
    assert "RESEARCH_RZ_T001_bounded_best_lower_and_partiality" in lean_source


def test_research_lean_z4_and_partiality_models_match_executable_fixtures():
    lean_source = Path(
        "experimental/research_lean/VeyraResearchR16Z4Audit.lean"
    ).read_text(encoding="utf-8")

    doctrine = z4_doctrine()
    z4_states = doctrine.carrier
    observer_ctors = {
        "silence": "silence",
        "parity": "parity",
        "threshold": "threshold",
        "phase-pair": "phasePair",
    }
    z4_labels_block = _lean_def_block(lean_source, "z4Labels")
    for observer in doctrine.observers:
        responses = observer_response_map(observer)
        labels = tuple(responses[state] for state in z4_states)
        ctor = observer_ctors[observer.name]
        if len(set(labels)) == 1:
            assert f"| .{ctor}, _ => {labels[0]}" in z4_labels_block
        else:
            for state, label in enumerate(labels):
                assert f"| .{ctor}, .s{state} => {label}" in z4_labels_block

    shift_block = _lean_def_block(lean_source, "z4ShiftApply")
    assert "| .k0, state => state" in shift_block
    for shift in range(1, 4):
        graph = transition_map(z4_shift(shift))
        for state in z4_states:
            assert (
                f"| .k{shift}, .s{state} => .s{graph[state]}"
                in shift_block
            )

    carrier, source_doctrine, raw_ambient_join, _, _ = (
        _five_state_partiality_fixture()
    )
    lean_defs = {"bottom": "z5Bottom", "a": "z5A", "b": "z5B", "top": "z5Top"}
    for observer in source_doctrine.observers:
        responses = observer_response_map(observer)
        labels = tuple(responses[state] for state in carrier)
        _assert_unary_label_definition(
            lean_source,
            lean_defs[observer.name],
            labels,
        )
    raw_responses = observer_response_map(raw_ambient_join)
    _assert_unary_label_definition(
        lean_source,
        "z5Raw",
        tuple(raw_responses[state] for state in carrier),
    )

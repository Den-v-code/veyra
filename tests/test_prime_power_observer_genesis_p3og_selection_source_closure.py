"""Hostile tests for declared P3-OG selection-source dependency closure."""

from dataclasses import replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_codec import digest
from src.core.prime_power_observer_genesis_p3og_one_shot_selection import (
    SelectionDependencyKind,
    p3og_one_shot_selection_source,
    p3og_selection_dependency_node,
    p3og_selection_source_closure,
    selector_law_digest,
    validate_p3og_one_shot_selection_source,
    validate_p3og_selection_source_closure,
)
from src.core.prime_power_observer_genesis_p3og_selection_source_closure import (
    BLIND_SEED_ROOT_ID,
    POOL_ROOT_ID,
    SELECTOR_LAW_ROOT_ID,
)


def _source(label: str = "closure"):
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
        seed_rows=(("alpha", (0, 1, 0)), ("beta", (0, 2, 0))),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )


def _pool_digest(source):
    return digest("pool", tuple(seed.seed_digest for seed in source.seeds))


def _root_nodes(source, blind, *, pool_parents=(), blind_parents=(), selector_parents=()):
    return (
        p3og_selection_dependency_node(
            POOL_ROOT_ID, SelectionDependencyKind.POOL, pool_parents, _pool_digest(source)
        ),
        p3og_selection_dependency_node(
            BLIND_SEED_ROOT_ID, SelectionDependencyKind.BLIND_SEED, blind_parents, blind
        ),
        p3og_selection_dependency_node(
            SELECTOR_LAW_ROOT_ID,
            SelectionDependencyKind.SELECTOR_LAW,
            selector_parents,
            selector_law_digest(),
        ),
    )


def test_default_declared_closure_is_bound_into_selection_source() -> None:
    source = _source()
    blind = "a" * 64
    closure = p3og_selection_source_closure(source, blind)
    assert closure.root_ids == (POOL_ROOT_ID, BLIND_SEED_ROOT_ID, SELECTOR_LAW_ROOT_ID)
    assert closure.closure_node_ids == closure.root_ids
    assert closure.forbidden_node_ids == ()
    rebuilt = validate_p3og_selection_source_closure(source, blind, closure)
    assert rebuilt == closure
    selection = p3og_one_shot_selection_source(source, blind, closure)
    assert selection.source_closure == closure
    assert validate_p3og_one_shot_selection_source(source, selection)[1] == selection


def test_direct_criterion_dependency_is_rejected() -> None:
    source = _source()
    blind = "b" * 64
    criterion = p3og_selection_dependency_node(
        "criterion", SelectionDependencyKind.DISCRIMINATION_CRITERION, (), "c" * 64
    )
    nodes = (
        criterion,
        *_root_nodes(source, blind, blind_parents=("criterion",)),
    )
    with pytest.raises(ValueError, match="forbidden-dependency"):
        p3og_selection_source_closure(source, blind, nodes)


def test_disconnected_criterion_dependency_is_rejected() -> None:
    source = _source()
    blind = "a" * 64
    criterion = p3og_selection_dependency_node(
        "criterion-disconnected",
        SelectionDependencyKind.DISCRIMINATION_CRITERION,
        (),
        "b" * 64,
    )
    nodes = (criterion, *_root_nodes(source, blind))
    with pytest.raises(ValueError, match="forbidden-dependency"):
        p3og_selection_source_closure(source, blind, nodes)


def test_disconnected_innocuous_dependency_is_rejected() -> None:
    source = _source()
    blind = "c" * 64
    transform = p3og_selection_dependency_node(
        "unused-transform",
        SelectionDependencyKind.TRANSFORM,
        (),
        "d" * 64,
    )
    nodes = (transform, *_root_nodes(source, blind))
    with pytest.raises(ValueError, match="disconnected-dependency"):
        p3og_selection_source_closure(source, blind, nodes)


def test_transitive_hashed_criterion_dependency_is_rejected() -> None:
    source = _source()
    blind = "d" * 64
    criterion = p3og_selection_dependency_node(
        "criterion", SelectionDependencyKind.DISCRIMINATION_CRITERION, (), "e" * 64
    )
    transform = p3og_selection_dependency_node(
        "hash-transform",
        SelectionDependencyKind.TRANSFORM,
        ("criterion",),
        "f" * 64,
    )
    nodes = (
        criterion,
        transform,
        *_root_nodes(source, blind, blind_parents=("hash-transform",)),
    )
    with pytest.raises(ValueError, match="forbidden-dependency"):
        p3og_selection_source_closure(source, blind, nodes)


def test_target_dependency_into_pool_is_rejected() -> None:
    source = _source()
    blind = "1" * 64
    target = p3og_selection_dependency_node(
        "target", SelectionDependencyKind.TARGET, (), "2" * 64
    )
    nodes = (target, *_root_nodes(source, blind, pool_parents=("target",)))
    with pytest.raises(ValueError, match="forbidden-dependency"):
        p3og_selection_source_closure(source, blind, nodes)


def test_dependency_cycle_is_rejected_even_when_kinds_are_innocuous() -> None:
    source = _source()
    blind = "3" * 64
    left = p3og_selection_dependency_node(
        "left", SelectionDependencyKind.TRANSFORM, ("right",), "4" * 64
    )
    right = p3og_selection_dependency_node(
        "right", SelectionDependencyKind.TRANSFORM, ("left",), "5" * 64
    )
    nodes = (left, right, *_root_nodes(source, blind, blind_parents=("left",)))
    with pytest.raises(ValueError, match="cycle"):
        p3og_selection_source_closure(source, blind, nodes)


def test_foreign_source_closure_splice_is_rejected() -> None:
    source = _source()
    foreign = _source("foreign")
    blind = "6" * 64
    closure = p3og_selection_source_closure(source, blind)
    with pytest.raises(ValueError):
        validate_p3og_selection_source_closure(foreign, blind, closure)


def test_selector_root_payload_drift_is_rejected() -> None:
    source = _source()
    blind = "7" * 64
    roots = list(_root_nodes(source, blind))
    roots[2] = p3og_selection_dependency_node(
        SELECTOR_LAW_ROOT_ID,
        SelectionDependencyKind.SELECTOR_LAW,
        (),
        "8" * 64,
    )
    with pytest.raises(ValueError, match="root-drift"):
        p3og_selection_source_closure(source, blind, tuple(roots))


def test_selection_source_rejects_tampered_nested_closure() -> None:
    source = _source()
    blind = "9" * 64
    closure = p3og_selection_source_closure(source, blind)
    forged = replace(closure, closure_node_ids=closure.closure_node_ids[:-1])
    selection = p3og_one_shot_selection_source(source, blind, closure)
    forged_selection = replace(selection, source_closure=forged)
    with pytest.raises(ValueError):
        validate_p3og_one_shot_selection_source(source, forged_selection)

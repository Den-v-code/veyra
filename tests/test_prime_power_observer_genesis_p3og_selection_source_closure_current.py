"""Hostile regressions for declared P3-OG selection dependency closure."""

from dataclasses import replace

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_codec import digest
from src.core.prime_power_observer_genesis_p3og_selection_source_closure import (
    BLIND_SEED_ROOT_ID,
    POOL_ROOT_ID,
    SELECTOR_LAW_ROOT_ID,
    p3og_selection_dependency_node,
    p3og_selection_source_closure,
    selector_law_digest,
    validate_p3og_selection_source_closure,
)
from src.core.prime_power_observer_genesis_p3og_selection_source_closure_types import (
    P3OG_SELECTION_SOURCE_CLOSURE_BOUNDARY,
    P3OG_SELECTION_SOURCE_CLOSURE_NONCLAIMS,
    SelectionDependencyKind,
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


def _root_nodes(
    source,
    blind,
    *,
    pool_parents=(),
    blind_parents=(),
    selector_parents=(),
):
    return (
        p3og_selection_dependency_node(
            POOL_ROOT_ID,
            SelectionDependencyKind.POOL,
            pool_parents,
            _pool_digest(source),
        ),
        p3og_selection_dependency_node(
            BLIND_SEED_ROOT_ID,
            SelectionDependencyKind.BLIND_SEED,
            blind_parents,
            blind,
        ),
        p3og_selection_dependency_node(
            SELECTOR_LAW_ROOT_ID,
            SelectionDependencyKind.SELECTOR_LAW,
            selector_parents,
            selector_law_digest(),
        ),
    )


def test_default_closure_is_minimal_replayable_and_explicitly_narrow() -> None:
    source = _source()
    blind = "a" * 64
    closure = p3og_selection_source_closure(source, blind)
    assert set(closure.closure_node_ids) == {
        POOL_ROOT_ID,
        BLIND_SEED_ROOT_ID,
        SELECTOR_LAW_ROOT_ID,
    }
    assert closure.forbidden_node_ids == ()
    assert closure.boundary == P3OG_SELECTION_SOURCE_CLOSURE_BOUNDARY
    assert "full-def-og-002-discharge" in P3OG_SELECTION_SOURCE_CLOSURE_NONCLAIMS
    assert validate_p3og_selection_source_closure(source, blind, closure) == closure


@pytest.mark.parametrize(
    "kind",
    [
        SelectionDependencyKind.DISCRIMINATION_CRITERION,
        SelectionDependencyKind.TARGET,
        SelectionDependencyKind.SELECTED_RESPONSE,
        SelectionDependencyKind.LATER_STATUS,
        SelectionDependencyKind.THEOREM_CONCLUSION,
    ],
)
def test_every_outcome_bearing_dependency_kind_is_rejected_from_root_ancestry(kind) -> None:
    source = _source()
    blind = "b" * 64
    forbidden = p3og_selection_dependency_node(
        "forbidden",
        kind,
        (),
        "c" * 64,
    )
    nodes = (
        forbidden,
        *_root_nodes(source, blind, selector_parents=("forbidden",)),
    )
    with pytest.raises(ValueError, match="forbidden-dependency"):
        p3og_selection_source_closure(source, blind, nodes)


def test_transitive_hashed_criterion_dependency_is_rejected() -> None:
    source = _source()
    blind = "d" * 64
    criterion = p3og_selection_dependency_node(
        "criterion",
        SelectionDependencyKind.DISCRIMINATION_CRITERION,
        (),
        "e" * 64,
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
        "target",
        SelectionDependencyKind.TARGET,
        (),
        "2" * 64,
    )
    nodes = (target, *_root_nodes(source, blind, pool_parents=("target",)))
    with pytest.raises(ValueError, match="forbidden-dependency"):
        p3og_selection_source_closure(source, blind, nodes)


def test_unrelated_future_node_is_not_falsely_counted_as_root_dependency() -> None:
    source = _source()
    blind = "3" * 64
    future = p3og_selection_dependency_node(
        "later-result",
        SelectionDependencyKind.LATER_STATUS,
        (),
        "4" * 64,
    )
    closure = p3og_selection_source_closure(
        source,
        blind,
        (future, *_root_nodes(source, blind)),
    )
    assert "later-result" not in closure.closure_node_ids
    assert closure.forbidden_node_ids == ()


def test_dependency_cycle_is_rejected_even_outside_root_closure() -> None:
    source = _source()
    blind = "5" * 64
    left = p3og_selection_dependency_node(
        "left",
        SelectionDependencyKind.TRANSFORM,
        ("right",),
        "6" * 64,
    )
    right = p3og_selection_dependency_node(
        "right",
        SelectionDependencyKind.TRANSFORM,
        ("left",),
        "7" * 64,
    )
    nodes = (left, right, *_root_nodes(source, blind))
    with pytest.raises(ValueError, match="cycle"):
        p3og_selection_source_closure(source, blind, nodes)


def test_unknown_parent_is_rejected_before_traversal() -> None:
    source = _source()
    blind = "8" * 64
    nodes = _root_nodes(source, blind, selector_parents=("missing",))
    with pytest.raises(ValueError, match="unknown-parent"):
        p3og_selection_source_closure(source, blind, nodes)


def test_selector_root_payload_drift_is_rejected() -> None:
    source = _source()
    blind = "9" * 64
    roots = list(_root_nodes(source, blind))
    roots[2] = p3og_selection_dependency_node(
        SELECTOR_LAW_ROOT_ID,
        SelectionDependencyKind.SELECTOR_LAW,
        (),
        "0" * 64,
    )
    with pytest.raises(ValueError, match="root-drift"):
        p3og_selection_source_closure(source, blind, tuple(roots))


def test_foreign_source_splice_is_rejected() -> None:
    source = _source()
    foreign = _source("foreign")
    blind = "a" * 64
    closure = p3og_selection_source_closure(source, blind)
    with pytest.raises(ValueError):
        validate_p3og_selection_source_closure(foreign, blind, closure)


def test_nested_closure_tampering_is_rejected() -> None:
    source = _source()
    blind = "b" * 64
    closure = p3og_selection_source_closure(source, blind)
    forged = replace(closure, closure_node_ids=closure.closure_node_ids[:-1])
    with pytest.raises(ValueError):
        validate_p3og_selection_source_closure(source, blind, forged)


def test_node_order_does_not_change_semantic_closure_or_digest() -> None:
    source = _source()
    blind = "c" * 64
    transform = p3og_selection_dependency_node(
        "transform",
        SelectionDependencyKind.TRANSFORM,
        (),
        "d" * 64,
    )
    roots = _root_nodes(source, blind, blind_parents=("transform",))
    first = p3og_selection_source_closure(source, blind, (transform, *roots))
    second = p3og_selection_source_closure(source, blind, (*reversed(roots), transform))
    assert first == second

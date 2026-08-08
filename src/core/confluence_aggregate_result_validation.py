"""Hostile-safe raw-input result revalidation for P1-C2."""

from __future__ import annotations

import logging

from .confluence_aggregate_result_exact import (
    exact_fields, exact_instance, exact_optional_string, reject as _reject,
)
from .confluence_aggregate_runtime import finite_confluence_aggregate
from .confluence_aggregate_types import (
    C2_NONCLAIMS, ConfluenceAggregateResourceLimit, ConfluenceRequirementRow,
    FiniteConfluenceAggregate, FiniteConfluenceCatalogSource,
    FiniteConfluenceResult, RequirementKind,
)
from .confluence_types import ConfluenceObstruction, FiniteDiagramSource
from .positive_ontology_types import ObserverDoctrine

logger = logging.getLogger(__name__)


def validate_finite_confluence_result(
    raw_doctrine: ObserverDoctrine, raw_diagram: FiniteDiagramSource,
    raw_catalog: FiniteConfluenceCatalogSource, value: FiniteConfluenceResult,
) -> FiniteConfluenceResult:
    """Freshly derive the expected union variant, then validate supplied shape."""
    logger.debug("validate_finite_confluence_result entry")
    expected = finite_confluence_aggregate(raw_doctrine, raw_diagram, raw_catalog)
    if type(value) is not type(expected):
        _reject("confluence-aggregate-result-variant-drift")
    if type(expected) is ConfluenceAggregateResourceLimit:
        _validate_refusal(value, expected)
    elif type(expected) is FiniteConfluenceAggregate:
        _validate_aggregate(value, expected)
    else:
        _reject("unknown-confluence-aggregate-result-variant")
    logger.debug("validate_finite_confluence_result exit type=%s", type(expected).__name__)
    return expected


def _validate_refusal(raw, expected) -> None:
    logger.debug("validate aggregate refusal entry")
    exact_instance(raw, ConfluenceAggregateResourceLimit, "resource-limit")
    exact_fields(raw, expected, (
        ("status", type(expected.status)), ("doctrine_fingerprint", str),
        ("diagram_digest", str), ("catalog_digest", str), ("policy_digest", str),
        ("run_digest", str), ("failed_bound", type(expected.failed_bound)),
        ("required_value", int), ("allowed_value", int), ("refusal_digest", str),
    ), "confluence-aggregate-refusal-drift")
    _nonclaims(raw.nonclaims)
    logger.debug("validate aggregate refusal exit")


def _validate_aggregate(raw, expected) -> None:
    logger.debug("validate aggregate positive entry")
    exact_instance(raw, FiniteConfluenceAggregate, "positive-result")
    if (
        type(raw.expected_local_keys) is not tuple
        or type(raw.expected_global_keys) is not tuple
        or type(raw.rows) is not tuple or type(raw.nonclaims) is not tuple
    ):
        _reject("confluence-aggregate-outer-container-drift")
    exact_fields(raw, expected, (
        ("doctrine_fingerprint", str), ("diagram_digest", str),
        ("catalog_digest", str), ("policy_digest", str), ("run_digest", str),
        ("local_status", type(expected.local_status)),
        ("global_status", type(expected.global_status)),
        ("coverage", type(expected.coverage)), ("total_charge", int),
        ("aggregate_digest", str),
    ), "confluence-aggregate-outer-drift")
    lengths = (
        len(raw.expected_local_keys), len(raw.expected_global_keys), len(raw.rows),
        len(raw.nonclaims),
    )
    expected_lengths = (
        len(expected.expected_local_keys), len(expected.expected_global_keys),
        len(expected.rows), len(expected.nonclaims),
    )
    if lengths != expected_lengths:
        _reject("confluence-aggregate-outer-length-drift")
    _keys(raw.expected_local_keys, expected.expected_local_keys, RequirementKind.LOCAL)
    _keys(raw.expected_global_keys, expected.expected_global_keys, RequirementKind.GLOBAL)
    _nonclaims(raw.nonclaims)
    _obstruction(raw.first_obstruction, expected.first_obstruction, "aggregate-first")
    for supplied, wanted in zip(raw.rows, expected.rows, strict=True):
        _row(supplied, wanted)
    logger.debug("validate aggregate positive exit rows=%d", len(expected.rows))


def _row(raw, expected) -> None:
    logger.debug("validate aggregate row entry")
    exact_instance(raw, ConfluenceRequirementRow, "requirement-row")
    _key(raw.key, expected.key)
    exact_fields(raw, expected, (
        ("transport_digest", str), ("charged_checks", int),
        ("status", type(expected.status)), ("row_digest", str),
    ), "confluence-aggregate-row-drift")
    for name in (
        "plan_digest", "left_history_digest", "right_history_digest",
        "local_judgment_digest", "global_history_cell_digest",
    ):
        supplied, wanted = getattr(raw, name), getattr(expected, name)
        exact_optional_string(
            supplied, wanted, "confluence-aggregate-row-variant-drift",
        )
    _obstruction(raw.first_obstruction, expected.first_obstruction, "row-first")
    logger.debug("validate aggregate row exit")


def _keys(raw: tuple, expected: tuple, kind: RequirementKind) -> None:
    logger.debug("validate aggregate keys entry kind=%s", kind.value)
    for supplied, wanted in zip(raw, expected, strict=True):
        _key(supplied, wanted)
        if supplied[0] is not kind:
            _reject("confluence-aggregate-key-kind-drift")
    logger.debug("validate aggregate keys exit kind=%s", kind.value)


def _key(raw, expected) -> None:
    logger.debug("validate aggregate key entry")
    if type(raw) is not tuple or len(raw) != 3:
        _reject("confluence-aggregate-key-shape-drift")
    if (
        type(raw[0]) is not RequirementKind or raw[0] is not expected[0]
        or type(raw[1]) is not str or raw[1] != expected[1]
        or type(raw[2]) is not str or raw[2] != expected[2]
    ):
        _reject("confluence-aggregate-key-drift")
    logger.debug("validate aggregate key exit")


def _obstruction(raw, expected, field: str) -> None:
    logger.debug("validate aggregate obstruction entry field=%s", field)
    if expected is None:
        if raw is not None:
            _reject(f"confluence-{field}-obstruction-drift")
    else:
        exact_instance(raw, ConfluenceObstruction, f"{field}-obstruction")
        exact_fields(raw, expected, (
            ("lane", str), ("occurrence", int), ("observer_id", str),
            ("outcome", str),
        ), f"confluence-{field}-obstruction-drift")
    logger.debug("validate aggregate obstruction exit field=%s", field)


def _nonclaims(value) -> None:
    logger.debug("validate aggregate nonclaims entry")
    if (
        type(value) is not tuple or len(value) != len(C2_NONCLAIMS)
        or any(type(item) is not str for item in value) or value != C2_NONCLAIMS
    ):
        _reject("confluence-aggregate-nonclaims-drift")
    logger.debug("validate aggregate nonclaims exit")

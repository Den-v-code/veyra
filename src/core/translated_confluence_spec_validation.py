"""Shallow-first exact spec and policy snapshots for P1-C3."""

from __future__ import annotations

import logging

from .observer_morphism_types import ProjectionStep
from .observer_relation_resource_types import RelationResourcePolicy
from .observer_relation_types import (
    ComparisonMode, LawStatus, LossStatus, MorphismReplaySpec,
    ObserverRelationScope, RelationClass,
)
from .translated_confluence_types import (
    C3TransportMode, TranslatedConfluencePolicy, TranslatedEchoTransportSpec,
    TranslationDirection,
)
from .translated_confluence_validation import hex_digest, reject

logger = logging.getLogger(__name__)


def _get(value: object, names: tuple[str, ...], reason: str) -> tuple[object, ...]:
    """Read exact DTO fields without dynamic property lookup."""
    logger.debug("c3 spec get entry reason=%s", reason)
    try:
        result = tuple(object.__getattribute__(value, name) for name in names)
    except AttributeError:
        reject(reason)
    logger.debug("c3 spec get exit fields=%d", len(result))
    return result


def shallow_outer_policy(value: object) -> tuple[object, ...]:
    """Capture one exact outer policy before reconstruction."""
    logger.debug("c3 shallow_outer_policy entry")
    if type(value) is not TranslatedConfluencePolicy:
        reject("translated-confluence-policy-must-be-exact")
    row = _get(value, TranslatedConfluencePolicy.__slots__, "translated-confluence-policy-missing-fields")
    if (
        type(row[0]) is not str or type(row[1]) is not int
        or type(row[2]) is not int or type(row[3]) is not str
    ):
        reject("translated-confluence-policy-field-type")
    hex_digest(row[3], "translated-confluence-policy-digest")
    logger.debug("c3 shallow_outer_policy exit")
    return row


def _morphism(value: object) -> tuple[object, ...]:
    """Capture exact raw morphism syntax with a closed projection tuple."""
    logger.debug("c3 shallow morphism entry")
    if type(value) is not MorphismReplaySpec:
        reject("translated-transport-requires-raw-morphism")
    row = _get(
        value, ("morphism_id", "fine_observer_id", "coarse_observer_id", "projection"),
        "translated-morphism-missing-fields",
    )
    if any(type(item) is not str for item in row[:3]) or type(row[3]) is not tuple or len(row[3]) > 128:
        reject("translated-morphism-field-type-or-length")
    if any(type(item) is not ProjectionStep for item in row[3]):
        reject("translated-morphism-projection-drift")
    result = (*row[:3], tuple(row[3]))
    logger.debug("c3 shallow morphism exit steps=%d", len(row[3]))
    return result


def _stage_key(value: object, field: str) -> tuple[str, str]:
    """Capture one exact two-string A2 stage key."""
    logger.debug("c3 shallow stage_key entry field=%s", field)
    if type(value) is not tuple or len(value) != 2 or any(type(item) is not str for item in value):
        reject(f"translated-{field}-stage-key-drift")
    result = (value[0], value[1])
    logger.debug("c3 shallow stage_key exit field=%s", field)
    return result


def _scope(value: object) -> tuple[object, ...]:
    """Capture exact A2 scope containers before lower-layer replay."""
    logger.debug("c3 shallow scope entry")
    if type(value) is not ObserverRelationScope:
        reject("translated-relation-scope-must-be-exact")
    names = (
        "doctrine_fingerprint", "observer_source_digest", "stage_source_digest",
        "fine_observer_id", "coarse_observer_id", "stages", "ordered_pairs",
        "mode", "scope_digest",
    )
    row = _get(value, names, "translated-relation-scope-missing-fields")
    if (
        any(type(item) is not str for item in (*row[:5], row[8]))
        or type(row[5]) is not tuple or not 1 <= len(row[5]) <= 32
        or type(row[6]) is not tuple or len(row[6]) != len(row[5]) ** 2
        or type(row[7]) is not ComparisonMode
    ):
        reject("translated-relation-scope-field-type-or-length")
    for item in (*row[:3], row[8]):
        hex_digest(item, "translated-relation-scope-digest")
    stages = tuple(_stage_key(item, "scope") for item in row[5])
    pairs: list[tuple[tuple[str, str], tuple[str, str]]] = []
    for item in row[6]:
        if type(item) is not tuple or len(item) != 2:
            reject("translated-scope-pair-drift")
        pairs.append((_stage_key(item[0], "pair-left"), _stage_key(item[1], "pair-right")))
    result = (*row[:5], stages, tuple(pairs), row[7], row[8])
    logger.debug("c3 shallow scope exit stages=%d pairs=%d", len(stages), len(pairs))
    return result


def _relation_policy(value: object) -> tuple[object, ...]:
    """Capture exact nested A2 policy primitive fields."""
    logger.debug("c3 shallow relation_policy entry")
    if type(value) is not RelationResourcePolicy:
        reject("translated-relation-policy-must-be-exact")
    row = _get(
        value, ("version", "max_cost", "max_encoded_bytes", "policy_digest"),
        "translated-relation-policy-missing-fields",
    )
    if type(row[0]) is not str or type(row[1]) is not int or type(row[2]) is not int or type(row[3]) is not str:
        reject("translated-relation-policy-field-type")
    hex_digest(row[3], "translated-relation-policy-digest")
    logger.debug("c3 shallow relation_policy exit")
    return row


def shallow_spec(value: object) -> tuple[object, ...]:
    """Capture every public spec field before reconstruction or equality."""
    logger.debug("c3 shallow_spec entry")
    if type(value) is not TranslatedEchoTransportSpec:
        reject("translated-transport-spec-must-be-exact")
    row = _get(value, TranslatedEchoTransportSpec.__slots__, "translated-transport-spec-missing-fields")
    if (
        any(type(row[index]) is not str for index in (0, 1, 2, 4, 5, 6, 7, 15, 16, 18))
        or type(row[3]) is not TranslationDirection
        or type(row[11]) is not LawStatus or type(row[12]) is not LawStatus
        or type(row[13]) is not RelationClass
        or (row[14] is not None and type(row[14]) is not LossStatus)
        or type(row[17]) is not C3TransportMode
    ):
        reject("translated-transport-spec-field-type")
    for index in (1, 2, 15):
        hex_digest(row[index], "translated-transport-spec-digest")
    result = (
        *row[:8], _morphism(row[8]), _scope(row[9]), _relation_policy(row[10]),
        *row[11:],
    )
    logger.debug("c3 shallow_spec exit")
    return result

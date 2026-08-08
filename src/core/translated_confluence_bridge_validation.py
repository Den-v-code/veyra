"""Shallow-first hostile-safe supplied bridge validation for P1-C3."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from .observer_relation_validation import snapshot_recurrence
from .translated_confluence_types import (
    ObserverProgramBridgeRow, P0P1AResponseBridgeSource, StageInputBridgeRow,
)
from .translated_confluence_validation import (
    TranslatedConfluenceValidationError, hex_digest, reject,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _BridgeSnapshot:
    outer: tuple[str, ...]
    observers: tuple[tuple[object, ...], ...]
    stages: tuple[tuple[object, ...], ...]
    order: tuple[str, ...]


def _fields(value: object, names: tuple[str, ...], reason: str) -> tuple[object, ...]:
    """Read declared fields without property dispatch on an exact DTO."""
    logger.debug("c3 bridge fields entry reason=%s", reason)
    try:
        result = tuple(object.__getattribute__(value, name) for name in names)
    except AttributeError:
        reject(reason)
    logger.debug("c3 bridge fields exit count=%d", len(result))
    return result


def _observer(value: object) -> tuple[object, ...]:
    """Capture one exact bridge observer row using primitive-only fields."""
    logger.debug("c3 bridge observer shallow entry")
    if type(value) is not ObserverProgramBridgeRow:
        reject("observer-program-bridge-row-must-be-exact")
    names = ObserverProgramBridgeRow.__slots__
    row = _fields(value, names, "observer-program-bridge-row-missing-fields")
    if (
        any(type(item) is not str for item in (row[0], row[1], *row[3:]))
        or type(row[2]) is not bytes
    ):
        reject("observer-program-bridge-row-field-type")
    for index in (3, 4, 5, 6):
        hex_digest(row[index], "observer-program-bridge-row-digest")
    logger.debug("c3 bridge observer shallow exit")
    return row


def _stage(value: object) -> tuple[object, ...]:
    """Capture one exact stage row and safely snapshot its recurrence."""
    logger.debug("c3 bridge stage shallow entry")
    if type(value) is not StageInputBridgeRow:
        reject("stage-input-bridge-row-must-be-exact")
    row = _fields(value, StageInputBridgeRow.__slots__, "stage-input-bridge-row-missing-fields")
    if any(type(row[index]) is not str for index in (0, 1, 3, 4, 5, 6)):
        reject("stage-input-bridge-row-field-type")
    for index in (1, 3, 5, 6):
        hex_digest(row[index], "stage-input-bridge-row-digest")
    try:
        _, canonical = snapshot_recurrence(row[2])
    except (TypeError, ValueError) as exc:
        logger.error("c3 bridge stage recurrence rejected")
        raise TranslatedConfluenceValidationError(
            "invalid-stage-input-bridge-recurrence"
        ) from exc
    result = (row[0], row[1], canonical, *row[3:])
    logger.debug("c3 bridge stage shallow exit")
    return result


def shallow_bridge(value: object) -> _BridgeSnapshot:
    """Reject hollow/subclass/huge/container drift before reconstruction."""
    logger.debug("c3 shallow_bridge entry")
    if type(value) is not P0P1AResponseBridgeSource:
        reject("response-bridge-must-be-exact")
    names = P0P1AResponseBridgeSource.__slots__
    raw = _fields(value, names, "response-bridge-missing-fields")
    observers, stages, order = raw[5], raw[6], raw[7]
    if (
        type(observers) is not tuple or not 1 <= len(observers) <= 64
        or type(stages) is not tuple or not 1 <= len(stages) <= 32
        or type(order) is not tuple or not 1 <= len(order) <= 32
    ):
        reject("response-bridge-container-or-length")
    outer = (*raw[:5], raw[8], raw[9], raw[10])
    if any(type(item) is not str for item in outer):
        reject("response-bridge-field-type")
    for item in (*outer[:5], outer[5]):
        hex_digest(item, "response-bridge-digest")
    if any(type(item) is not str for item in order):
        reject("response-bridge-order-field-type")
    for item in order:
        hex_digest(item, "response-bridge-order-digest")
    result = _BridgeSnapshot(
        outer, tuple(_observer(item) for item in observers),
        tuple(_stage(item) for item in stages), tuple(order),
    )
    logger.debug("c3 shallow_bridge exit observers=%d stages=%d", len(observers), len(stages))
    return result


def compare_bridge(snapshot: _BridgeSnapshot, expected: P0P1AResponseBridgeSource) -> None:
    """Compare only captured primitive/canonical values to a fresh bridge."""
    logger.debug("c3 compare_bridge entry")
    expected_outer = (
        expected.p0_doctrine_fingerprint, expected.diagram_digest,
        expected.p1a_doctrine_fingerprint, expected.p1a_observer_source_digest,
        expected.a2_stage_source_digest, expected.bridge_digest,
        expected.version, expected.scope,
    )
    if snapshot.outer != expected_outer or snapshot.order != expected.a2_ordered_commitments:
        reject("response-bridge-drift")
    if len(snapshot.observers) != len(expected.observer_rows) or len(snapshot.stages) != len(expected.stage_rows):
        reject("response-bridge-drift")
    for supplied, wanted in zip(snapshot.observers, expected.observer_rows, strict=True):
        expected_row = tuple(object.__getattribute__(wanted, name) for name in wanted.__slots__)
        if supplied != expected_row:
            reject("observer-program-bridge-row-drift")
    for supplied, wanted in zip(snapshot.stages, expected.stage_rows, strict=True):
        expected_row = (
            wanted.diagram_stage_id, wanted.diagram_stage_commitment,
            snapshot_recurrence(wanted.recurrence)[1], wanted.recurrence_digest,
            wanted.relation_stage_id, wanted.relation_stage_commitment, wanted.row_digest,
        )
        if supplied != expected_row:
            reject("stage-input-bridge-row-drift")
    logger.debug("c3 compare_bridge exit")

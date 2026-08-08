"""Canonical R12.1 branding for exact R11 Ready/Blocked observations."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from typing import NoReturn

from .observer_core_codec import canonical_observer_bytes
from .observer_core_semantics import MAX_OBSERVER_DEPTH, MAX_OBSERVER_NODES, infer_observer_kind
from .observer_core_support import outcome_data
from .observer_core_types import (
    Apply,
    Blocked,
    LeafKind,
    MarkValue,
    Pair,
    PairKind,
    PairValue,
    PathStep,
    PrimitiveId,
    Ready,
    RecurrenceValue,
)
from .shadow_effect_types import BrandedObservation, CarrierId, ObservationBrand

logger = logging.getLogger(__name__)
BRAND_SCHEMA = "veyra.observed-response.r12.1"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class ShadowEffectError(ValueError):
    """A deterministic R12.1 validation rejection."""


def reject(reason: str) -> NoReturn:
    """Log and raise one stable R12.1 rejection."""
    logger.error("shadow effect rejected reason=%s", reason)
    raise ShadowEffectError(reason)


def digest_bytes(payload: bytes) -> str:
    """Return one canonical SHA-256 hex digest."""
    logger.debug("digest_bytes entry bytes=%d", len(payload))
    result = hashlib.sha256(payload).hexdigest()
    logger.debug("digest_bytes exit digest=%s", result)
    return result


def canonical_data_bytes(data: object) -> bytes:
    """Encode JSON-compatible data with one deterministic representation."""
    logger.debug("canonical_data_bytes entry type=%s", type(data).__name__)
    try:
        result = json.dumps(data, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    except (TypeError, ValueError, RecursionError) as exc:
        reject(f"noncanonical-data:{type(exc).__name__}")
    logger.debug("canonical_data_bytes exit bytes=%d", len(result))
    return result


def response_kind_data(kind: object) -> dict[str, object]:
    """Serialize one exact R11 response kind without extension hooks."""
    logger.debug("response_kind_data entry type=%s", type(kind).__name__)
    stack: list[tuple[bool, object, int]] = [(False, kind, 0)]
    active: set[int] = set()
    values: list[dict[str, object]] = []
    nodes = 0
    while stack:
        exiting, node, depth = stack.pop()
        identity = id(node)
        if exiting:
            active.remove(identity)
            if type(node) is LeafKind:
                values.append({"tag": node.value})
            else:
                right, left = values.pop(), values.pop()
                values.append({"tag": "pair", "left": left, "right": right})
            continue
        nodes += 1
        if nodes > MAX_OBSERVER_NODES or depth > MAX_OBSERVER_DEPTH:
            reject("response-kind-resource-limit")
        if identity in active:
            reject("circular-response-kind")
        if type(node) not in {LeafKind, PairKind}:
            reject("invalid-response-kind")
        active.add(identity)
        stack.append((True, node, depth))
        if type(node) is PairKind:
            stack.append((False, node.right, depth + 1))
            stack.append((False, node.left, depth + 1))
    if len(values) != 1:
        reject("invalid-response-kind-shape")
    logger.debug("response_kind_data exit nodes=%d", nodes)
    return values[0]


def _response_matches_kind(kind: object, value: object) -> bool:
    """Match an exact response value to the observer's inferred kind."""
    logger.debug("_response_matches_kind entry")
    stack = [(kind, value)]
    nodes = 0
    while stack:
        expected, actual = stack.pop()
        nodes += 1
        if nodes > MAX_OBSERVER_NODES:
            reject("response-kind-resource-limit")
        if expected is LeafKind.RECURRENCE:
            if type(actual) is not RecurrenceValue:
                logger.debug("_response_matches_kind exit result=False")
                return False
        elif expected is LeafKind.MARK:
            if type(actual) is not MarkValue:
                logger.debug("_response_matches_kind exit result=False")
                return False
        elif type(expected) is PairKind and type(actual) is PairValue:
            stack.append((expected.right, actual.right))
            stack.append((expected.left, actual.left))
        else:
            logger.debug("_response_matches_kind exit result=False")
            return False
    logger.debug("_response_matches_kind exit result=True nodes=%d", nodes)
    return True


def _observer_obstruction_paths(observer: object) -> frozenset[tuple[PathStep, ...]]:
    """Enumerate exact paths at which this closed observer may block."""
    logger.debug("_observer_obstruction_paths entry")
    stack = [(observer, ())]
    paths: set[tuple[PathStep, ...]] = set()
    nodes = 0
    while stack:
        node, path = stack.pop()
        nodes += 1
        if nodes > MAX_OBSERVER_NODES:
            reject("observer-path-resource-limit")
        if type(node) is Apply:
            step = PathStep.APPLY_TAIL if node.primitive is PrimitiveId.TAIL else PathStep.APPLY_CREST
            child_path = path + (step,)
            if node.primitive is PrimitiveId.TAIL:
                paths.add(child_path)
            stack.append((node.child, child_path))
        elif type(node) is Pair:
            stack.append((node.right, path + (PathStep.PAIR_RIGHT,)))
            stack.append((node.left, path + (PathStep.PAIR_LEFT,)))
    logger.debug("_observer_obstruction_paths exit paths=%d nodes=%d", len(paths), nodes)
    return frozenset(paths)


def _validate_observation_for_observer(observer: object, observation: object) -> object:
    """Require the payload shape and obstruction paths to address this observer."""
    logger.debug("_validate_observation_for_observer entry")
    kind = infer_observer_kind(observer)
    payload = outcome_data(observation)
    if type(observation) is Ready and not _response_matches_kind(kind, observation.value):
        reject("observation-kind-mismatch")
    if type(observation) is Blocked:
        allowed = _observer_obstruction_paths(observer)
        if any(item.path not in allowed for item in observation.obstructions):
            reject("observation-obstruction-mismatch")
    logger.debug("_validate_observation_for_observer exit tag=%s", payload["tag"])
    return kind


def _binding_digest(
    source: CarrierId,
    observer_digest: str,
    response_kind_digest: str,
    payload_digest: str,
) -> str:
    """Bind every provenance component into one mutation-evident digest."""
    logger.debug("_binding_digest entry source=%s", source.value)
    result = digest_bytes(
        canonical_data_bytes(
            {
                "schema": BRAND_SCHEMA,
                "source": source.value,
                "observer_digest": observer_digest,
                "response_kind_digest": response_kind_digest,
                "payload_digest": payload_digest,
            }
        )
    )
    logger.debug("_binding_digest exit digest=%s", result)
    return result


def brand_observation(observer: object, observation: object, source: CarrierId) -> BrandedObservation:
    """Bind one exact R11 Ready/Blocked observation to its observer and source."""
    logger.debug("brand_observation entry observer=%s observation=%s", type(observer).__name__, type(observation).__name__)
    if type(source) is not CarrierId or source not in {CarrierId.R7_RECURRENCE, CarrierId.R9_INTRINSIC_MODE}:
        reject("invalid-observation-source")
    if type(observation) not in {Ready, Blocked}:
        reject("invalid-observation")
    kind = _validate_observation_for_observer(observer, observation)
    observer_bytes = canonical_observer_bytes(observer)
    kind_bytes = canonical_data_bytes(response_kind_data(kind))
    payload_bytes = canonical_data_bytes(outcome_data(observation))
    observer_digest = digest_bytes(observer_bytes)
    kind_digest = digest_bytes(kind_bytes)
    payload_digest = digest_bytes(payload_bytes)
    result = BrandedObservation(
        ObservationBrand(
            BRAND_SCHEMA,
            source,
            observer_digest,
            kind_digest,
            _binding_digest(source, observer_digest, kind_digest, payload_digest),
        ),
        observation,
        payload_digest,
    )
    logger.debug("brand_observation exit payload=%s", result.payload_digest)
    return result


def branded_observation_data(value: object) -> dict[str, object]:
    """Return canonical data after strict brand and payload validation."""
    logger.debug("branded_observation_data entry type=%s", type(value).__name__)
    if type(value) is not BrandedObservation or type(value.brand) is not ObservationBrand:
        reject("invalid-branded-observation")
    brand = value.brand
    if (
        brand.schema != BRAND_SCHEMA
        or type(brand.source) is not CarrierId
        or brand.source not in {CarrierId.R7_RECURRENCE, CarrierId.R9_INTRINSIC_MODE}
        or type(brand.observer_digest) is not str
        or type(brand.response_kind_digest) is not str
        or not _HEX64.fullmatch(brand.observer_digest)
        or not _HEX64.fullmatch(brand.response_kind_digest)
        or type(brand.binding_digest) is not str
        or not _HEX64.fullmatch(brand.binding_digest)
        or type(value.payload_digest) is not str
        or not _HEX64.fullmatch(value.payload_digest)
    ):
        reject("invalid-observation-brand")
    payload = outcome_data(value.observation)
    if digest_bytes(canonical_data_bytes(payload)) != value.payload_digest:
        reject("observation-payload-drift")
    if _binding_digest(
        brand.source,
        brand.observer_digest,
        brand.response_kind_digest,
        value.payload_digest,
    ) != brand.binding_digest:
        reject("observation-brand-drift")
    result = {
        "schema": brand.schema,
        "source": brand.source.value,
        "observer_digest": brand.observer_digest,
        "response_kind_digest": brand.response_kind_digest,
        "binding_digest": brand.binding_digest,
        "payload": payload,
        "payload_digest": value.payload_digest,
    }
    logger.debug("branded_observation_data exit")
    return result


def verify_branded_observation(observer: object, value: object, source: CarrierId) -> bool:
    """Reject transplantation to another observer, kind, payload, or carrier."""
    logger.debug("verify_branded_observation entry observer=%s source=%r", type(observer).__name__, source)
    if type(source) is not CarrierId or source not in {CarrierId.R7_RECURRENCE, CarrierId.R9_INTRINSIC_MODE}:
        reject("invalid-observation-source")
    data = branded_observation_data(value)
    if data["source"] != source.value:
        reject("observation-source-transplant")
    observer_digest = digest_bytes(canonical_observer_bytes(observer))
    kind_digest = digest_bytes(canonical_data_bytes(response_kind_data(infer_observer_kind(observer))))
    if data["observer_digest"] != observer_digest or data["response_kind_digest"] != kind_digest:
        reject("observation-brand-transplant")
    _validate_observation_for_observer(observer, value.observation)
    logger.debug("verify_branded_observation exit result=True")
    return True

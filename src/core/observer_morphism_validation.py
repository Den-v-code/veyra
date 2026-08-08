"""Fail-closed snapshots and digests for P1-A observer morphisms."""

from __future__ import annotations

from hashlib import sha256
import logging
from typing import NoReturn

from .observer_core_types import LeafKind, PairKind, ResponseKind
from .positive_ontology_doctrine import snapshot_observer_doctrine
from .positive_ontology_types import ObserverDoctrine
from .positive_ontology_validation import PositiveOntologyValidationError
from .observer_morphism_types import (
    ObserverSourceBinding,
    ProjectionStep,
    ResponseTranslation,
)
from .observer_morphism_structure import _projection_factorizes

logger = logging.getLogger(__name__)
MAX_P1A_ID_BYTES = 128
MAX_P1A_PROJECTION = 128


class ObserverMorphismValidationError(ValueError):
    """An exact P1-A representation or binding contract was violated."""

def snapshot_morphism_doctrine(value: ObserverDoctrine) -> ObserverDoctrine:
    """Normalize lower-layer doctrine failures into the P1-A boundary."""
    logger.debug("snapshot_morphism_doctrine entry")
    try:
        result = snapshot_observer_doctrine(value)
    except PositiveOntologyValidationError as exc:
        logger.error("snapshot_morphism_doctrine rejected")
        raise ObserverMorphismValidationError("invalid-morphism-doctrine") from exc
    logger.debug("snapshot_morphism_doctrine exit")
    return result


def _reject(reason: str) -> NoReturn:
    logger.error("observer morphism rejected reason=%s", reason)
    raise ObserverMorphismValidationError(reason)


def snapshot_p1a_identifier(value: str, field: str) -> str:
    """Capture a bounded exact identifier without hostile formatting."""
    logger.debug("snapshot_p1a_identifier entry field=%s", field)
    if type(value) is not str or not value or len(value) > MAX_P1A_ID_BYTES:
        _reject(f"invalid-{field}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        _reject(f"invalid-{field}")
    if size > MAX_P1A_ID_BYTES:
        _reject(f"invalid-{field}")
    logger.debug("snapshot_p1a_identifier exit field=%s bytes=%d", field, size)
    return value


def snapshot_projection(value: tuple[ProjectionStep, ...]) -> tuple[ProjectionStep, ...]:
    """Capture one exact bounded projection, including empty identity."""
    logger.debug("snapshot_projection entry")
    if type(value) is not tuple or len(value) > MAX_P1A_PROJECTION:
        _reject("invalid-projection")
    if any(type(item) is not ProjectionStep for item in value):
        _reject("invalid-projection-step")
    result = tuple(value)
    logger.debug("snapshot_projection exit steps=%d", len(result))
    return result


def response_kind_signature(value: ResponseKind) -> tuple[str, ...]:
    """Encode an exact bounded response kind without tuple-sentinel collision."""
    logger.debug("response_kind_signature entry")
    stack: list[tuple[bool, object]] = [(False, value)]
    active: set[int] = set()
    output: list[str] = []
    nodes = 0
    while stack:
        closing, node = stack.pop()
        if closing:
            active.discard(id(node))
            output.append("pair-close")
            continue
        nodes += 1
        if nodes > 256:
            _reject("response-kind-resource-limit")
        if type(node) is LeafKind:
            output.append(node.value)
            continue
        if type(node) is not PairKind or id(node) in active:
            _reject("invalid-response-kind")
        try:
            left, right = node.left, node.right
        except AttributeError:
            _reject("response-kind-missing-fields")
        active.add(id(node))
        output.append("pair-open")
        stack.extend(((True, node), (False, right), (False, left)))
    result = tuple(output)
    logger.debug("response_kind_signature exit nodes=%d", nodes)
    return result


def membership_digest(
    binding_id: str,
    doctrine_fingerprint: str,
    observer_ids: tuple[str, ...],
    observer_digests: tuple[str, ...],
) -> str:
    """Digest exact source membership with length-prefixed fields."""
    logger.debug("membership_digest entry")
    binding_id = snapshot_p1a_identifier(binding_id, "binding-id")
    if (
        type(doctrine_fingerprint) is not str
        or len(doctrine_fingerprint) != 64
        or any(ch not in "0123456789abcdef" for ch in doctrine_fingerprint)
        or type(observer_ids) is not tuple
        or type(observer_digests) is not tuple
        or len(observer_ids) != len(observer_digests)
    ):
        _reject("invalid-membership-digest-input")
    captured_ids = tuple(
        snapshot_p1a_identifier(item, "observer-id") for item in observer_ids
    )
    captured_digests: list[str] = []
    for item in observer_digests:
        if (
            type(item) is not str
            or len(item) != 64
            or any(ch not in "0123456789abcdef" for ch in item)
        ):
            _reject("invalid-membership-digest-input")
        captured_digests.append(item)
    digest = sha256()
    for token in (binding_id, doctrine_fingerprint, *captured_ids, *captured_digests):
        _digest_token(digest, token.encode("utf-8"))
    result = digest.hexdigest()
    logger.debug("membership_digest exit")
    return result


def translation_digest(
    translation_id: str,
    doctrine_fingerprint: str,
    binding_digest: str,
    fine_id: str,
    coarse_id: str,
    projection: tuple[ProjectionStep, ...],
    fine_kind: ResponseKind,
    coarse_kind: ResponseKind,
) -> str:
    """Digest one exact structural translation with kind signatures."""
    logger.debug("translation_digest entry")
    translation_id = snapshot_p1a_identifier(translation_id, "translation-id")
    fine_id = snapshot_p1a_identifier(fine_id, "fine-observer-id")
    coarse_id = snapshot_p1a_identifier(coarse_id, "coarse-observer-id")
    projection = snapshot_projection(projection)
    if (
        type(doctrine_fingerprint) is not str
        or len(doctrine_fingerprint) != 64
        or any(ch not in "0123456789abcdef" for ch in doctrine_fingerprint)
        or type(binding_digest) is not str
        or len(binding_digest) != 64
        or any(ch not in "0123456789abcdef" for ch in binding_digest)
    ):
        _reject("invalid-translation-digest-input")
    digest = sha256()
    tokens = (
        translation_id, doctrine_fingerprint, binding_digest, fine_id, coarse_id,
        *(item.value for item in projection),
        *response_kind_signature(fine_kind), *response_kind_signature(coarse_kind),
    )
    for token in tokens:
        _digest_token(digest, token.encode("utf-8"))
    result = digest.hexdigest()
    logger.debug("translation_digest exit")
    return result


def snapshot_source_binding(
    value: ObserverSourceBinding, doctrine: ObserverDoctrine
) -> ObserverSourceBinding:
    """Validate immutable membership against one exact doctrine snapshot."""
    logger.debug("snapshot_source_binding entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    if type(value) is not ObserverSourceBinding:
        _reject("source-binding-must-be-exact")
    try:
        binding_id, doctrine_fp = value.binding_id, value.doctrine_fingerprint
        ids, digests = value.observer_ids, value.observer_digests
        supplied, scope = value.membership_digest, value.scope
    except AttributeError:
        _reject("source-binding-missing-fields")
    binding_id = snapshot_p1a_identifier(binding_id, "binding-id")
    if (
        type(doctrine_fp) is not str
        or type(scope) is not str
        or type(supplied) is not str
    ):
        _reject("source-binding-string-fields-required")
    if doctrine_fp != doctrine.fingerprint or scope != "immutability-membership-not-chronology":
        _reject("source-binding-doctrine-or-scope-drift")
    if type(ids) is not tuple or type(digests) is not tuple or not ids or len(ids) != len(digests):
        _reject("invalid-source-binding-members")
    if len(ids) > len(doctrine.observers):
        _reject("source-binding-member-limit")
    captured_ids = tuple(snapshot_p1a_identifier(item, "observer-id") for item in ids)
    if len(set(captured_ids)) != len(captured_ids):
        _reject("duplicate-source-binding-member")
    members = {item.observer_id: item for item in doctrine.observers}
    captured_digests: list[str] = []
    for item in digests:
        if type(item) is not str or len(item) != 64 or any(ch not in "0123456789abcdef" for ch in item):
            _reject("invalid-source-binding-observer-digest")
        captured_digests.append(item)
    expected_digests: list[str] = []
    for observer_id in captured_ids:
        if observer_id not in members:
            _reject("source-binding-nonmember")
        expected_digests.append(sha256(members[observer_id].canonical).hexdigest())
    expected_tuple = tuple(expected_digests)
    if tuple(captured_digests) != expected_tuple:
        _reject("source-binding-observer-drift")
    expected = membership_digest(binding_id, doctrine.fingerprint, captured_ids, expected_tuple)
    if type(supplied) is not str or supplied != expected:
        _reject("source-binding-digest-drift")
    result = ObserverSourceBinding(
        binding_id, doctrine.fingerprint, captured_ids, expected_tuple, expected
    )
    logger.debug("snapshot_source_binding exit members=%d", len(captured_ids))
    return result


def snapshot_translation(
    value: ResponseTranslation,
    doctrine: ObserverDoctrine,
    binding: ObserverSourceBinding,
) -> ResponseTranslation:
    """Validate one exact translation against source membership and kinds."""
    logger.debug("snapshot_translation entry")
    doctrine = snapshot_morphism_doctrine(doctrine)
    binding = snapshot_source_binding(binding, doctrine)
    if type(value) is not ResponseTranslation:
        _reject("translation-must-be-exact")
    try:
        translation_id, doctrine_fp = value.translation_id, value.doctrine_fingerprint
        binding_digest = value.source_binding_digest
        fine_id, coarse_id = value.fine_observer_id, value.coarse_observer_id
        projection, fine_kind, coarse_kind = value.projection, value.fine_kind, value.coarse_kind
        supplied, scope = value.translation_digest, value.scope
    except AttributeError:
        _reject("translation-missing-fields")
    translation_id = snapshot_p1a_identifier(translation_id, "translation-id")
    fine_id = snapshot_p1a_identifier(fine_id, "fine-observer-id")
    coarse_id = snapshot_p1a_identifier(coarse_id, "coarse-observer-id")
    projection = snapshot_projection(projection)
    if (
        type(doctrine_fp) is not str
        or type(binding_digest) is not str
        or type(supplied) is not str
        or type(scope) is not str
    ):
        _reject("translation-string-fields-required")
    members = {item.observer_id: item for item in doctrine.observers}
    if fine_id not in binding.observer_ids or coarse_id not in binding.observer_ids:
        _reject("translation-source-unbound")
    if fine_id not in members or coarse_id not in members:
        _reject("translation-observer-nonmember")
    if not _projection_factorizes(doctrine, fine_id, coarse_id, projection):
        _reject("translation-projection-does-not-factorize")
    expected_fine, expected_coarse = members[fine_id].response_kind, members[coarse_id].response_kind
    if (
        doctrine_fp != doctrine.fingerprint
        or binding_digest != binding.membership_digest
        or response_kind_signature(fine_kind) != response_kind_signature(expected_fine)
        or response_kind_signature(coarse_kind) != response_kind_signature(expected_coarse)
        or scope != "closed-r11-pair-projection"
    ):
        _reject("translation-binding-or-kind-drift")
    expected = translation_digest(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, projection, expected_fine, expected_coarse,
    )
    if type(supplied) is not str or supplied != expected:
        _reject("translation-digest-drift")
    result = ResponseTranslation(
        translation_id, doctrine.fingerprint, binding.membership_digest,
        fine_id, coarse_id, projection, expected_fine, expected_coarse, expected,
    )
    logger.debug("snapshot_translation exit steps=%d", len(projection))
    return result


def _digest_token(digest: object, token: bytes) -> None:
    logger.debug("_digest_token entry bytes=%d", len(token))
    digest.update(len(token).to_bytes(4, "big"))  # type: ignore[attr-defined]
    digest.update(token)  # type: ignore[attr-defined]
    logger.debug("_digest_token exit")

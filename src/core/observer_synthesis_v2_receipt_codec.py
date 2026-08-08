"""Canonical codec and exact structural gates for finite R14.5 receipts."""
from __future__ import annotations

import logging
import re
from typing import NoReturn, cast

from .intrinsic_vam_lowering_types import TransportedIntrinsicIR
from .intrinsic_vam_receipts import (
    digest_transport_data,
    intrinsic_transport_envelope_data,
)
from .observer_synthesis_v2_protocol import ExpectedRelation, SplitId
from .observer_synthesis_v2_receipt_types import (
    ObserverSynthesisReceiptBundleV2,
    ObserverSynthesisReceiptRowV2,
)
from .proof_core_codec import canonical_json, digest_data
from .shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope

logger = logging.getLogger(__name__)
RECEIPT_SCHEMA = "veyra.observer-synthesis-v2.receipts.r14.5.v1"
ROW_SCHEMA = f"{RECEIPT_SCHEMA}.row"
BOUNDARY = (
    "ten exact default-corpus Crest(Input) R11 echoes lowered through the "
    "finite R12.3 preservation lane; no evidence acceptance, proof, promotion, "
    "taxonomy change, novelty, superiority, or general synthesis claim"
)
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")


class InvalidObserverSynthesisReceiptV2(ValueError):
    """Stable malformed, drifted, or transplanted R14.5 receipt rejection."""


def reject_receipt_v2(reason: str) -> NoReturn:
    """Log and raise one stable finite-receipt rejection."""
    logger.error("observer synthesis v2 receipt rejected reason=%s", reason)
    raise InvalidObserverSynthesisReceiptV2(reason)


def _is_digest(value: object) -> bool:
    """Accept only exact lowercase SHA-256 strings."""
    logger.debug("_is_digest entry type=%s", type(value).__name__)
    result = type(value) is str and _HEX64.fullmatch(value) is not None
    logger.debug("_is_digest exit result=%s", result)
    return result


def _row_body_data_v2(row: object) -> dict[str, object]:
    """Validate and serialize every row field except its self digest."""
    logger.debug("_row_body_data_v2 entry type=%s", type(row).__name__)
    if type(row) is not ObserverSynthesisReceiptRowV2:
        reject_receipt_v2("invalid-receipt-row-type")
    scalar_digests = (
        row.case_digest,
        row.case_payload_digest,
        row.clone_digest,
        row.outcome_digest,
        row.observer_digest,
        row.response_kind_digest,
        row.r12_payload_digest,
        row.ir_digest,
        row.r12_binding_digest,
        row.envelope_digest,
    )
    if (
        type(row.ordinal) is not int
        or not 0 <= row.ordinal < 10
        or type(row.case_id) is not int
        or type(row.group_id) is not int
        or type(row.split) is not SplitId
        or type(row.expected) is not ExpectedRelation
        or type(row.required_for_winner) is not bool
        or type(row.actual) is not ExpectedRelation
        or type(row.matched) is not bool
        or row.matched is not (row.actual is row.expected)
        or type(row.source_digests) is not tuple
        or len(row.source_digests) != 2
        or any(not _is_digest(item) for item in row.source_digests)
        or any(not _is_digest(item) for item in scalar_digests)
        or type(row.transport) is not TransportedIntrinsicIR
        or type(row.row_digest) is not str
    ):
        reject_receipt_v2("invalid-receipt-row-fields")
    envelope = intrinsic_transport_envelope_data(row.transport)
    receipt = envelope["receipt"]
    if (
        receipt["lane"] != "r11-echo-outcome"
        or receipt["provenance"] != "r7-recurrence"
        or receipt["source_digests"] != list(row.source_digests)
        or receipt["observer_digest"] != row.observer_digest
        or receipt["response_kind_digest"] != row.response_kind_digest
        or receipt["payload_digest"] != row.r12_payload_digest
        or receipt["ir_digest"] != row.ir_digest
        or receipt["binding_digest"] != row.r12_binding_digest
        or digest_transport_data(envelope) != row.envelope_digest
        or envelope["verification"] != "unverified-envelope"
        or envelope["evidence_accepted"] is not False
        or envelope["taxonomy_changed"] is not False
        or receipt["promotion_ready"] is not False
        or receipt["evidence"]["may_enter_promotion_contract"] is not False
    ):
        reject_receipt_v2("invalid-receipt-r12-binding")
    result: dict[str, object] = {
        "actual": row.actual.value,
        "case_digest": row.case_digest,
        "case_id": row.case_id,
        "case_payload_digest": row.case_payload_digest,
        "clone_digest": row.clone_digest,
        "envelope_digest": row.envelope_digest,
        "expected": row.expected.value,
        "group_id": row.group_id,
        "ir_digest": row.ir_digest,
        "matched": row.matched,
        "observer_digest": row.observer_digest,
        "ordinal": row.ordinal,
        "outcome_digest": row.outcome_digest,
        "r12_binding_digest": row.r12_binding_digest,
        "r12_envelope": envelope,
        "r12_payload_digest": row.r12_payload_digest,
        "required_for_winner": row.required_for_winner,
        "response_kind_digest": row.response_kind_digest,
        "schema": ROW_SCHEMA,
        "source_digests": list(row.source_digests),
        "split": row.split.value,
    }
    logger.debug("_row_body_data_v2 exit case_id=%d", row.case_id)
    return result


def receipt_row_data_v2(row: object) -> dict[str, object]:
    """Serialize one final row only after replaying its complete R12 envelope."""
    logger.debug("receipt_row_data_v2 entry")
    if type(row) is not ObserverSynthesisReceiptRowV2:
        reject_receipt_v2("invalid-receipt-row-type")
    valid = cast(ObserverSynthesisReceiptRowV2, row)
    body = _row_body_data_v2(valid)
    if not _is_digest(valid.row_digest):
        reject_receipt_v2("invalid-receipt-row-digest")
    if digest_data(body, f"{ROW_SCHEMA}.binding") != valid.row_digest:
        reject_receipt_v2("receipt-row-digest-drift")
    result = {**body, "row_digest": valid.row_digest}
    logger.debug("receipt_row_data_v2 exit")
    return result


def _bundle_body_data_v2(bundle: object) -> dict[str, object]:
    """Validate and serialize every bundle field except its self digest."""
    logger.debug("_bundle_body_data_v2 entry type=%s", type(bundle).__name__)
    if type(bundle) is not ObserverSynthesisReceiptBundleV2:
        reject_receipt_v2("invalid-receipt-bundle-type")
    global_digests = (
        bundle.catalog_digest,
        bundle.winner_digest,
        bundle.corpus_digest,
        bundle.trial_report_digest,
        bundle.manifest_digest,
        bundle.guarantee_digest,
        bundle.winner_retained_digest,
    )
    false_flags = (
        bundle.general_completeness,
        bundle.general_minimality,
        bundle.novelty,
        bundle.superiority,
        bundle.evidence_accepted,
        bundle.promotion_ready,
        bundle.taxonomy_changed,
        bundle.proof_complete,
    )
    if (
        type(bundle.schema) is not str
        or bundle.schema != RECEIPT_SCHEMA
        or any(not _is_digest(item) for item in global_digests)
        or type(bundle.winner_ordinal) is not int
        or type(bundle.winner_cost) is not int
        or type(bundle.winner_depth) is not int
        or type(bundle.winner_canonical) is not bytes
        or type(bundle.capabilities) is not tuple
        or len(bundle.capabilities) != 1
        or bundle.capabilities[0] is not BridgeCapability.PRESERVES
        or bundle.evidence_class is not EvidenceClass.EXECUTABLE_WITNESS
        or bundle.evidence_scope is not EvidenceScope.FINITE
        or type(bundle.taxonomy_counts) is not tuple
        or len(bundle.taxonomy_counts) != 4
        or any(type(item) is not int for item in bundle.taxonomy_counts)
        or bundle.taxonomy_counts != (2, 4, 25, 5)
        or type(bundle.rows) is not tuple
        or len(bundle.rows) != 10
        or any(type(flag) is not bool or flag is not False for flag in false_flags)
        or type(bundle.boundary) is not str
        or bundle.boundary != BOUNDARY
        or type(bundle.bundle_digest) is not str
    ):
        reject_receipt_v2("invalid-receipt-bundle-fields")
    result: dict[str, object] = {
        "boundary": BOUNDARY,
        "capabilities": ["preserves"],
        "catalog_digest": bundle.catalog_digest,
        "corpus_digest": bundle.corpus_digest,
        "evidence": {
            "accepted": False,
            "class": "executable-witness",
            "may_enter_promotion_contract": False,
            "scope": "finite",
        },
        "false_claims": {
            "general_completeness": False,
            "general_minimality": False,
            "novelty": False,
            "proof_complete": False,
            "promotion_ready": False,
            "superiority": False,
            "taxonomy_changed": False,
        },
        "guarantee_digest": bundle.guarantee_digest,
        "manifest_digest": bundle.manifest_digest,
        "rows": [receipt_row_data_v2(row) for row in bundle.rows],
        "schema": RECEIPT_SCHEMA,
        "taxonomy_counts": list(bundle.taxonomy_counts),
        "trial_report_digest": bundle.trial_report_digest,
        "winner": {
            "canonical": bundle.winner_canonical.decode("ascii"),
            "cost": bundle.winner_cost,
            "depth": bundle.winner_depth,
            "digest": bundle.winner_digest,
            "ordinal": bundle.winner_ordinal,
            "retained_digest": bundle.winner_retained_digest,
        },
    }
    logger.debug("_bundle_body_data_v2 exit rows=%d", len(bundle.rows))
    return result


def receipt_bundle_data_v2(bundle: object) -> dict[str, object]:
    """Serialize a final self-bound ten-row finite receipt bundle."""
    logger.debug("receipt_bundle_data_v2 entry")
    if type(bundle) is not ObserverSynthesisReceiptBundleV2:
        reject_receipt_v2("invalid-receipt-bundle-type")
    valid = cast(ObserverSynthesisReceiptBundleV2, bundle)
    body = _bundle_body_data_v2(valid)
    if not _is_digest(valid.bundle_digest):
        reject_receipt_v2("invalid-receipt-bundle-digest")
    if digest_data(body, f"{RECEIPT_SCHEMA}.binding") != valid.bundle_digest:
        reject_receipt_v2("receipt-bundle-digest-drift")
    result = {**body, "bundle_digest": valid.bundle_digest}
    logger.debug("receipt_bundle_data_v2 exit")
    return result


def receipt_bundle_bytes_v2(bundle: object) -> bytes:
    """Return exact canonical bytes only for a fully validated bundle."""
    logger.debug("receipt_bundle_bytes_v2 entry")
    result = canonical_json(receipt_bundle_data_v2(bundle)).encode("utf-8")
    logger.debug("receipt_bundle_bytes_v2 exit bytes=%d", len(result))
    return result

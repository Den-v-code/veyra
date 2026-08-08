"""Fixed finite-evidence receipts for R12.3 intrinsic VAM transport."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import NoReturn

from vam.src.intrinsic_ir import INTRINSIC_IR_SCHEMA, intrinsic_ir_data

from .intrinsic_vam_lowering_types import (
    IntrinsicLoweringLane,
    IntrinsicLoweringReceipt,
    TransportedIntrinsicIR,
)
from .intrinsic_vam_values import IntrinsicVamLoweringError
from .shadow_effect_branding import canonical_data_bytes, digest_bytes
from .shadow_effect_types import BridgeCapability, CarrierId, EvidenceClass, EvidenceScope

logger = logging.getLogger(__name__)
LOWERING_SCHEMA = "veyra.intrinsic-vam.transport.r12.3.v1"
_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_CAPABILITIES = (BridgeCapability.PRESERVES,)


@dataclass(frozen=True, slots=True)
class _LaneRow:
    """One immutable audited structural row."""

    source: CarrierId
    evidence_id: str
    boundary: str
    digest_count: int
    observed: bool


_ROWS = MappingProxyType(
    {
        IntrinsicLoweringLane.R7_RECURRENCE: _LaneRow(
            CarrierId.R7_RECURRENCE,
            "r12.3-r7-recurrence-executable",
            "bounded exact R7 recurrence preservation; executable finite witness only",
            1,
            False,
        ),
        IntrinsicLoweringLane.R9_INTRINSIC_MODE: _LaneRow(
            CarrierId.R9_INTRINSIC_MODE,
            "r12.3-r9-intrinsic-mode-executable",
            "bounded verified R9 intrinsic-image preservation; executable finite witness only",
            1,
            False,
        ),
        IntrinsicLoweringLane.R11_BRANDED_OBSERVATION: _LaneRow(
            CarrierId.R11_RESPONSE,
            "r12.3-r11-observation-replay",
            "bounded R11 observation replay; no reachability, reflection, or promotion claim",
            1,
            True,
        ),
        IntrinsicLoweringLane.R11_ECHO_OUTCOME: _LaneRow(
            CarrierId.R11_RESPONSE,
            "r12.3-r11-echo-replay",
            "bounded ordered R11 echo replay; no equality reflection or promotion claim",
            2,
            True,
        ),
    }
)


def _reject(reason: str) -> NoReturn:
    """Log and raise one stable receipt rejection."""
    logger.error("intrinsic VAM receipt rejected reason=%s", reason)
    raise IntrinsicVamLoweringError(reason)


def digest_transport_data(value: object) -> str:
    """Digest one already bounded canonical diagnostic value."""
    logger.debug("digest_transport_data entry type=%s", type(value).__name__)
    result = digest_bytes(canonical_data_bytes(value))
    logger.debug("digest_transport_data exit digest=%s", result)
    return result


def _receipt_body(receipt: IntrinsicLoweringReceipt) -> dict[str, object]:
    """Serialize every receipt field except its self-binding digest."""
    logger.debug("_receipt_body entry lane=%r", receipt.lane)
    row = _ROWS[receipt.lane]
    result = {
        "schema": LOWERING_SCHEMA,
        "lane": receipt.lane.value,
        "source": row.source.value,
        "provenance": receipt.provenance.value,
        "target": CarrierId.VAM_INTRINSIC_IR.value,
        "capabilities": [BridgeCapability.PRESERVES.value],
        "direction": "preservation",
        "evidence": {
            "class": EvidenceClass.EXECUTABLE_WITNESS.value,
            "scope": EvidenceScope.FINITE.value,
            "id": row.evidence_id,
            "boundary": row.boundary,
            "may_enter_promotion_contract": False,
        },
        "source_digests": list(receipt.source_digests),
        "observer_digest": receipt.observer_digest,
        "response_kind_digest": receipt.response_kind_digest,
        "payload_digest": receipt.payload_digest,
        "ir_schema": INTRINSIC_IR_SCHEMA,
        "ir_digest": receipt.ir_digest,
        "promotion_ready": False,
    }
    logger.debug("_receipt_body exit lane=%s", receipt.lane.value)
    return result


def _make_intrinsic_transport(
    lane: IntrinsicLoweringLane,
    provenance: CarrierId,
    source_digests: tuple[str, ...],
    observer_digest: str,
    kind_digest: str,
    payload_digest: str,
    value: object,
) -> TransportedIntrinsicIR:
    """Create one fixed-row, mutation-evident finite witness transport."""
    logger.debug("_make_intrinsic_transport entry lane=%r", lane)
    if (
        type(lane) is not IntrinsicLoweringLane
        or lane not in _ROWS
        or type(provenance) is not CarrierId
        or provenance not in {CarrierId.R7_RECURRENCE, CarrierId.R9_INTRINSIC_MODE}
    ):
        _reject("invalid-transport-construction")
    row = _ROWS[lane]
    ir_digest = digest_transport_data(intrinsic_ir_data(value))
    receipt = IntrinsicLoweringReceipt(
        LOWERING_SCHEMA,
        lane,
        row.source,
        provenance,
        CarrierId.VAM_INTRINSIC_IR,
        _CAPABILITIES,
        EvidenceClass.EXECUTABLE_WITNESS,
        EvidenceScope.FINITE,
        row.evidence_id,
        source_digests,
        observer_digest,
        kind_digest,
        payload_digest,
        ir_digest,
        row.boundary,
        "",
        False,
    )
    binding = digest_transport_data(_receipt_body(receipt))
    result = TransportedIntrinsicIR(value, replace(receipt, binding_digest=binding))
    logger.debug("_make_intrinsic_transport exit binding=%s", binding)
    return result


def intrinsic_transport_envelope_data(value: object) -> dict[str, object]:
    """Serialize structural data explicitly without accepting its evidence claim."""
    logger.debug("intrinsic_transport_envelope_data entry type=%s", type(value).__name__)
    if type(value) is not TransportedIntrinsicIR or type(value.receipt) is not IntrinsicLoweringReceipt:
        _reject("invalid-transport-bundle")
    receipt = value.receipt
    if type(receipt.lane) is not IntrinsicLoweringLane or receipt.lane not in _ROWS:
        _reject("invalid-transport-lane")
    row = _ROWS[receipt.lane]
    scalar_digests = (receipt.payload_digest, receipt.ir_digest, receipt.binding_digest)
    observed_digests = (receipt.observer_digest, receipt.response_kind_digest)
    if (
        type(receipt.schema) is not str
        or receipt.schema != LOWERING_SCHEMA
        or receipt.source is not row.source
        or type(receipt.provenance) is not CarrierId
        or receipt.provenance not in {CarrierId.R7_RECURRENCE, CarrierId.R9_INTRINSIC_MODE}
        or receipt.target is not CarrierId.VAM_INTRINSIC_IR
        or type(receipt.capabilities) is not tuple
        or len(receipt.capabilities) != 1
        or receipt.capabilities[0] is not BridgeCapability.PRESERVES
        or receipt.evidence_class is not EvidenceClass.EXECUTABLE_WITNESS
        or receipt.evidence_scope is not EvidenceScope.FINITE
        or type(receipt.evidence_id) is not str
        or receipt.evidence_id != row.evidence_id
        or type(receipt.boundary) is not str
        or receipt.boundary != row.boundary
        or receipt.promotion_ready is not False
        or type(receipt.source_digests) is not tuple
        or len(receipt.source_digests) != row.digest_count
        or any(type(item) is not str or not _HEX64.fullmatch(item) for item in receipt.source_digests)
        or any(type(item) is not str or not _HEX64.fullmatch(item) for item in scalar_digests)
        or any(type(item) is not str for item in observed_digests)
        or (row.observed and any(not _HEX64.fullmatch(item) for item in observed_digests))
        or (not row.observed and observed_digests != ("", ""))
        or (receipt.lane is IntrinsicLoweringLane.R7_RECURRENCE and receipt.provenance is not CarrierId.R7_RECURRENCE)
        or (receipt.lane is IntrinsicLoweringLane.R9_INTRINSIC_MODE and receipt.provenance is not CarrierId.R9_INTRINSIC_MODE)
    ):
        _reject("invalid-transport-receipt")
    ir_data = intrinsic_ir_data(value.value)
    if digest_transport_data(ir_data) != receipt.ir_digest:
        _reject("transport-ir-drift")
    body = _receipt_body(receipt)
    if digest_transport_data(body) != receipt.binding_digest:
        _reject("transport-receipt-drift")
    result = {
        "receipt": {**body, "binding_digest": receipt.binding_digest},
        "value": ir_data,
        "verification": "unverified-envelope",
        "evidence_accepted": False,
        "taxonomy_changed": False,
    }
    logger.debug("intrinsic_transport_envelope_data exit lane=%s", receipt.lane.value)
    return result


def _require_intrinsic_replay(expected: TransportedIntrinsicIR, actual: object) -> TransportedIntrinsicIR:
    """Require canonical equality with a freshly replayed expected transport."""
    logger.debug("_require_intrinsic_replay entry")
    expected_data = intrinsic_transport_envelope_data(expected)
    actual_data = intrinsic_transport_envelope_data(actual)
    if canonical_data_bytes(expected_data) != canonical_data_bytes(actual_data):
        _reject("transport-replay-mismatch")
    logger.debug("_require_intrinsic_replay exit trusted=expected")
    return expected

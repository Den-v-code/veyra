"""Domain-separated commitments for finite P1-E4 history evidence."""

from __future__ import annotations

from hashlib import sha256
import logging

from .observer_actualization_types import (
    AccessEdge, ActualizationCounterfactual, HistoryEvent,
    HistoricalAssumption,
)

logger = logging.getLogger(__name__)


def digest(domain: str, fields: tuple[tuple[str, bytes], ...]) -> str:
    """Hash an ordered exact field list under one explicit domain."""
    logger.debug("actualization digest entry domain=%s fields=%d", domain, len(fields))
    h = sha256()
    for token in (b"veyra.p1e4.v1", domain.encode("ascii")):
        h.update(len(token).to_bytes(4, "big"))
        h.update(token)
    for name, value in fields:
        key = name.encode("ascii")
        h.update(len(key).to_bytes(4, "big"))
        h.update(key)
        h.update(len(value).to_bytes(8, "big"))
        h.update(value)
    result = h.hexdigest()
    logger.debug("actualization digest exit domain=%s", domain)
    return result


def event_bytes(value: HistoryEvent) -> bytes:
    logger.debug("event_bytes entry event=%s", value.event_id)
    fields = (
        value.event_id, value.kind.value, "\x1f".join(value.parent_ids),
        str(value.logical_time), value.payload_digest, value.lineage_id,
        value.availability.value,
    )
    result = "\x1e".join(fields).encode("utf-8")
    logger.debug("event_bytes exit event=%s", value.event_id)
    return result


def access_bytes(value: AccessEdge) -> bytes:
    logger.debug("access_bytes entry")
    result = "\x1e".join((
        value.provider_event_id, value.consumer_event_id, value.kind.value,
    )).encode("utf-8")
    logger.debug("access_bytes exit")
    return result


def assumption_bytes(value: HistoricalAssumption) -> bytes:
    logger.debug("assumption_bytes entry")
    result = "\x1e".join((
        value.assumption_id, value.source_event_id, "\x1f".join(value.depends_on),
    )).encode("utf-8")
    logger.debug("assumption_bytes exit")
    return result


def counterfactual_bytes(value: ActualizationCounterfactual) -> bytes:
    logger.debug("counterfactual_bytes entry kind=%s", value.kind.value)
    result = "\x1e".join((
        value.case_id, value.kind.value, value.provider_event_id,
        value.consumer_event_id, value.alternate_target_digest,
        value.copied_lineage_id, "\x1f".join(value.copied_parent_ids),
    )).encode("utf-8")
    logger.debug("counterfactual_bytes exit kind=%s", value.kind.value)
    return result


def policy_digest(values: tuple[int, ...]) -> str:
    logger.debug("policy_digest entry")
    result = digest("resource-policy", tuple(
        (f"bound-{index}", str(value).encode("ascii"))
        for index, value in enumerate(values)
    ))
    logger.debug("policy_digest exit")
    return result


def birth_core_digest(
    history_id: str, lineage_id: str, past: tuple[HistoryEvent, ...],
    birth: HistoryEvent, construction_digest: str, e1_source_digest: str,
    oep_digest: str, target_stage_digest: str, witness_digest: str,
    recurrence_digest: str,
) -> str:
    logger.debug("birth_core_digest entry")
    result = digest("birth-core", (
        ("history-id", history_id.encode()), ("lineage-id", lineage_id.encode()),
        ("past", b"\x00".join(event_bytes(item) for item in past)),
        ("birth", event_bytes(birth)),
        ("construction", construction_digest.encode("ascii")),
        ("e1-source", e1_source_digest.encode("ascii")),
        ("oep", oep_digest.encode("ascii")),
        ("construction-target", target_stage_digest.encode("ascii")),
        ("witness", witness_digest.encode("ascii")),
        ("recurrence", recurrence_digest.encode("ascii")),
    ))
    logger.debug("birth_core_digest exit")
    return result


def token_digest(core_digest: str, lineage_id: str, birth_event_id: str) -> str:
    logger.debug("token_digest entry")
    result = digest("historical-token", (
        ("birth-core", core_digest.encode("ascii")),
        ("lineage", lineage_id.encode()),
        ("birth-event", birth_event_id.encode()),
    ))
    logger.debug("token_digest exit")
    return result


def history_digest(
    history_id: str, token_id: str, events: tuple[HistoryEvent, ...],
    access: tuple[AccessEdge, ...], assumptions: tuple[HistoricalAssumption, ...],
    counterfactuals: tuple[ActualizationCounterfactual, ...],
) -> str:
    logger.debug("history_digest entry")
    result = digest("history", (
        ("history-id", history_id.encode()), ("token", token_id.encode("ascii")),
        ("events", b"\x00".join(event_bytes(item) for item in events)),
        ("access", b"\x00".join(access_bytes(item) for item in access)),
        ("assumptions", b"\x00".join(assumption_bytes(item) for item in assumptions)),
        ("counterfactuals", b"\x00".join(counterfactual_bytes(item) for item in counterfactuals)),
    ))
    logger.debug("history_digest exit")
    return result


def source_digest(
    core: str, token: str, history: str, doctrine: str, scope: str, policy: str,
) -> str:
    logger.debug("source_digest entry")
    result = digest("source", tuple(
        (name, value.encode("ascii")) for name, value in (
            ("core", core), ("token", token), ("history", history),
            ("doctrine", doctrine), ("scope", scope), ("policy", policy),
        )
    ))
    logger.debug("source_digest exit")
    return result


def judgment_digest(
    source: str, statuses: tuple[str, ...], evidence: tuple[str, ...],
) -> str:
    logger.debug("judgment_digest entry")
    result = digest("judgment", (
        ("source", source.encode("ascii")),
        ("statuses", "\x1f".join(statuses).encode()),
        ("evidence", "\x1f".join(evidence).encode()),
    ))
    logger.debug("judgment_digest exit")
    return result

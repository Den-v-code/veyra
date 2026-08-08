"""Fail-closed trusted snapshots for R14.4 winner and corpus inputs."""
from __future__ import annotations

import logging
from typing import NoReturn

from .observer_core_semantics import MAX_RECURRENCE_DEPTH, MAX_RECURRENCE_NODES
from .observer_synthesis_v2_cegis_types import LockedObserverWinnerV2
from .observer_synthesis_v2_corpus import (
    LockedObserverCorpusV2,
    build_locked_corpus_v2,
)
from .observer_synthesis_v2_protocol import (
    ExpectedRelation,
    ObserverCaseV2,
    SplitId,
    build_observer_case_v2,
)
from .proof_core_types import CoreTerm, Pulse, Silence

logger = logging.getLogger(__name__)

EXPECTED_WINNER_ORDINAL = 1
EXPECTED_WINNER_COST = 1
EXPECTED_WINNER_DEPTH = 1
EXPECTED_WINNER_DIGEST = "7eb8dcdbd11c47eb2f8553c26ca2cd4f4a09027deccb2a2a69bee881f927e502"
EXPECTED_WINNER_CANONICAL = (
    b'{"observer":{"child":{"tag":"input"},"primitive":"crest","tag":"apply"},'
    b'"schema":"veyra.observer-core.v2"}'
)
EXPECTED_CORPUS_SCHEMA = "veyra.observer-synthesis-v2.corpus.r14.3a.v1"
EXPECTED_CORPUS_DIGEST = "050352b6964eada5f3bb36d68a7989b11d781ab89e20a92aeaaa9bfe5ce146b1"
EXPECTED_CASE_IDS = (101, 102, 201, 202, 301, 302, 401, 402, 403, 404)
EXPECTED_CASE_DIGESTS = (
    "73bf85b76a2001a79f07345372902a71e9015f75919b6a83a26e8f744bee9c95",
    "8046893653457efe1e81ca45f14b74ec3a856c66f1dc9a33bbda6de166c2c064",
    "48b39d96bc92155cda93881cc0faf1ad86273dc3e480d74b163311b5b4a1293a",
    "4b95c0501d6cdc01822158ae0678934808571012201e0594ca2ddf7bd12e141c",
    "697e56e7d297d2c67613d902f317f1e34a70165c3f8d7d7fc8617e4d8e8b6a1a",
    "84d4d7ec15a1c2df9dcf730b76577504600b411a4a39815ff92b4694e1747c89",
    "529348add488a485fd782fedc0776e0e308ed41df451de8b1270a4d4455e11dd",
    "5cf9666050a93c2902168ee7e6a027f592021f7b34013f71ef0248e421ae5657",
    "3fb062cfa012ca22f29ed09a7b4cb41ff3d50d0231dff58f3c571b18639dce0a",
    "aff6deb8cae77269707718da1e31c6f7472d361f17e3503e365cda8fcd8a1dd8",
)
DEFAULT_LOCKED_WINNER_V2 = LockedObserverWinnerV2(
    EXPECTED_WINNER_ORDINAL,
    EXPECTED_WINNER_COST,
    EXPECTED_WINNER_DEPTH,
    EXPECTED_WINNER_CANONICAL,
    EXPECTED_WINNER_DIGEST,
)


class InvalidTrialV2(ValueError):
    """Malformed or non-default R14.4 input rejected before trial execution."""


def reject_trial_v2(reason: str) -> NoReturn:
    logger.error("reject_trial_v2 entry=error reason=%s", reason)
    raise InvalidTrialV2(reason)


def snapshot_locked_winner_v2(winner: object) -> LockedObserverWinnerV2:
    """Return a fresh exact copy of the sole locked R14.3b winner."""
    logger.debug("snapshot_locked_winner_v2 entry type=%s", type(winner).__name__)
    if type(winner) is not LockedObserverWinnerV2:
        reject_trial_v2("invalid-locked-winner-type")
    try:
        captured = (
            winner.ordinal,
            winner.cost,
            winner.depth,
            winner.canonical,
            winner.digest,
        )
    except AttributeError:
        reject_trial_v2("invalid-locked-winner-fields")
    if (
        type(captured[0]) is not int
        or type(captured[1]) is not int
        or type(captured[2]) is not int
        or type(captured[3]) is not bytes
        or type(captured[4]) is not str
        or captured
        != (
            EXPECTED_WINNER_ORDINAL,
            EXPECTED_WINNER_COST,
            EXPECTED_WINNER_DEPTH,
            EXPECTED_WINNER_CANONICAL,
            EXPECTED_WINNER_DIGEST,
        )
    ):
        reject_trial_v2("invalid-locked-winner-binding")
    result = LockedObserverWinnerV2(
        captured[0],
        captured[1],
        captured[2],
        memoryview(captured[3]).tobytes(),
        captured[4],
    )
    logger.debug("snapshot_locked_winner_v2 exit digest=%s", result.digest[:12])
    return result


def _snapshot_recurrence(term: object) -> CoreTerm:
    logger.debug("_snapshot_recurrence entry type=%s", type(term).__name__)
    node = term
    pulses = 0
    seen: set[int] = set()
    while True:
        if pulses > MAX_RECURRENCE_DEPTH or len(seen) >= MAX_RECURRENCE_NODES:
            reject_trial_v2("trial-recurrence-resource-limit")
        if type(node) is Silence:
            break
        if type(node) is not Pulse or id(node) in seen:
            reject_trial_v2("trial-recurrence-invalid")
        seen.add(id(node))
        pulses += 1
        try:
            node = node.tail
        except AttributeError:
            reject_trial_v2("trial-recurrence-invalid")
    result: CoreTerm = Silence()
    for _ in range(pulses):
        result = Pulse(result)
    logger.debug("_snapshot_recurrence exit pulses=%d", pulses)
    return result


def _snapshot_case(case: object) -> ObserverCaseV2:
    logger.debug("_snapshot_case entry type=%s", type(case).__name__)
    if type(case) is not ObserverCaseV2:
        reject_trial_v2("invalid-trial-case-type")
    try:
        captured = (
            case.case_id,
            case.group_id,
            case.split,
            case.left,
            case.right,
            case.expected,
            case.required_for_winner,
            case.payload_digest,
            case.clone_digest,
            case.case_digest,
        )
    except AttributeError:
        reject_trial_v2("invalid-trial-case-fields")
    if (
        type(captured[0]) is not int
        or type(captured[1]) is not int
        or type(captured[2]) is not SplitId
        or type(captured[5]) is not ExpectedRelation
        or type(captured[6]) is not bool
        or any(type(value) is not str for value in captured[7:])
    ):
        reject_trial_v2("invalid-trial-case-fields")
    try:
        trusted = build_observer_case_v2(
            captured[0],
            captured[1],
            captured[2],
            _snapshot_recurrence(captured[3]),
            _snapshot_recurrence(captured[4]),
            captured[5],
            captured[6],
        )
    except (TypeError, ValueError, RecursionError):
        reject_trial_v2("invalid-trial-case-payload")
    if (
        trusted.payload_digest != captured[7]
        or trusted.clone_digest != captured[8]
        or trusted.case_digest != captured[9]
    ):
        reject_trial_v2("invalid-trial-case-binding")
    logger.debug("_snapshot_case exit case_id=%d", trusted.case_id)
    return trusted


def snapshot_locked_corpus_for_trial_v2(corpus: object) -> LockedObserverCorpusV2:
    """Deep-copy and require the exact pre-fit ten-case default corpus."""
    logger.debug(
        "snapshot_locked_corpus_for_trial_v2 entry type=%s",
        type(corpus).__name__,
    )
    if type(corpus) is not LockedObserverCorpusV2:
        reject_trial_v2("invalid-trial-corpus-type")
    try:
        captured = (corpus.schema, corpus.cases, corpus.corpus_digest)
    except AttributeError:
        reject_trial_v2("invalid-trial-corpus-fields")
    if (
        type(captured[0]) is not str
        or type(captured[1]) is not tuple
        or type(captured[2]) is not str
        or captured[0] != EXPECTED_CORPUS_SCHEMA
        or captured[2] != EXPECTED_CORPUS_DIGEST
        or len(captured[1]) != len(EXPECTED_CASE_IDS)
    ):
        reject_trial_v2("invalid-trial-corpus-header")
    trusted = tuple(_snapshot_case(case) for case in captured[1])
    actual_pins = tuple((case.case_id, case.case_digest) for case in trusted)
    expected_pins = tuple(zip(EXPECTED_CASE_IDS, EXPECTED_CASE_DIGESTS, strict=True))
    if actual_pins != expected_pins:
        reject_trial_v2("invalid-trial-corpus-case-pin")
    try:
        result = build_locked_corpus_v2(trusted)
    except (TypeError, ValueError):
        reject_trial_v2("invalid-trial-corpus-closure")
    if result.corpus_digest != EXPECTED_CORPUS_DIGEST:
        reject_trial_v2("invalid-trial-corpus-digest")
    logger.debug(
        "snapshot_locked_corpus_for_trial_v2 exit cases=%d",
        len(result.cases),
    )
    return result

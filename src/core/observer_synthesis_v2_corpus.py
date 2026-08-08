"""Locked disjoint R14.3a corpus fixed before observer fitting."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import NoReturn

from .proof_core_codec import digest_data
from .proof_core_types import Pulse, Silence
from .observer_synthesis_v2_protocol import (
    CASE_SCHEMA,
    ExpectedRelation,
    ObserverCaseV2,
    ObserverSynthesisProtocolError,
    SplitId,
    build_observer_case_v2,
    validate_observer_case_v2,
)

logger = logging.getLogger(__name__)

CORPUS_SCHEMA = "veyra.observer-synthesis-v2.corpus.r14.3a.v1"
MAX_CORPUS_CASES = 1024


@dataclass(frozen=True, slots=True)
class LockedObserverCorpusV2:
    """Ordered immutable cases and their pre-fit binding digest."""

    schema: str
    cases: tuple[ObserverCaseV2, ...]
    corpus_digest: str


class ObserverSynthesisCorpusError(ValueError):
    """Stable corpus closure, order, or leakage rejection."""


def _reject(reason: str) -> NoReturn:
    logger.error("observer synthesis v2 corpus rejected reason=%s", reason)
    raise ObserverSynthesisCorpusError(reason)


def _corpus_digest(cases: tuple[ObserverCaseV2, ...]) -> str:
    logger.debug("_corpus_digest entry cases=%d", len(cases))
    result = digest_data(
        {
            "case_digests": [case.case_digest for case in cases],
            "case_schema": CASE_SCHEMA,
            "schema": CORPUS_SCHEMA,
        },
        f"{CORPUS_SCHEMA}.locked-order",
    )
    logger.debug("_corpus_digest exit digest=%s", result[:12])
    return result


def build_locked_corpus_v2(
    cases: tuple[ObserverCaseV2, ...],
) -> LockedObserverCorpusV2:
    """Build a split-complete corpus with unique IDs and ordered payloads."""
    logger.debug(
        "build_locked_corpus_v2 entry type=%s",
        type(cases).__name__,
    )
    if (
        type(cases) is not tuple
        or not cases
        or len(cases) > MAX_CORPUS_CASES
    ):
        _reject("invalid-corpus-cases")
    try:
        checked = tuple(validate_observer_case_v2(case) for case in cases)
    except ObserverSynthesisProtocolError:
        _reject("invalid-corpus-case")
    ids = tuple(case.case_id for case in checked)
    payloads = tuple(case.payload_digest for case in checked)
    digests = tuple(case.case_digest for case in checked)
    group_splits: dict[int, SplitId] = {}
    clone_splits: dict[str, SplitId] = {}
    for case in checked:
        prior_group = group_splits.setdefault(case.group_id, case.split)
        prior_clone = clone_splits.setdefault(case.clone_digest, case.split)
        if prior_group is not case.split or prior_clone is not case.split:
            _reject("corpus-cross-split-clone-leakage")
    ranks = {split: ordinal for ordinal, split in enumerate(SplitId)}
    ordered = tuple(sorted(checked, key=lambda case: (ranks[case.split], case.case_id)))
    if (
        len(set(ids)) != len(ids)
        or len(set(payloads)) != len(payloads)
        or len(set(digests)) != len(digests)
        or checked != ordered
        or {case.split for case in checked} != set(SplitId)
    ):
        _reject("invalid-corpus-closure")
    result = LockedObserverCorpusV2(
        CORPUS_SCHEMA,
        checked,
        _corpus_digest(checked),
    )
    logger.debug("build_locked_corpus_v2 exit cases=%d", len(result.cases))
    return result


def validate_locked_corpus_v2(corpus: object) -> LockedObserverCorpusV2:
    """Replay exact type, closure, order, cases, and corpus binding."""
    logger.debug("validate_locked_corpus_v2 entry type=%s", type(corpus).__name__)
    if (
        type(corpus) is not LockedObserverCorpusV2
        or type(corpus.schema) is not str
        or corpus.schema != CORPUS_SCHEMA
        or type(corpus.cases) is not tuple
        or type(corpus.corpus_digest) is not str
    ):
        _reject("invalid-corpus-fields")
    rebuilt = build_locked_corpus_v2(corpus.cases)
    if rebuilt != corpus:
        _reject("invalid-corpus-binding")
    logger.debug("validate_locked_corpus_v2 exit cases=%d", len(corpus.cases))
    return corpus


def cases_for_split_v2(
    corpus: object,
    split: object,
) -> tuple[ObserverCaseV2, ...]:
    """Return one exact precommitted split without dynamic selectors."""
    logger.debug(
        "cases_for_split_v2 entry split_type=%s",
        type(split).__name__,
    )
    valid = validate_locked_corpus_v2(corpus)
    if type(split) is not SplitId:
        _reject("invalid-corpus-split")
    result = tuple(case for case in valid.cases if case.split is split)
    logger.debug(
        "cases_for_split_v2 exit split=%s cases=%d",
        split.value,
        len(result),
    )
    return result


def winner_required_cases_v2(
    corpus: object,
) -> tuple[ObserverCaseV2, ...]:
    """Return only precommitted winner obligations; diagnostics stay separate."""
    logger.debug("winner_required_cases_v2 entry")
    valid = validate_locked_corpus_v2(corpus)
    result = tuple(case for case in valid.cases if case.required_for_winner)
    logger.debug("winner_required_cases_v2 exit cases=%d", len(result))
    return result


SILENCE = Silence()
PULSE_1 = Pulse(SILENCE)
PULSE_2 = Pulse(PULSE_1)
PULSE_3 = Pulse(PULSE_2)
PULSE_4 = Pulse(PULSE_3)
PULSE_5 = Pulse(PULSE_4)

DEFAULT_CASES = (
    build_observer_case_v2(101, 1001, SplitId.TRAIN, SILENCE, PULSE_1, ExpectedRelation.SEPARATE, True),
    build_observer_case_v2(102, 1002, SplitId.TRAIN, PULSE_1, PULSE_2, ExpectedRelation.ECHO, True),
    build_observer_case_v2(201, 2001, SplitId.HOLDOUT, SILENCE, PULSE_2, ExpectedRelation.SEPARATE, True),
    build_observer_case_v2(202, 2002, SplitId.HOLDOUT, PULSE_2, PULSE_2, ExpectedRelation.ECHO, True),
    build_observer_case_v2(301, 3001, SplitId.UNSEEN, PULSE_4, PULSE_5, ExpectedRelation.ECHO, True),
    build_observer_case_v2(302, 3002, SplitId.UNSEEN, SILENCE, PULSE_4, ExpectedRelation.SEPARATE, True),
    build_observer_case_v2(401, 4001, SplitId.ADVERSARIAL, PULSE_3, SILENCE, ExpectedRelation.SEPARATE, True),
    build_observer_case_v2(402, 4002, SplitId.ADVERSARIAL, PULSE_4, PULSE_4, ExpectedRelation.ECHO, True),
    build_observer_case_v2(
        403,
        4003,
        SplitId.ADVERSARIAL,
        SILENCE,
        PULSE_5,
        ExpectedRelation.DOMAIN_BLOCKED,
        False,
    ),
    build_observer_case_v2(
        404,
        4003,
        SplitId.ADVERSARIAL,
        PULSE_5,
        SILENCE,
        ExpectedRelation.DOMAIN_BLOCKED,
        False,
    ),
)
DEFAULT_LOCKED_CORPUS = build_locked_corpus_v2(DEFAULT_CASES)
EXPECTED_DEFAULT_CORPUS_DIGEST = (
    "050352b6964eada5f3bb36d68a7989b11d781ab89e20a92aeaaa9bfe5ce146b1"
)


def _verify_default_corpus_pin() -> None:
    logger.debug("_verify_default_corpus_pin entry")
    if DEFAULT_LOCKED_CORPUS.corpus_digest != EXPECTED_DEFAULT_CORPUS_DIGEST:
        logger.error("default R14.3a corpus digest drift")
        raise RuntimeError("default-r14.3a-corpus-digest-drift")
    logger.debug("_verify_default_corpus_pin exit")


_verify_default_corpus_pin()

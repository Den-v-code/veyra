"""Pure pinned assembly for in-process and isolated R14.4 trials."""
from __future__ import annotations

from dataclasses import replace
import logging
from typing import Callable

from .observer_synthesis_v2_baselines import EXPECTED_SUBJECT_DIGESTS
from .observer_synthesis_v2_cegis_types import LockedObserverWinnerV2
from .observer_synthesis_v2_corpus import LockedObserverCorpusV2
from .observer_synthesis_v2_grammar import enumerate_observer_grammar_v2
from .observer_synthesis_v2_protocol import SplitId
from .observer_synthesis_v2_trial_codec import guarantee_data_v2, subject_result_data_v2
from .observer_synthesis_v2_trial_types import (
    BoundedGuaranteeV2,
    ObserverTrialReportV2,
    TrialSubjectManifestV2,
    TrialSubjectResultV2,
)
from .observer_synthesis_v2_trial_provenance import (
    _brand_trial_report_v2,
    require_trial_subject_brand_v2,
)
from .observer_synthesis_v2_trial_validation import InvalidTrialV2
from .observer_synthesis_v2_validation import verify_observer_grammar_enumeration_v2
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

TRIAL_SCHEMA = "veyra.observer-synthesis-v2.trial.r14.4.v1"
GUARANTEE_SCHEMA = "veyra.observer-synthesis-v2.guarantee.r14.4.v1"
BOUNDARY = (
    "exact finite 1,565-row R11 grammar, locked ten-case corpus, and five "
    "predeclared AST subjects only; no general completeness, minimality, "
    "novelty, superiority, proof, evidence, promotion, or taxonomy claim"
)
EXPECTED_WINNER_RELATIONS = (
    "SEPARATE", "ECHO", "SEPARATE", "ECHO", "ECHO",
    "SEPARATE", "SEPARATE", "ECHO", "SEPARATE", "SEPARATE",
)
EXPECTED_WINNER_MATCHES = (
    True, True, True, True, True, True, True, True, False, False,
)
EXPECTED_GUARANTEE_DIGEST = "56287ca10c7de90bb04bb4794ad6fb455511675304357031370b76866531dba9"
EXPECTED_TRIAL_REPORT_DIGEST = "07dbfe7567f86a2817bd01317ceb14e8c8650fd2ed488a7e1a6a7aad5f890f48"


def build_bounded_guarantee_v2(
    subjects: tuple[TrialSubjectResultV2, ...],
    catalog_provider: Callable[[], object] = enumerate_observer_grammar_v2,
) -> BoundedGuaranteeV2:
    """Build only the exact finite guarantee after catalog replay."""
    logger.debug("build_bounded_guarantee_v2 entry subjects=%d", len(subjects))
    try:
        valid_catalog = verify_observer_grammar_enumeration_v2(
            catalog_provider()
        )
    except (AttributeError, TypeError, ValueError) as exc:
        logger.error("build_bounded_guarantee_v2 malformed catalog")
        raise InvalidTrialV2("invalid-trial-catalog") from exc
    if not valid_catalog:
        logger.error("build_bounded_guarantee_v2 invalid catalog")
        raise InvalidTrialV2("invalid-trial-catalog")
    winner = subjects[0]
    train = winner.splits[0]
    postfit = tuple(
        row for row in winner.cases
        if row.split is not SplitId.TRAIN and row.required_for_winner
    )
    prior = tuple(
        subject for subject in subjects
        if subject.observer_digest == EXPECTED_SUBJECT_DIGESTS[1]
    )
    prefix_minimal = len(prior) == 1 and all(
        row.splits[0].required_matched < row.splits[0].required_total
        for row in prior
    )
    resource_complete = len(subjects) == 5 and all(
        len(row.cases) == 10
        and row.accounting.candidates == 1
        and row.accounting.canonical_bytes > 0
        and row.accounting.evaluations == 10
        and row.accounting.retained_output_bytes > 0
        and not row.accounting.cutoff
        for row in subjects
    )
    provisional = BoundedGuaranteeV2(
        True,
        prefix_minimal,
        train.required_matched,
        train.required_total,
        sum(row.matched for row in postfit),
        len(postfit),
        winner.required_matched,
        winner.required_total,
        winner.diagnostic_matched,
        winner.diagnostic_total,
        resource_complete,
        False, False, False, False, False, False, False, False,
        "",
        BOUNDARY,
    )
    result = replace(
        provisional,
        guarantee_digest=digest_data(
            guarantee_data_v2(provisional),
            f"{GUARANTEE_SCHEMA}.bounded",
        ),
    )
    if result.guarantee_digest != EXPECTED_GUARANTEE_DIGEST:
        logger.error("build_bounded_guarantee_v2 digest drift")
        raise RuntimeError("r14.4-guarantee-digest-drift")
    logger.debug("build_bounded_guarantee_v2 exit digest=%s", result.guarantee_digest[:12])
    return result


def verify_winner_pins_v2(report: TrialSubjectResultV2) -> None:
    """Require the literal ten-case winner vector and split counts."""
    logger.debug("verify_winner_pins_v2 entry")
    relations = tuple(row.actual.value for row in report.cases)
    matches = tuple(row.matched for row in report.cases)
    counts = (
        report.splits[0].required_matched,
        report.splits[0].required_total,
        sum(row.required_matched for row in report.splits[1:]),
        sum(row.required_total for row in report.splits[1:]),
        report.required_matched,
        report.required_total,
        report.diagnostic_matched,
        report.diagnostic_total,
    )
    if (
        relations != EXPECTED_WINNER_RELATIONS
        or matches != EXPECTED_WINNER_MATCHES
        or counts != (2, 2, 6, 6, 8, 8, 0, 2)
    ):
        logger.error("verify_winner_pins_v2 semantic drift")
        raise RuntimeError("r14.4-winner-semantic-drift")
    logger.debug("verify_winner_pins_v2 exit")


def assemble_locked_trial_report_v2(
    winner: LockedObserverWinnerV2,
    corpus: LockedObserverCorpusV2,
    manifest: TrialSubjectManifestV2,
    subjects: tuple[TrialSubjectResultV2, ...],
    catalog_provider: Callable[[], object] = enumerate_observer_grammar_v2,
) -> ObserverTrialReportV2:
    """Assemble the pinned report without executing observer semantics."""
    logger.debug("assemble_locked_trial_report_v2 entry subjects=%d", len(subjects))
    if type(subjects) is not tuple:
        logger.error("assemble_locked_trial_report_v2 unbranded subject container")
        raise InvalidTrialV2("invalid-trial-subject-provenance")
    try:
        subjects = tuple(
            require_trial_subject_brand_v2(row, index)
            for index, row in enumerate(subjects)
        )
    except ValueError as exc:
        logger.error("assemble_locked_trial_report_v2 unbranded subject")
        raise InvalidTrialV2("invalid-trial-subject-provenance") from exc
    if (
        len(subjects) != 5
        or tuple(row.subject_id for row in subjects)
        != tuple(row.subject_id for row in manifest.subjects)
        or tuple(row.observer_digest for row in subjects)
        != tuple(row.digest for row in manifest.subjects)
    ):
        logger.error("assemble_locked_trial_report_v2 subject binding invalid")
        raise InvalidTrialV2("invalid-trial-subject-binding")
    verify_winner_pins_v2(subjects[0])
    guarantee = build_bounded_guarantee_v2(subjects, catalog_provider)
    report_data = {
        "corpus_digest": corpus.corpus_digest,
        "guarantee_digest": guarantee.guarantee_digest,
        "manifest_digest": manifest.manifest_digest,
        "schema": TRIAL_SCHEMA,
        "subjects": [subject_result_data_v2(row) for row in subjects],
        "winner_digest": winner.digest,
    }
    provisional = ObserverTrialReportV2(
        TRIAL_SCHEMA,
        winner.digest,
        corpus.corpus_digest,
        manifest.manifest_digest,
        subjects,
        guarantee,
        digest_data(report_data, f"{TRIAL_SCHEMA}.report"),
        BOUNDARY,
    )
    if provisional.report_digest != EXPECTED_TRIAL_REPORT_DIGEST:
        logger.error("assemble_locked_trial_report_v2 report digest drift")
        raise RuntimeError("r14.4-trial-report-digest-drift")
    result = _brand_trial_report_v2(provisional)
    logger.debug("assemble_locked_trial_report_v2 exit digest=%s", result.report_digest[:12])
    return result

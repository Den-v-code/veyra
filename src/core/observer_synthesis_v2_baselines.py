"""Exact five-subject R14.4 synthesized/control AST manifest."""
from __future__ import annotations

from hashlib import sha256
import logging

from .observer_core_codec import canonical_observer_bytes
from .observer_core_types import Apply, Input, ObserverExpr, Pair, PrimitiveId
from .observer_synthesis_v2_trial_types import (
    TrialSubjectManifestV2,
    TrialSubjectRoleV2,
    TrialSubjectV2,
)
from .observer_synthesis_v2_trial_validation import (
    EXPECTED_WINNER_DIGEST,
    LockedObserverWinnerV2,
    snapshot_locked_winner_v2,
)
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

SUBJECT_SCHEMA = "veyra.observer-synthesis-v2.subjects.r14.4.v1"
EXPECTED_SUBJECT_IDS = (
    "synthesized-winner",
    "baseline-input",
    "baseline-tail-input",
    "baseline-crest-input",
    "baseline-pair-input-input",
)
EXPECTED_SUBJECT_DIGESTS = (
    EXPECTED_WINNER_DIGEST,
    "5eb21cbbf9ace8fb6c9264119177bf610a4c6f3dcaec5cad5820f8f2729542c4",
    "576b993359acca70bee23e9694c18b1b088ac4589d9392dc30d81a7fe57e4e2c",
    EXPECTED_WINNER_DIGEST,
    "d12028350c64525f6d5fae5f51600d4ea576fde36b42dde9f0ecaa777b841f92",
)
EXPECTED_SUBJECT_BYTES = (106, 62, 105, 106, 108)
EXPECTED_SUBJECT_MANIFEST_DIGEST = (
    "4de40e8fdc41475c7e2f39d4370aecb0447e1b73b0254d723d17b1dc49221317"
)


def _subject(
    subject_id: str,
    role: TrialSubjectRoleV2,
    observer: ObserverExpr,
) -> TrialSubjectV2:
    logger.debug("_subject entry subject_id=%s", subject_id)
    canonical = canonical_observer_bytes(observer)
    result = TrialSubjectV2(
        subject_id,
        role,
        observer,
        canonical,
        sha256(canonical).hexdigest(),
    )
    logger.debug("_subject exit digest=%s", result.digest[:12])
    return result


def _manifest_data(subjects: tuple[TrialSubjectV2, ...]) -> dict[str, object]:
    logger.debug("_manifest_data entry subjects=%d", len(subjects))
    result: dict[str, object] = {
        "schema": SUBJECT_SCHEMA,
        "subjects": [
            {
                "canonical": subject.canonical.decode("ascii"),
                "digest": subject.digest,
                "role": subject.role.value,
                "subject_id": subject.subject_id,
            }
            for subject in subjects
        ],
    }
    logger.debug("_manifest_data exit")
    return result


def build_trial_subject_manifest_v2(
    winner: LockedObserverWinnerV2,
) -> TrialSubjectManifestV2:
    """Build the exact winner plus four named same-information R11 controls."""
    logger.debug("build_trial_subject_manifest_v2 entry")
    trusted = snapshot_locked_winner_v2(winner)
    subjects = (
        _subject(
            EXPECTED_SUBJECT_IDS[0],
            TrialSubjectRoleV2.SYNTHESIZED,
            Apply(PrimitiveId.CREST, Input()),
        ),
        _subject(EXPECTED_SUBJECT_IDS[1], TrialSubjectRoleV2.BASELINE, Input()),
        _subject(
            EXPECTED_SUBJECT_IDS[2],
            TrialSubjectRoleV2.BASELINE,
            Apply(PrimitiveId.TAIL, Input()),
        ),
        _subject(
            EXPECTED_SUBJECT_IDS[3],
            TrialSubjectRoleV2.BASELINE,
            Apply(PrimitiveId.CREST, Input()),
        ),
        _subject(
            EXPECTED_SUBJECT_IDS[4],
            TrialSubjectRoleV2.BASELINE,
            Pair(Input(), Input()),
        ),
    )
    actual = (
        tuple(subject.subject_id for subject in subjects),
        tuple(subject.digest for subject in subjects),
        tuple(len(subject.canonical) for subject in subjects),
    )
    expected = (EXPECTED_SUBJECT_IDS, EXPECTED_SUBJECT_DIGESTS, EXPECTED_SUBJECT_BYTES)
    if actual != expected or subjects[0].canonical != trusted.canonical:
        logger.error("R14.4 subject manifest drift")
        raise RuntimeError("r14.4-subject-manifest-drift")
    result = TrialSubjectManifestV2(
        SUBJECT_SCHEMA,
        subjects,
        digest_data(_manifest_data(subjects), f"{SUBJECT_SCHEMA}.manifest"),
    )
    if result.manifest_digest != EXPECTED_SUBJECT_MANIFEST_DIGEST:
        logger.error("R14.4 subject manifest digest drift")
        raise RuntimeError("r14.4-subject-manifest-digest-drift")
    logger.debug(
        "build_trial_subject_manifest_v2 exit digest=%s",
        result.manifest_digest[:12],
    )
    return result

"""Exact run-local provenance for prevalidated R14 trial case DTOs."""
from __future__ import annotations

from dataclasses import dataclass, replace
import logging
from typing import cast

from .observer_synthesis_v2_protocol import ExpectedRelation, SplitId
from .observer_synthesis_v2_trial_codec import case_result_data_v2
from .observer_synthesis_v2_trial_types import TrialCaseResultV2
from .proof_core_codec import digest_data

logger = logging.getLogger(__name__)

_CASE_SEAL = object()
_CASE_BRAND_SCHEMA = "veyra.observer-synthesis-v2.case-brand.r14.5c.v1"


@dataclass(frozen=True, slots=True)
class _CaseBrandV2:
    """Unserialized validator provenance for one subject/case position."""

    seal: object
    subject_index: int
    case_index: int
    binding_digest: str


def _case_shape_v2(case: object) -> bool:
    logger.debug("_case_shape_v2 entry type=%s", type(case).__name__)
    if type(case) is not TrialCaseResultV2:
        return False
    try:
        result = (
            type(case.case_id) is int
            and type(case.case_digest) is str
            and type(case.split) is SplitId
            and type(case.required_for_winner) is bool
            and type(case.expected) is ExpectedRelation
            and type(case.actual) is ExpectedRelation
            and type(case.matched) is bool
            and type(case.outcome_digest) is str
        )
    except AttributeError:
        logger.exception("_case_shape_v2 deleted field")
        result = False
    logger.debug("_case_shape_v2 exit valid=%s", result)
    return result


def _brand_trial_case_v2(
    case: TrialCaseResultV2,
    subject_index: int,
    case_index: int,
) -> TrialCaseResultV2:
    """Brand one freshly evaluated or fully parsed case position."""
    logger.debug(
        "_brand_trial_case_v2 entry subject=%r case=%r",
        subject_index,
        case_index,
    )
    if (
        not _case_shape_v2(case)
        or type(subject_index) is not int
        or type(case_index) is not int
    ):
        logger.error("_brand_trial_case_v2 invalid source")
        raise ValueError("invalid-trial-case-brand-source")
    brand = _CaseBrandV2(
        _CASE_SEAL,
        subject_index,
        case_index,
        digest_data(case_result_data_v2(case), _CASE_BRAND_SCHEMA),
    )
    result = replace(case, provenance=brand)
    logger.debug("_brand_trial_case_v2 exit digest=%s", brand.binding_digest[:12])
    return result


def require_trial_case_brand_v2(
    case: object,
    subject_index: int,
    case_index: int,
) -> TrialCaseResultV2:
    """Reject even equal-value case DTOs transplanted across positions."""
    logger.debug(
        "require_trial_case_brand_v2 entry subject=%r case=%r",
        subject_index,
        case_index,
    )
    if not _case_shape_v2(case):
        logger.error("require_trial_case_brand_v2 invalid shape")
        raise ValueError("invalid-trial-case-provenance")
    trusted = cast(TrialCaseResultV2, case)
    try:
        brand = trusted.provenance
        valid = (
            type(brand) is _CaseBrandV2
            and brand.seal is _CASE_SEAL
            and brand.subject_index == subject_index
            and brand.case_index == case_index
            and type(brand.binding_digest) is str
            and brand.binding_digest
            == digest_data(case_result_data_v2(trusted), _CASE_BRAND_SCHEMA)
        )
    except (AttributeError, TypeError, ValueError):
        logger.exception("require_trial_case_brand_v2 malformed case")
        valid = False
    if not valid:
        logger.error("require_trial_case_brand_v2 provenance mismatch")
        raise ValueError("invalid-trial-case-provenance")
    logger.debug("require_trial_case_brand_v2 exit")
    return trusted

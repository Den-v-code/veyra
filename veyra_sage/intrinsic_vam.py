"""Sage-facing presentation of the certified intrinsic-VAM R12 lane."""

from __future__ import annotations

import logging

from src.core.certify_intrinsic_vam import certify_intrinsic_vam_r12
from src.core.certify_types import Certificate

logger = logging.getLogger(__name__)

SAGE_INTRINSIC_VAM_SCHEMA = "veyra.sage.intrinsic-vam.r12.6.v1"
_CERTIFICATE_NAME = "intrinsic_vam_r12"
_BOUNDARY = (
    "presentation of core certificate, not independent evidence "
    "or promotion contract"
)


def _intrinsic_vam_presentation(certificate: Certificate) -> dict[str, object]:
    """Render one exact core R12 certificate without accepting new evidence."""
    logger.debug(
        "_intrinsic_vam_presentation entry certificate_type=%s",
        type(certificate).__name__,
    )
    if type(certificate) is not Certificate:
        logger.error(
            "_intrinsic_vam_presentation rejected certificate_type=%s",
            type(certificate).__name__,
        )
        raise TypeError("intrinsic-VAM presentation requires an exact Certificate")
    if (
        certificate.name != _CERTIFICATE_NAME
        or type(certificate.method) is not str
        or type(certificate.passed) is not bool
        or type(certificate.detail) is not str
        or certificate.level != 2
    ):
        logger.error(
            "_intrinsic_vam_presentation rejected name=%s level=%s",
            certificate.name,
            certificate.level,
        )
        raise ValueError("intrinsic-VAM presentation requires the R12 certificate")
    result: dict[str, object] = {
        "schema": SAGE_INTRINSIC_VAM_SCHEMA,
        "certificate": certificate.name,
        "method": certificate.method,
        "passed": certificate.passed,
        "detail": certificate.detail,
        "level": certificate.level,
        "theorems": 9,
        "lanes": 4,
        "vami_frames": 4,
        "capability": "preserves",
        "evidence": "formal-bridge",
        "scope": "general",
        "presentation_only": True,
        "evidence_accepted": False,
        "promotion_ready": False,
        "taxonomy_changed": False,
        "proof_complete": False,
        "boundary": _BOUNDARY,
    }
    logger.debug(
        "_intrinsic_vam_presentation exit passed=%s promotion_ready=%s",
        result["passed"],
        result["promotion_ready"],
    )
    return result


class VeyraIntrinsicVamLab:
    """Read-only Sage presentation backed by one real core R12 certificate."""

    def __init__(self) -> None:
        """Run the core certificate exactly once for this lab instance."""
        logger.debug("VeyraIntrinsicVamLab.__init__ entry")
        try:
            certificate = certify_intrinsic_vam_r12()
        except Exception:
            logger.exception("VeyraIntrinsicVamLab.__init__ core certificate failed")
            raise
        self._presentation = _intrinsic_vam_presentation(certificate)
        logger.debug(
            "VeyraIntrinsicVamLab.__init__ exit passed=%s",
            self._presentation["passed"],
        )

    def certificate_row(self) -> dict[str, object]:
        """Return a fresh JSON-ready presentation row."""
        logger.debug("VeyraIntrinsicVamLab.certificate_row entry")
        result = dict(self._presentation)
        logger.debug(
            "VeyraIntrinsicVamLab.certificate_row exit passed=%s",
            result["passed"],
        )
        return result

    def summary(self) -> dict[str, object]:
        """Return the exact non-claim presentation summary."""
        logger.debug("VeyraIntrinsicVamLab.summary entry")
        result = self.certificate_row()
        logger.debug(
            "VeyraIntrinsicVamLab.summary exit schema=%s",
            result["schema"],
        )
        return result

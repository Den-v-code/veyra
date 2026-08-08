"""Presentation-only Sage facade for the exact finite R14 certificate."""
from __future__ import annotations

import logging

from src.core.certify_observer_synthesis_v2 import (
    R14_CERTIFICATE_DETAIL,
    R14_CERTIFICATE_METHOD,
    R14_CERTIFICATE_NAME,
    certify_observer_synthesis_v2_r14,
)
from src.core.certify_types import Certificate

logger = logging.getLogger(__name__)

SAGE_OBSERVER_SYNTHESIS_V2_SCHEMA = (
    "veyra.sage.observer-synthesis-v2.r14.6.v1"
)
_BOUNDARY = (
    "presentation of the exact passing core R14 finite audit certificate; no "
    "semantic replay, theorem, formal proof, R8 evidence, or promotion"
)


def _certificate_snapshot(certificate: object) -> tuple[str, str, bool, str, int]:
    """Capture and exact-type one core certificate before comparisons."""
    logger.debug("_certificate_snapshot entry type=%s", type(certificate).__name__)
    if type(certificate) is not Certificate:
        raise TypeError("R14 presentation requires an exact Certificate")
    try:
        fields = (
            certificate.name, certificate.method, certificate.passed,
            certificate.detail, certificate.level,
        )
    except AttributeError as error:
        logger.exception("_certificate_snapshot deleted slot")
        raise TypeError("R14 certificate requires complete slots") from error
    kinds = (str, str, bool, str, int)
    if any(type(item) is not kind for item, kind in zip(fields, kinds)):
        raise ValueError("R14 certificate requires exact scalar types")
    logger.debug("_certificate_snapshot exit")
    return fields


def _presentation_from_snapshot(
    fields: tuple[str, str, bool, str, int],
) -> dict[str, object]:
    """Render one already-captured exact certificate snapshot."""
    logger.debug("_presentation_from_snapshot entry")
    name, method, passed, detail, level = fields
    if fields != (
        R14_CERTIFICATE_NAME, R14_CERTIFICATE_METHOD, True,
        R14_CERTIFICATE_DETAIL, 3,
    ):
        raise ValueError("R14 presentation requires the exact core certificate")
    result: dict[str, object] = {
        "schema": SAGE_OBSERVER_SYNTHESIS_V2_SCHEMA,
        "certificate": name,
        "method": method,
        "passed": passed,
        "detail": detail,
        "level": level,
        "finite_audit": True,
        "subjects": 5,
        "cases": 10,
        "required": "8/8",
        "diagnostic": "0/2",
        "receipt_rows": 10,
        "taxonomy": "2/4/25/5",
        "layers": 36,
        "presentation_only": True,
        "semantic_replay": False,
        "theorem": False,
        "formal_proof": False,
        "r8_evidence": False,
        "evidence_accepted": False,
        "promotion_ready": False,
        "taxonomy_changed": False,
        "proof_complete": False,
        "boundary": _BOUNDARY,
    }
    logger.debug("_presentation_from_snapshot exit passed=%s", passed)
    return result


def _observer_synthesis_v2_presentation(
    certificate: Certificate,
) -> dict[str, object]:
    """Render one exact core certificate without accepting new evidence."""
    logger.debug(
        "_observer_synthesis_v2_presentation entry certificate_type=%s",
        type(certificate).__name__,
    )
    result = _presentation_from_snapshot(_certificate_snapshot(certificate))
    logger.debug(
        "_observer_synthesis_v2_presentation exit passed=%s",
        result["passed"],
    )
    return result


def _observer_synthesis_v2_from_core(
    certificates: list[Certificate],
) -> dict[str, object]:
    """Select exactly one already-run core certificate without replaying it."""
    logger.debug(
        "_observer_synthesis_v2_from_core entry count=%s",
        len(certificates) if type(certificates) is list else "invalid",
    )
    if type(certificates) is not list:
        raise TypeError("R14 core certificate collection must be an exact list")
    snapshots = tuple(_certificate_snapshot(item) for item in certificates)
    matches = [row for row in snapshots if row[0] == R14_CERTIFICATE_NAME]
    if len(matches) != 1:
        logger.error(
            "_observer_synthesis_v2_from_core matches=%d",
            len(matches),
        )
        raise RuntimeError("core suite requires one observer_synthesis_v2_r14")
    result = _presentation_from_snapshot(matches[0])
    logger.debug("_observer_synthesis_v2_from_core exit")
    return result


class VeyraObserverSynthesisV2Lab:
    """Read-only Sage presentation backed by one real core R14 certificate."""

    def __init__(self) -> None:
        """Run the core certificate exactly once for this lab instance."""
        logger.debug("VeyraObserverSynthesisV2Lab.__init__ entry")
        try:
            certificate = certify_observer_synthesis_v2_r14()
        except Exception:
            logger.exception(
                "VeyraObserverSynthesisV2Lab.__init__ certificate failed",
            )
            raise
        self._presentation = _observer_synthesis_v2_presentation(certificate)
        logger.debug(
            "VeyraObserverSynthesisV2Lab.__init__ exit passed=%s",
            self._presentation["passed"],
        )

    def certificate_row(self) -> dict[str, object]:
        """Return a fresh JSON-ready exact core-certificate presentation."""
        logger.debug("VeyraObserverSynthesisV2Lab.certificate_row entry")
        result = dict(self._presentation)
        logger.debug(
            "VeyraObserverSynthesisV2Lab.certificate_row exit passed=%s",
            result["passed"],
        )
        return result

    def summary(self) -> dict[str, object]:
        """Return the exact finite-audit nonclaim presentation."""
        logger.debug("VeyraObserverSynthesisV2Lab.summary entry")
        result = self.certificate_row()
        logger.debug(
            "VeyraObserverSynthesisV2Lab.summary exit schema=%s",
            result["schema"],
        )
        return result

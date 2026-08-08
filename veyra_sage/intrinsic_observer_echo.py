"""Sage-facing presentation of the exact R13 observer-echo certificate."""
from __future__ import annotations

import logging

from src.core.certify_intrinsic_observer_echo import (
    R13_CERTIFICATE_DETAIL,
    R13_CERTIFICATE_METHOD,
    certify_intrinsic_observer_echo_r13,
)
from src.core.certify_types import Certificate

logger = logging.getLogger(__name__)
SAGE_INTRINSIC_OBSERVER_ECHO_SCHEMA = (
    "veyra.sage.intrinsic-observer-echo.r13.4.v1"
)
_CERTIFICATE_NAME = "intrinsic_observer_echo_r13"
_BOUNDARY = (
    "presentation of the exact core R13 certificate, not independent Sage "
    "evidence, a broader echo theorem, or proof completeness"
)


def _intrinsic_observer_echo_presentation(
    certificate: Certificate,
) -> dict[str, object]:
    """Render one exact core R13 certificate without accepting new evidence."""
    logger.debug(
        "_intrinsic_observer_echo_presentation entry certificate_type=%s",
        type(certificate).__name__,
    )
    if type(certificate) is not Certificate:
        raise TypeError("R13 presentation requires an exact Certificate")
    if (
        certificate.name != _CERTIFICATE_NAME
        or certificate.method != R13_CERTIFICATE_METHOD
        or certificate.passed is not True
        or certificate.detail != R13_CERTIFICATE_DETAIL
        or certificate.level != 3
    ):
        raise ValueError("R13 presentation requires the exact core certificate")
    result: dict[str, object] = {
        "schema": SAGE_INTRINSIC_OBSERVER_ECHO_SCHEMA,
        "certificate": certificate.name,
        "method": certificate.method,
        "passed": certificate.passed,
        "detail": certificate.detail,
        "level": certificate.level,
        "theorem": "THM-R13-003",
        "formal_theorems": 5,
        "executable_rows": 3,
        "contract_promoted": True,
        "theorem_derived_layers": 2,
        "presentation_only": True,
        "evidence_accepted": False,
        "proof_complete": False,
        "boundary": _BOUNDARY,
    }
    logger.debug(
        "_intrinsic_observer_echo_presentation exit passed=%s",
        result["passed"],
    )
    return result


class VeyraIntrinsicObserverEchoLab:
    """Read-only Sage presentation backed by one real core R13 certificate."""

    def __init__(self) -> None:
        """Run the core certificate exactly once for this lab instance."""
        logger.debug("VeyraIntrinsicObserverEchoLab.__init__ entry")
        try:
            certificate = certify_intrinsic_observer_echo_r13()
        except Exception:
            logger.exception(
                "VeyraIntrinsicObserverEchoLab.__init__ certificate failed",
            )
            raise
        self._presentation = _intrinsic_observer_echo_presentation(certificate)
        logger.debug(
            "VeyraIntrinsicObserverEchoLab.__init__ exit passed=%s",
            self._presentation["passed"],
        )

    def certificate_row(self) -> dict[str, object]:
        """Return a fresh JSON-ready exact core-certificate presentation."""
        logger.debug("VeyraIntrinsicObserverEchoLab.certificate_row entry")
        result = dict(self._presentation)
        logger.debug(
            "VeyraIntrinsicObserverEchoLab.certificate_row exit passed=%s",
            result["passed"],
        )
        return result

    def summary(self) -> dict[str, object]:
        """Return the exact non-claim presentation summary."""
        logger.debug("VeyraIntrinsicObserverEchoLab.summary entry")
        result = self.certificate_row()
        logger.debug(
            "VeyraIntrinsicObserverEchoLab.summary exit schema=%s",
            result["schema"],
        )
        return result

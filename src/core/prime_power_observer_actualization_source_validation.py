"""Hostile-safe canonical source-envelope validation shared by P3-N0 APIs."""

from __future__ import annotations

import logging

from .padic_family_introduction_types import N1IntroductionPackage
from .prime_power_observer_actualization_common import (
    N0ValidationError, exact_hex, exact_int, exact_shape, exact_text, reject,
)
from .prime_power_observer_actualization_evidence_types import N0TheoremSource
from .prime_power_observer_actualization_nested_validation import bounded_text, exact_tuple
from .prime_power_observer_actualization_source_tree import validate_exact_source_tree
from .prime_power_observer_actualization_types import (
    DoctrineAdmission, N0FamilyFiniteBridgeSource, N0Ledger, N0Policy, N0Source,
    N2FPackage, PrimePowerObserverDoctrine, RhoObserverScope,
)

logger = logging.getLogger(__name__)


def _exact_children(raw) -> None:
    """Check every direct child type/container before any child dereference."""
    logger.debug("_exact_children entry")
    if (type(raw["doctrine"]) is not PrimePowerObserverDoctrine
            or type(raw["policy"]) is not N0Policy
            or type(raw["theorem_source"]) is not N0TheoremSource
            or type(raw["bridge"]) is not N0FamilyFiniteBridgeSource
            or type(raw["strict_package"]) is not N2FPackage
            or type(raw["open_package"]) is not N2FPackage
            or type(raw["scope"]) is not RhoObserverScope
            or type(raw["prebirth_ledger"]) is not N0Ledger
            or type(raw["postbirth_ledger"]) is not N0Ledger
            or type(raw["history_ledger"]) is not N0Ledger):
        reject("n0-source-child-envelope-invalid")
    packages = raw["n1_packages"]
    if (type(packages) is not tuple or len(packages) != 3
            or any(type(item) is not N1IntroductionPackage for item in packages)):
        reject("n0-source-n1-package-envelope-invalid")
    logger.debug("_exact_children exit")


def _validate_doctrine_policy(raw) -> bool:
    """Recompute direct doctrine/policy children after their exact types are known."""
    logger.debug("_validate_doctrine_policy entry")
    doctrine = exact_shape(raw["doctrine"], PrimePowerObserverDoctrine, "n0-source-doctrine")
    if type(doctrine["admission"]) is not DoctrineAdmission:
        reject("n0-source-doctrine-admission-invalid")
    for name in (
        "version", "principle_family_id", "principle_id", "prime_kind", "tower_kind",
        "family_domain_kind",
    ):
        bounded_text(doctrine[name], f"n0-source-doctrine-{name}", maximum=256)
    premises = exact_tuple(
        doctrine["premises"], "n0-source-doctrine-premises", maximum=32,
    )
    for index, item in enumerate(premises):
        bounded_text(item, f"n0-source-doctrine-premise-{index}", maximum=256)
    exact_hex(doctrine["doctrine_digest"], "n0-source-doctrine-digest")
    policy = exact_shape(raw["policy"], N0Policy, "n0-source-policy")
    cap_names = (
        "max_depth", "max_integer_bits", "max_exponent", "max_modulus_bits",
        "max_events", "max_parent_edges", "max_access_edges", "max_evaluations",
        "max_families", "max_finite_rows", "max_reductions", "max_assumptions",
        "max_ledger_bytes", "max_captured_bytes", "max_output_bytes", "timeout_seconds",
    )
    for name in cap_names:
        exact_int(policy[name], f"n0-source-policy-{name}", minimum=1, maximum=2**31)
    exact_hex(policy["policy_digest"], "n0-source-policy-digest")
    exact_text(policy["version"], "n0-source-policy-version", maximum=64)
    logger.debug("_validate_doctrine_policy exit")
    return doctrine["admission"] is DoctrineAdmission.ADMITTED


def validate_n0_source(source) -> N0Source:
    """Validate one exact canonical N0 source before any public nested access."""
    logger.debug("validate_n0_source entry type=%s", type(source).__name__)
    raw = exact_shape(source, N0Source, "n0-source")
    exact_int(raw["prime"], "n0-source-prime", minimum=2, maximum=65521)
    exact_int(raw["depth"], "n0-source-depth", maximum=64)
    exact_text(raw["lineage_id"], "n0-source-lineage")
    exact_hex(raw["source_digest"], "n0-source-digest")
    _exact_children(raw)
    admitted = _validate_doctrine_policy(raw)
    from .prime_power_observer_actualization_sources import exact_n0_source
    try:
        expected = exact_n0_source(
            raw["prime"], raw["depth"], raw["lineage_id"], policy=raw["policy"],
            admitted=admitted,
        )
        validate_exact_source_tree(source, expected)
        matches = source == expected
    except N0ValidationError:
        raise
    except Exception as exc:
        logger.exception("validate_n0_source foreign canonical rejection")
        reject(f"n0-source-canonical-rejected-{type(exc).__name__}")
    if not matches:
        reject("n0-source-drift")
    logger.debug("validate_n0_source exit")
    return source

"""Fresh exact validation for bounded P3-OG native-state closure evidence."""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from hmac import compare_digest
import logging

from .prime_power_observer_genesis_p3og_codec import evidence_bytes
from .prime_power_observer_genesis_p3og_native_closure_runtime import (
    _run_p3og_native_first_closure_validated,
)
from .prime_power_observer_genesis_p3og_native_closure_source import (
    validate_native_closure_source,
)
from .prime_power_observer_genesis_p3og_native_closure_types import (
    P3OGNativeClosureSource,
    P3OGNativeFirstClosureEvidence,
)
from .prime_power_observer_genesis_p3og_types import P3OGSource

logger = logging.getLogger(__name__)


def _require_exact_native_closure_shape(
    value: object,
    expected: object,
    depth: int = 0,
) -> None:
    """Reject foreign nested values before canonical byte comparison."""
    if depth > 24 or type(value) is not type(expected):
        raise ValueError("p3og-native-first-closure-evidence-shape")
    if type(expected) is tuple:
        if len(value) != len(expected):  # type: ignore[arg-type]
            raise ValueError("p3og-native-first-closure-evidence-shape")
        for actual_item, expected_item in zip(  # type: ignore[arg-type]
            value,
            expected,
            strict=True,
        ):
            _require_exact_native_closure_shape(
                actual_item,
                expected_item,
                depth + 1,
            )
    elif is_dataclass(expected) and not isinstance(expected, type):
        for field in fields(expected):
            _require_exact_native_closure_shape(
                getattr(value, field.name),
                getattr(expected, field.name),
                depth + 1,
            )


def validate_p3og_native_first_closure_evidence(
    source: P3OGSource,
    closure_source: P3OGNativeClosureSource,
    evidence: P3OGNativeFirstClosureEvidence,
) -> P3OGNativeFirstClosureEvidence:
    """Freshly replay closure pressure; grant no history or role authority."""
    source, closure_source = validate_native_closure_source(source, closure_source)
    if type(evidence) is not P3OGNativeFirstClosureEvidence:
        raise ValueError("p3og-native-first-closure-evidence-type")
    try:
        expected = _run_p3og_native_first_closure_validated(
            source,
            closure_source,
        )
        _require_exact_native_closure_shape(evidence, expected)
        equal = compare_digest(
            evidence_bytes(evidence),
            evidence_bytes(expected),
        )
    except (AttributeError, RecursionError, TypeError, UnicodeError, ValueError) as exc:
        raise ValueError("p3og-native-first-closure-evidence-malformed") from exc
    if not equal:
        raise ValueError("p3og-native-first-closure-evidence-drift")
    return expected

"""Non-root facade for P3-N2-derived P3-OG arithmetic input provenance."""

from .prime_power_observer_genesis_p3og_arithmetic_input_runtime import (
    p3og_arithmetic_input_source,
    validate_p3og_arithmetic_input_source,
)
from .prime_power_observer_genesis_p3og_arithmetic_input_types import (
    P3OGArithmeticInputSource,
    P3OG_ARITHMETIC_INPUT_NONCLAIMS,
)

__all__ = (
    "P3OGArithmeticInputSource",
    "P3OG_ARITHMETIC_INPUT_NONCLAIMS",
    "p3og_arithmetic_input_source",
    "validate_p3og_arithmetic_input_source",
)

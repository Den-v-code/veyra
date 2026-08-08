"""Isolated R12.4 intrinsic-carrier codec and structural runtime."""

from .codec import (
    INTRINSIC_PROFILE,
    IntrinsicCodecError,
    decode_intrinsic_frame,
    encode_intrinsic_frame,
)
from .runtime import (
    canonical_intrinsic_report_json,
    execute_intrinsic_ir,
    inspect_intrinsic_frame,
    intrinsic_error_data,
)

__all__ = [
    "INTRINSIC_PROFILE",
    "IntrinsicCodecError",
    "canonical_intrinsic_report_json",
    "decode_intrinsic_frame",
    "encode_intrinsic_frame",
    "execute_intrinsic_ir",
    "inspect_intrinsic_frame",
    "intrinsic_error_data",
]

"""Reviewed immutable manifest for the exact R7 Lean semantic TCB."""
from types import MappingProxyType

TCB_SCHEMA = "veyra-proof-tcb-v1"
EXPECTED_LEAN_BINARY_SHA256 = "3e0d0d3d801675359f2d4cf9815bfdb417b20b92fdd9d48b3b14c95bbae28bbf"
EXPECTED_LEAN_RUNTIME = (
    "990d68abe5bda161659d2a28ad9ba70f8739fdc30fb3655e3258df6bbc2f761a",
    2365,
    522231408,
)
EXPECTED_LEAN_OBJECTS = MappingProxyType({
    "arithmetic": (
        "VeyraNativeArithmetic.olean", 176856,
        "2ee38abbf195fcc2f0837366af98ca3047b1bc682691c049c3c9fe3eb44b1945",
    ),
    "kernel": (
        "VeyraProofKernel.olean", 2353728,
        "0b42aca8cab44c3bd40355379f95ff3845b3cc24ce9d24984e1be2721603c4c1",
    ),
    "soundness": (
        "VeyraProofSoundness.olean", 611240,
        "935ce61c4375afcb8a5c3275b1f17f34d5e83c24f6fc54b8324f29941dbb6e1a",
    ),
})
EXPECTED_TCB_DIGESTS = MappingProxyType({
    "arithmetic": "e85fa215ae8cba4901620f452efd008efb4787f3373154814d897d66a45373f3",
    "kernel": "a3a89c7aa52a978cbe3fb7aa5b5089963b7eff61c3ab3f95ff2d38e4cce2bd53",
    "soundness": "225056f1820899edcaebe1d7876f325fcf90903be29c823fede88c1dabb17f14",
})
MANIFEST_BOUNDARY = (
    "reviewed Python/Lean recurrence-rule parity manifest; source drift blocks "
    "until the semantic review and manifest are deliberately renewed"
)

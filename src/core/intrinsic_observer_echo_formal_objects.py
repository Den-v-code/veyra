"""Externally reviewed deterministic Lean object records for R13.2."""
from types import MappingProxyType

_EXPECTED_R13_OBJECT_ROWS = (
    ("lean_arithmetic", ("VeyraNativeArithmetic.olean", 176856, "2ee38abbf195fcc2f0837366af98ca3047b1bc682691c049c3c9fe3eb44b1945")),
    ("lean_semantics", ("VeyraNativeSemantics.olean", 767352, "e3ff6f807e2570e8b637e9fab76c786023339c6f24c6acf5866ba55b4337e505")),
    ("lean_intrinsic_runtime", ("VeyraIntrinsicRuntime.olean", 81928, "49230a22143b1eec485f2f97e788608fdc833a963493ab369e62fdad359b30cf")),
    ("lean_kernel", ("VeyraProofKernel.olean", 2353728, "0b42aca8cab44c3bd40355379f95ff3845b3cc24ce9d24984e1be2721603c4c1")),
    ("lean_soundness", ("VeyraProofSoundness.olean", 611240, "935ce61c4375afcb8a5c3275b1f17f34d5e83c24f6fc54b8324f29941dbb6e1a")),
    ("lean_transport", ("VeyraRecurrenceModeBridge.olean", 261136, "b2b616349e095f2b436fbf9fbaee561fb39f618ff4e51693f23fd1093b2e201f")),
    ("lean_observer_core", ("VeyraObserverCore.olean", 1582528, "aee3e69a1ba2a1b580efd3da0a2483a8eee132b29e3cc06227714bdf1b6ea0b9")),
    ("lean_observer_proof", ("VeyraObserverProof.olean", 171064, "3e93f940cbf342f8bef8e70af967379020f8b157f8dd3fc66b608de9be4b6055")),
    ("lean_intrinsic_vam", ("VeyraIntrinsicVamBridge.olean", 1912864, "dd997757c3dedfb02abfd9c7341186bac107646fb9a5a5c2b6f4b664250e0df0")),
    ("lean_intrinsic_observer_echo", ("VeyraIntrinsicObserverEcho.olean", 329656, "f4a30bd94393ff456e2c70fc65e8ff0e46a24ef6ed8b74d453d6d00574a0aa08")),
)
EXPECTED_R13_OBJECTS = MappingProxyType(dict(_EXPECTED_R13_OBJECT_ROWS))

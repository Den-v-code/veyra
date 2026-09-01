"""Fail-fast reviewed-envelope regression for the R13 formal bridge."""
from dataclasses import replace

import src.core.intrinsic_observer_echo_formal_bridge as bridge
from src.core.intrinsic_observer_echo_effects import EXPECTED_REGISTRY_DIGEST
from src.core.intrinsic_observer_echo_evidence import EXPECTED_EVIDENCE_DIGEST
from src.core.intrinsic_observer_echo_formal_bridge_core import _CHECKED_DIAGNOSTICS
from src.core.intrinsic_observer_echo_formal_lean_render import THEOREM_IDS
from src.core.intrinsic_observer_echo_formal_manifest import (
    BRIDGE_ID,
    EXPECTED_BINDING_DIGEST,
    EXPECTED_PHASE_ARTIFACT,
    EXPECTED_R11_BINDING,
    EXPECTED_R12_BINDING,
    EXPECTED_R13_TCB_DIGESTS,
    EXPECTED_SNAPSHOT_DIGEST,
    EXPECTED_SOURCE_ELABORATION_BINDING,
    EXPECTED_TOOLCHAIN_IDENTITY,
    MANIFEST_BOUNDARY,
)
from src.core.intrinsic_observer_echo_formal_objects import EXPECTED_R13_OBJECTS
from src.core.intrinsic_observer_echo_formal_report import IntrinsicObserverEchoFormalBridgeReport
from src.core.shadow_effect_types import BridgeCapability, EvidenceClass, EvidenceScope


def _reviewed_report(effect_digest: str) -> IntrinsicObserverEchoFormalBridgeReport:
    return IntrinsicObserverEchoFormalBridgeReport(
        "checked",
        BRIDGE_ID,
        THEOREM_IDS,
        EXPECTED_PHASE_ARTIFACT,
        EXPECTED_SOURCE_ELABORATION_BINDING,
        EXPECTED_R11_BINDING,
        EXPECTED_R12_BINDING,
        EXPECTED_EVIDENCE_DIGEST,
        EXPECTED_REGISTRY_DIGEST,
        effect_digest,
        tuple(EXPECTED_R13_TCB_DIGESTS.items()),
        tuple(EXPECTED_R13_OBJECTS.items()),
        EXPECTED_SNAPSHOT_DIGEST,
        BridgeCapability.PRESERVES,
        EvidenceClass.FORMAL_BRIDGE,
        EvidenceScope.GENERAL,
        EXPECTED_BINDING_DIGEST,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        False,
        False,
        EXPECTED_TOOLCHAIN_IDENTITY,
        _CHECKED_DIAGNOSTICS,
        MANIFEST_BOUNDARY,
    )


def test_forged_executable_evidence_digest_rejects_before_origins(monkeypatch):
    calls = 0
    effect_digest = "e" * 64

    def forbidden_origins():
        nonlocal calls
        calls += 1
        raise AssertionError("expensive origins replay must not run")

    monkeypatch.setattr(bridge, "_origins", forbidden_origins)
    monkeypatch.setattr(bridge, "shadow_effect_registry_digest", lambda: EXPECTED_REGISTRY_DIGEST)
    monkeypatch.setattr(bridge, "intrinsic_observer_echo_effect_digest", lambda: effect_digest)
    forged = replace(
        _reviewed_report(effect_digest),
        executable_evidence_digest="0" * 64,
    )

    assert not bridge._matches_reviewed_envelope(forged)
    assert not bridge.verify_intrinsic_observer_echo_formal_bridge_report(forged)
    assert calls == 0

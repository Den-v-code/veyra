from src.core.essence import (
    VeyraEssenceReport,
    core_layers,
    essence_axioms,
    essence_checklist,
    essence_report,
)


def test_essence_axioms_are_declared_and_witnessed():
    axioms = essence_axioms()
    assert len(axioms) == 9
    assert axioms[0].name == "no-primitive-equality"
    assert all(item.status == "declared" and item.witness for item in axioms)
    assert {item.name for item in axioms} >= {"no-primitive-number", "coverage-discipline"}


def test_core_layers_are_ready_and_certificate_anchored():
    layers = core_layers()
    assert len(layers) == 36
    assert all(item.status == "ready" and item.certificate for item in layers)
    assert {item.name for item in layers} >= {"echo", "intrinsic-observer-echo", "native-number", "compression-algebra", "language", "diagnostics", "proof-discipline", "transcendental-limit", "convergence-algebra", "real-analysis-structure", "phase-equations", "statistics-concentration", "weighted-echo-measure", "science-domain-certificates", "model-diagnostics", "scale-memory-log", "native-runtime", "classical-benchmark", "native-number-theorem", "deduction-chain"}


def test_essence_report_marks_core_ready():
    report = essence_report()
    assert report.core_ready
    assert report.missing == ()
    assert report.summary() == {
        "axioms": 9,
        "layers": 36,
        "executable_layers": 36,
        "missing": 0,
        "checklist": 6,
        "core_ready": True,
        "execution_ready": True,
        "proof_complete": False,
        "theorem_derived": 2,
        "witness_only": 4,
        "shadow": 25,
        "meta": 5,
    }


def test_essence_report_does_not_eagerly_replay_expensive_summary(monkeypatch):
    calls = 0

    def counted_summary(self):
        nonlocal calls
        calls += 1
        return {"layers": len(self.layers)}

    monkeypatch.setattr(VeyraEssenceReport, "summary", counted_summary)
    report = essence_report()
    assert calls == 0
    assert len(report.layers) == 36


def test_essence_checklist_names_shadow_and_negative_pressure():
    text = "\n".join(essence_checklist())
    assert "shadows" in text
    assert "negative pressure" in text
    assert "Sage facade" in text

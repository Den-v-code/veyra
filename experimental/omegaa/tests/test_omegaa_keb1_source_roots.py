"""Non-self-referential exact six-file KEB1 source root."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from src.core.omegaa_keb1_codec import KEB1_SOURCE_PATHS_V1, keb1_source_root_v1

ROOT = Path(__file__).parents[1]
KPT1_SOURCE_ROOT = bytes.fromhex("55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a")
KEB1_CANDIDATE_SOURCE_ROOT = "cc6b3be5b10ec2915897694da46cbeab22eff7f626270d6a14615ca8478f0e4b"


def _frame(value: bytes) -> bytes:
    return len(value).to_bytes(8, "big") + value


def _manifest(paths: tuple[str, ...]) -> bytes:
    if set(paths) != set(KEB1_SOURCE_PATHS_V1) or paths != tuple(sorted(paths)) or len(paths) != len(set(paths)):
        raise ValueError("manifest path-set mismatch")
    chunks = []
    for name in paths:
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("manifest path integrity")
        chunks.append(_frame(name.encode()) + _frame(path.read_bytes()))
    return len(paths).to_bytes(8, "big") + b"".join(chunks)


def test_exact_six_file_root_reproduces() -> None:
    manifest = _manifest(KEB1_SOURCE_PATHS_V1)
    candidate = sha256(_frame(b"omegaa.keb1-source.v1") + _frame(KPT1_SOURCE_ROOT) + _frame(manifest)).digest()
    assert len(KEB1_SOURCE_PATHS_V1) == 6
    assert candidate.hex() == KEB1_CANDIDATE_SOURCE_ROOT
    assert keb1_source_root_v1() == candidate
    assert KEB1_CANDIDATE_SOURCE_ROOT.encode() not in manifest


def test_manifest_paths_are_exact_and_no_future_authority_dependency() -> None:
    assert KEB1_SOURCE_PATHS_V1 == tuple(sorted(KEB1_SOURCE_PATHS_V1))
    source = b"".join((ROOT / name).read_bytes() for name in KEB1_SOURCE_PATHS_V1)
    for forbidden in (b"omegaa_kci", b"omegaa_kie", b"omegaa_kcs", b"omegaa_kpa", b"omegaa_kqe", b"aggregate-checker-source"):
        assert forbidden not in source


def test_source_root_hash_and_os_drift_are_zero_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.core.omegaa_keb1_codec as codec_module

    called = 0

    def hostile(*_args: object, **_kwargs: object) -> object:
        nonlocal called
        called += 1
        raise AssertionError("must not run")

    monkeypatch.setattr(codec_module, "sha256", hostile)
    with pytest.raises(ValueError, match="codec-integrity"):
        codec_module.keb1_source_root_v1()
    assert called == 0
    monkeypatch.undo()
    monkeypatch.setattr(codec_module.os, "open", hostile)
    with pytest.raises(ValueError, match="codec-integrity"):
        codec_module.keb1_source_root_v1()
    assert called == 0


@pytest.mark.parametrize("paths", (KEB1_SOURCE_PATHS_V1[:-1], KEB1_SOURCE_PATHS_V1 + (KEB1_SOURCE_PATHS_V1[0],)))
def test_reference_manifest_refuses_missing_or_duplicate(paths: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="path-set mismatch"):
        _manifest(paths)

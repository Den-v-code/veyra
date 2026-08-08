from __future__ import annotations

from pathlib import Path

import pytest

from src.core import omegaa_kcs1_codec as codec


def test_source_root_is_stable_bytes32_and_exact_five_file_manifest() -> None:
    assert codec.KCS1_SOURCE_PATHS_V1 == tuple(sorted(codec.KCS1_SOURCE_PATHS_V1))
    assert len(codec.KCS1_SOURCE_PATHS_V1) == len(set(codec.KCS1_SOURCE_PATHS_V1)) == 5
    assert all(Path(name).is_file() for name in codec.KCS1_SOURCE_PATHS_V1)
    first = codec.kcs1_source_root_v1()
    second = codec.kcs1_source_root_v1()
    assert type(first) is bytes and len(first) == 32 and first == second


@pytest.mark.parametrize(
    "paths",
    (
        tuple(reversed(codec.KCS1_SOURCE_PATHS_V1)),
        codec.KCS1_SOURCE_PATHS_V1[:-1],
        ("/absolute",) + codec.KCS1_SOURCE_PATHS_V1[1:],
        (codec.KCS1_SOURCE_PATHS_V1[0],) * 5,
    ),
)
def test_manifest_rejects_reorder_missing_absolute_and_duplicates(
    monkeypatch: pytest.MonkeyPatch, paths: tuple[str, ...]
) -> None:
    monkeypatch.setattr(codec, "KCS1_SOURCE_PATHS_V1", paths)
    with pytest.raises(ValueError):
        codec.kcs1_source_root_v1()


def test_source_root_rejects_root_and_prerequisite_function_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(codec, "_ROOT", Path("/"))
    with pytest.raises(ValueError):
        codec.kcs1_source_root_v1()
    monkeypatch.undo()
    monkeypatch.setattr(codec, "kci1_source_root_v1", lambda: b"x" * 32)
    with pytest.raises(ValueError):
        codec.kcs1_source_root_v1()


def test_source_identity_has_no_future_or_authority_edge() -> None:
    source = Path(codec.__file__).read_text()
    assert "omegaa_kie1" not in source
    assert "omegaa_kis1" not in source
    assert "authority" not in source.lower()

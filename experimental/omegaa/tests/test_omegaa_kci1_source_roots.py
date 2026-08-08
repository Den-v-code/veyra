"""Independent KCI1 five-file raw manifest and no-follow source-root tests."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

import src.core.omegaa_kci1_codec as codec_module
from src.core.omegaa_kci1_codec import KCI1_SOURCE_PATHS_V1, kci1_source_root_v1
from src.core.omegaa_kci1_common import KCI1IntegrityError

ROOT = Path(__file__).parents[1]
PATHS = (
    "src/core/omegaa_kci1_builder.py",
    "src/core/omegaa_kci1_codec.py",
    "src/core/omegaa_kci1_common.py",
    "src/core/omegaa_kci1_parser.py",
    "src/core/omegaa_kci1_types.py",
)
SOURCE_ROOT_HEX = "55f19f524bbb9010ac399c5f2caf3d4513b7e81cd9f9e962b19be13fff05f6c0"


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _frame(value: bytes) -> bytes:
    return _u64(len(value)) + value


def _manifest(root: Path = ROOT) -> bytes:
    return _u64(len(PATHS)) + b"".join(
        _frame(name.encode("utf-8", errors="strict")) + _frame((root / name).read_bytes())
        for name in PATHS
    )


def _root_v1(label: str, fields: tuple[bytes, ...]) -> bytes:
    return sha256(
        _frame(label.encode("utf-8")) + b"".join(_frame(field) for field in fields)
    ).digest()


def test_exact_five_file_manifest_only_root_reproduces() -> None:
    manifest = _manifest()
    source_root = _root_v1("omegaa.kci1-source.v1", (manifest,))
    assert KCI1_SOURCE_PATHS_V1 == PATHS == tuple(sorted(PATHS))
    assert kci1_source_root_v1() == source_root
    assert source_root.hex() == SOURCE_ROOT_HEX
    assert source_root.hex().encode() not in manifest


def test_root_has_no_prerequisite_or_authority_edge() -> None:
    source = b"".join((ROOT / name).read_bytes() for name in PATHS).lower()
    for forbidden in (
        b"omegaa_kpt",
        b"omegaa_kcc",
        b"omegaa_kca",
        b"omegaa_kcf",
        b"omegaa_keb",
        b"omegaa_kie",
        b"registry",
        b"admission",
    ):
        assert forbidden not in source
    manifest = _manifest()
    source_root = _root_v1("omegaa.kci1-source.v1", (manifest,))
    assert _root_v1("omegaa.kci1-source.v1", (bytes(32), manifest)) != source_root


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "paths",
    (
        PATHS[:-1],
        PATHS + (PATHS[0],),
        PATHS + ("src/core/extra.py",),
        tuple(reversed(PATHS)),
        ("/" + PATHS[0],) + PATHS[1:],
        ("src/core/../core/omegaa_kci1_builder.py",) + PATHS[1:],
    ),
)
def test_manifest_refuses_nonexact_path_sets_and_forms(paths: tuple[str, ...]) -> None:
    with pytest.raises(KCI1IntegrityError, match="closed-input"):
        codec_module._source_manifest_v1(paths, ROOT)


def _copy_manifest_tree(target: Path) -> None:
    for name in PATHS:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / name).read_bytes())


def test_manifest_refuses_leaf_symlink_and_non_file(tmp_path: Path) -> None:
    _copy_manifest_tree(tmp_path)
    first = tmp_path / PATHS[0]
    first.unlink()
    first.symlink_to(tmp_path / PATHS[1])
    with pytest.raises(KCI1IntegrityError, match="path-integrity"):
        codec_module._source_manifest_v1(PATHS, tmp_path)
    first.unlink()
    first.mkdir()
    with pytest.raises(KCI1IntegrityError, match="path-integrity"):
        codec_module._source_manifest_v1(PATHS, tmp_path)


def test_manifest_refuses_symlinked_ancestor(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    outside = tmp_path / "outside"
    _copy_manifest_tree(outside)
    repository.mkdir()
    (repository / "src").symlink_to(outside / "src", target_is_directory=True)
    with pytest.raises(KCI1IntegrityError, match="path-integrity"):
        codec_module._source_manifest_v1(PATHS, repository)


def test_manifest_refuses_symlink_as_absolute_repository_root(tmp_path: Path) -> None:
    real_repository = tmp_path / "real" / "repository"
    _copy_manifest_tree(real_repository)
    linked_repository = tmp_path / "linked-repository"
    linked_repository.symlink_to(real_repository, target_is_directory=True)
    with pytest.raises(KCI1IntegrityError, match="root-integrity"):
        codec_module._source_manifest_v1(PATHS, linked_repository)

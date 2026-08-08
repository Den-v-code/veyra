"""Independent manifest-only source-root and config-ID pins for KCC1."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

import src.core.omegaa_kcc1_codec as codec_module
from src.core.omegaa_kcc1_codec import (
    KCC1_SOURCE_PATHS_V1,
    kcc1_empty_config_id_v1,
    kcc1_source_root_v1,
)
from src.core.omegaa_kcc1_common import KCC1IntegrityError

ROOT = Path(__file__).parents[1]
WIRE = bytes.fromhex("4b4343310000")
PATHS = (
    "src/core/omegaa_kcc1_builder.py",
    "src/core/omegaa_kcc1_codec.py",
    "src/core/omegaa_kcc1_common.py",
    "src/core/omegaa_kcc1_parser.py",
    "src/core/omegaa_kcc1_types.py",
)
SOURCE_ROOT_HEX = "7f2000a380447f5107a380361e9f822760b1b9416f3dbdcc9bfc23c796cd974a"
CONFIG_ID_HEX = "3782a57969dafa79cee5141036a9878d936aa951b3f851350eb52fb4ac235006"


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
    return sha256(_frame(label.encode("utf-8")) + b"".join(_frame(field) for field in fields)).digest()


def test_exact_five_file_manifest_only_root_and_config_id_reproduce() -> None:
    manifest = _manifest()
    source_root = _root_v1("omegaa.kcc1-empty-source.v1", (manifest,))
    config_id = _root_v1("omegaa.kcc1-empty-config.v1", (source_root, WIRE))
    assert KCC1_SOURCE_PATHS_V1 == PATHS == tuple(sorted(PATHS))
    assert kcc1_source_root_v1() == source_root
    assert kcc1_empty_config_id_v1() == config_id
    assert source_root.hex() == SOURCE_ROOT_HEX
    assert config_id.hex() == CONFIG_ID_HEX
    assert source_root.hex().encode() not in manifest


def test_root_has_no_prerequisite_or_semantic_authority_edge() -> None:
    source = b"".join((ROOT / name).read_bytes() for name in PATHS).lower()
    for forbidden in (b"omegaa_kpt", b"kci1", b"keb1", b"kie1", b"registry", b"admission"):
        assert forbidden not in source
    manifest = _manifest()
    source_root = _root_v1("omegaa.kcc1-empty-source.v1", (manifest,))
    assert _root_v1("omegaa.kcc1-empty-source.v1", (bytes(32), manifest)) != source_root


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "paths",
    (
        PATHS[:-1],
        PATHS + (PATHS[0],),
        PATHS + ("src/core/extra.py",),
        tuple(reversed(PATHS)),
        ("/" + PATHS[0],) + PATHS[1:],
        ("src/core/../core/omegaa_kcc1_builder.py",) + PATHS[1:],
    ),
)
def test_manifest_refuses_nonexact_path_sets_and_forms(paths: tuple[str, ...]) -> None:
    with pytest.raises(KCC1IntegrityError, match="closed-input"):
        codec_module._source_manifest_v1(paths, ROOT)


def _copy_manifest_tree(target: Path) -> None:
    for name in PATHS:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / name).read_bytes())


def test_manifest_refuses_symlink_and_non_file(tmp_path: Path) -> None:
    _copy_manifest_tree(tmp_path)
    first = tmp_path / PATHS[0]
    first.unlink()
    first.symlink_to(tmp_path / PATHS[1])
    with pytest.raises(KCC1IntegrityError, match="path-integrity"):
        codec_module._source_manifest_v1(PATHS, tmp_path)
    first.unlink()
    first.mkdir()
    with pytest.raises(KCC1IntegrityError, match="path-integrity"):
        codec_module._source_manifest_v1(PATHS, tmp_path)

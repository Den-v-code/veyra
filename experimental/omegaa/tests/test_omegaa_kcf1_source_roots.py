"""Non-self-referential RootV1 pins for accepted KPT/KCA and candidate KCF."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
KPT1_PATHS = (
    "src/core/omegaa_kpt1_builder.py", "src/core/omegaa_kpt1_codec.py",
    "src/core/omegaa_kpt1_common.py", "src/core/omegaa_kpt1_parser.py",
    "src/core/omegaa_kpt1_parser_tasks.py", "src/core/omegaa_kpt1_types.py",
)
KCA1_PATHS = (
    "src/core/omegaa_kca1_codec.py", "src/core/omegaa_kca1_common.py",
    "src/core/omegaa_kca1_parser.py", "src/core/omegaa_kca1_types.py",
)
KCF1_PATHS = (
    "src/core/omegaa_kcf1_builder.py", "src/core/omegaa_kcf1_codec.py",
    "src/core/omegaa_kcf1_common.py", "src/core/omegaa_kcf1_parser.py",
    "src/core/omegaa_kcf1_types.py",
)
KPT1_SOURCE_ROOT = "55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a"
KCA1_SLICE_A_SOURCE_ROOT = "e98c6e880727148d05c4d061192f842a71d77a28d65a704cfc7fa63194cc301c"
KCF1_CANDIDATE_SOURCE_ROOT = "95d24a28eb0a3a0f09ed7e8621d0e27b83de87e25efeb1aa641bbeb345ce22bf"


def _u64(value: int) -> bytes:
    return value.to_bytes(8, "big")


def _frame(value: bytes) -> bytes:
    return _u64(len(value)) + value


def _manifest(paths: tuple[str, ...], closed: tuple[str, ...]) -> bytes:
    if len(paths) != len(set(paths)) or set(paths) != set(closed):
        raise ValueError("manifest path-set mismatch")
    ordered = sorted(paths)
    chunks: list[bytes] = []
    for name in ordered:
        encoded = name.encode("utf-8", errors="strict")
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("manifest path integrity")
        chunks.append(_frame(encoded) + _frame(path.read_bytes()))
    return _u64(len(ordered)) + b"".join(chunks)


def _root_v1(label: str, fields: tuple[bytes, ...]) -> bytes:
    payload = _frame(label.encode("utf-8")) + b"".join(_frame(field) for field in fields)
    return sha256(payload).digest()


def test_exact_six_four_five_leaf_roots_reproduce_without_self_reference() -> None:
    kpt_manifest = _manifest(KPT1_PATHS, KPT1_PATHS)
    kca_manifest = _manifest(KCA1_PATHS, KCA1_PATHS)
    kcf_manifest = _manifest(KCF1_PATHS, KCF1_PATHS)
    kpt = _root_v1("omegaa.kpt1-source.v1", (kpt_manifest,))
    kca = _root_v1("omegaa.kca1-slice-a-source.v1", (kca_manifest,))
    kcf = _root_v1("omegaa.kcf1-source.v1", (kpt, kca, kcf_manifest))
    assert (len(KPT1_PATHS), len(KCA1_PATHS), len(KCF1_PATHS)) == (6, 4, 5)
    assert kpt.hex() == KPT1_SOURCE_ROOT
    assert kca.hex() == KCA1_SLICE_A_SOURCE_ROOT
    assert kcf.hex() == KCF1_CANDIDATE_SOURCE_ROOT
    assert KCF1_CANDIDATE_SOURCE_ROOT not in kcf_manifest.decode("utf-8", errors="ignore")


def test_leaf_roots_have_no_kcf_or_future_aggregate_authority_edge() -> None:
    upstream = b"".join((ROOT / name).read_bytes() for name in KPT1_PATHS + KCA1_PATHS)
    assert b"KCF1_SOURCE_ROOT" not in upstream
    assert KCF1_CANDIDATE_SOURCE_ROOT.encode() not in upstream
    assert b"omegaa.kcf1-source.v1" not in upstream
    assert b"aggregate-checker-source" not in upstream


def test_kcf_uses_only_exact_kernel_type_id_label() -> None:
    source = b"".join((ROOT / name).read_bytes() for name in KCF1_PATHS)
    assert b'"kernel_type_id"' in source
    assert b'"type_id"' not in source


@pytest.mark.parametrize(
    "paths", (KCF1_PATHS[:-1], KCF1_PATHS + (KCF1_PATHS[0],), KCF1_PATHS + ("missing.py",)),
)
def test_manifest_refuses_missing_duplicate_or_extra_paths(paths: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="path-set mismatch"):
        _manifest(paths, KCF1_PATHS)


def test_candidate_root_requires_both_raw_prerequisite_digests() -> None:
    manifest = _manifest(KCF1_PATHS, KCF1_PATHS)
    kpt = bytes.fromhex(KPT1_SOURCE_ROOT)
    kca = bytes.fromhex(KCA1_SLICE_A_SOURCE_ROOT)
    candidate = bytes.fromhex(KCF1_CANDIDATE_SOURCE_ROOT)
    assert _root_v1("omegaa.kcf1-source.v1", (manifest,)) != candidate
    assert _root_v1("omegaa.kcf1-source.v1", (kca, kpt, manifest)) != candidate

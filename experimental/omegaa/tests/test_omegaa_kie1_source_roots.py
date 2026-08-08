"""Independent KIE1 five-file source manifest, prerequisite, and no-follow tests."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Callable

import pytest

import src.core.omegaa_kie1_common as common_module
from src.core.omegaa_kci1_codec import kci1_source_root_v1
from src.core.omegaa_keb1_codec import keb1_source_root_v1
from src.core.omegaa_kie1_common import (
    KIE1_SOURCE_PATHS_V1,
    KIE1IntegrityErrorV1,
    kie1_source_root_v1,
)

ROOT = Path(__file__).parents[1]
PATHS = (
    "src/core/omegaa_kie1_binding.py",
    "src/core/omegaa_kie1_common.py",
    "src/core/omegaa_kie1_offsets.py",
    "src/core/omegaa_kie1_prepare.py",
    "src/core/omegaa_kie1_types.py",
)
KPT1_SOURCE_ROOT = bytes.fromhex(
    "55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a"
)


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
        _frame(label.encode("utf-8", errors="strict"))
        + b"".join(_frame(field) for field in fields)
    ).digest()


def test_exact_dependency_order_and_five_file_root_reproduce() -> None:
    manifest = _manifest()
    fields = (KPT1_SOURCE_ROOT, kci1_source_root_v1(), keb1_source_root_v1(), manifest)
    expected = _root_v1("omegaa.kie1-source.v1", fields)
    assert KIE1_SOURCE_PATHS_V1 == PATHS == tuple(sorted(PATHS))
    assert kie1_source_root_v1() == expected
    assert len(expected) == 32
    for prerequisite in fields[:3]:
        assert manifest.count(prerequisite) == 0
    assert expected not in manifest


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "paths",
    (
        PATHS[:-1],
        PATHS + (PATHS[0],),
        PATHS + ("src/core/extra.py",),
        tuple(reversed(PATHS)),
        ("/" + PATHS[0],) + PATHS[1:],
        ("src/core/../core/omegaa_kie1_binding.py",) + PATHS[1:],
    ),
)
def test_manifest_refuses_nonexact_sets_and_lexical_forms(paths: tuple[str, ...]) -> None:
    with pytest.raises(KIE1IntegrityErrorV1, match="closed-input"):
        common_module._source_manifest_v1(paths, ROOT)


def _copy_tree(target: Path) -> None:
    for name in PATHS:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / name).read_bytes())


def test_componentwise_reader_rejects_leaf_symlink_and_nonregular(tmp_path: Path) -> None:
    _copy_tree(tmp_path)
    leaf = tmp_path / PATHS[0]
    leaf.unlink()
    leaf.symlink_to(tmp_path / PATHS[1])
    with pytest.raises(KIE1IntegrityErrorV1, match="path-integrity"):
        common_module._read_source_file_v1(tmp_path, PATHS[0])
    leaf.unlink()
    leaf.mkdir()
    with pytest.raises(KIE1IntegrityErrorV1, match="path-integrity"):
        common_module._read_source_file_v1(tmp_path, PATHS[0])


def test_componentwise_reader_rejects_symlinked_ancestor(tmp_path: Path) -> None:
    real = tmp_path / "real"
    _copy_tree(real)
    linked = tmp_path / "linked"
    linked.mkdir()
    (linked / "src").symlink_to(real / "src", target_is_directory=True)
    with pytest.raises(KIE1IntegrityErrorV1, match="path-integrity"):
        common_module._read_source_file_v1(linked, PATHS[0])


def test_componentwise_reader_rejects_symlinked_absolute_root(tmp_path: Path) -> None:
    real = tmp_path / "real"
    _copy_tree(real)
    linked = tmp_path / "linked-root"
    linked.symlink_to(real, target_is_directory=True)
    with pytest.raises(KIE1IntegrityErrorV1, match="root-integrity"):
        common_module._read_source_file_v1(linked, PATHS[0])


def test_linux_open_flags_are_exact_captured_values() -> None:
    assert common_module._O_RDONLY_FROZEN == 0
    assert common_module._O_CLOEXEC_FROZEN == 524_288
    assert common_module._O_NOFOLLOW_FROZEN == 131_072
    assert common_module._O_DIRECTORY_FROZEN == 65_536
    assert common_module._FILE_FLAGS_FROZEN == 655_360
    assert common_module._DIRECTORY_FLAGS_FROZEN == 720_896


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "name",
    ("_O_RDONLY_FROZEN", "_O_CLOEXEC_FROZEN", "_O_NOFOLLOW_FROZEN", "_O_DIRECTORY_FROZEN"),
)
def test_linux_open_flag_drift_refuses_before_source_read(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.setattr(common_module, name, -1)
    with pytest.raises(KIE1IntegrityErrorV1, match="source-runtime-integrity"):
        common_module._read_source_file_v1(ROOT, PATHS[0])


def test_close_failure_is_sanitized_as_kie_integrity() -> None:
    with pytest.raises(KIE1IntegrityErrorV1, match="close-fd-integrity"):
        common_module._close_fd_v1(2**31 - 1)


class _Bomb:
    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, *_args: object, **_kwargs: object) -> object:
        self.calls += 1
        raise AssertionError("hostile callback executed")


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("name", "operation"),
    (
        ("_FRAME", common_module.kie1_source_root_v1),
        ("_CHECKED_U64", lambda: common_module._u64_bytes_v1(0)),
    ),
)
def test_source_helper_alias_drift_refuses_with_zero_callbacks(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    operation: Callable[[], object],
) -> None:
    bomb = _Bomb()
    monkeypatch.setattr(common_module, name, bomb)
    with pytest.raises(KIE1IntegrityErrorV1):
        operation()
    assert bomb.calls == 0


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    "name", ("_SOURCE_MANIFEST", "_KCI_ROOT", "_KEB_ROOT"),
)
def test_source_root_alias_drift_is_zero_callback(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    bomb = _Bomb()
    monkeypatch.setattr(common_module, name, bomb)
    with pytest.raises(KIE1IntegrityErrorV1):
        kie1_source_root_v1()
    assert bomb.calls == 0


def test_dag_forbids_kcc_kcs_kis_semantics_authority_and_registry_edges() -> None:
    source = b"".join((ROOT / name).read_bytes() for name in PATHS).lower()
    for forbidden in (
        b"omegaa_kcc",
        b"omegaa_kcs",
        b"omegaa_kis",
        b"omegaa_kec",
        b"omegaa_kqe",
        b"checker_success",
        b"registry",
        b"admission",
        b"authority_token",
    ):
        assert forbidden not in source

"""Fail-closed Python/Lean binding for the canonical R7 proof artifact."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import logging
import os
import re
import stat
import subprocess
from tempfile import TemporaryDirectory

from .proof_core_codec import canonical_json
from .proof_core_lean_render import render_resonance_lean
from .proof_core_manifest import (
    EXPECTED_LEAN_BINARY_SHA256, EXPECTED_LEAN_OBJECTS,
    EXPECTED_LEAN_RUNTIME, EXPECTED_TCB_DIGESTS, TCB_SCHEMA,
)
from .proof_core_snapshot import LeanSourceSnapshot, materialize_lean_snapshot
from .proof_core_resonance import (
    IntrinsicResonanceTheorem, intrinsic_resonance_theorem,
    verify_intrinsic_theorem_binding,
)
from .proof_elaboration_runtime_guard import ProtectedClosure, guarded_lean_run
from .proof_elaboration_toolchain import (
    LEAN_BINARY, TOOLCHAIN_ROOT, default_runtime_absences,
    lean_runtime_digest, paths_digest, records_digest,
)
from .platform_posix import user_home

from .paths import PROJECT_ROOT

logger = logging.getLogger(__name__)
LEAN_DIR = PROJECT_ROOT / "proofs" / "lean"
BUILD_DIR = PROJECT_ROOT / "data" / "tmp" / "r7-lean"
LEAN_TOOLCHAIN = "leanprover/lean4:v4.30.0-rc2"
LEAN_VERSION = "4.30.0-rc2"
THEOREM_IDS = tuple(f"THM-R7-{index:03d}" for index in range(1, 5))
PLACEHOLDER = re.compile(r"\b(?:sorryAx|sorry|admit|axiom|unsafe)\b")
CHECKED_DIAGNOSTICS = ";".join(
    f"{index}/4:{name}:rc=0" for index, name in enumerate(
        ("VeyraNativeArithmetic", "VeyraProofKernel", "VeyraProofSoundness", "VeyraProofResonance"), 1,
    )
)
CHECKED_BOUNDARY = (
    "exact reviewed Python/Lean recurrence calculus and intrinsic reflexivity only; "
    "Lean userspace runtime/source/object continuity is mutation-guarded; OS loader, "
    "kernel, ptrace, and root compromise remain outside this TCB; no cyclic/phase bridge"
)
R7_GUARDED_DOMAIN = b"veyra-r7-guarded-input-v1\0"


@dataclass(frozen=True)
class ProofCoreBridgeReport:
    """Integrity, reviewed-manifest, and Lean-check report for one binding."""

    status: str
    theorem_ids: tuple[str, ...]
    artifact_digest: str
    kernel_digest: str
    soundness_digest: str
    export_digest: str
    binding_digest: str
    artifact_checked: bool
    source_bound: bool
    manifest_checked: bool
    lean_checked: bool
    toolchain: str
    diagnostics: str
    boundary: str


def _sha(data: bytes) -> str:
    logger.debug("proof_core_bridge._sha entry bytes=%d", len(data))
    result = sha256(data).hexdigest()
    logger.debug("proof_core_bridge._sha exit result=%s", result)
    return result


def _read(path: Path) -> bytes:
    logger.debug("proof_core_bridge._read entry path=%s", path)
    try:
        result = path.read_bytes()
    except OSError as exc:
        logger.error("proof_core_bridge._read error path=%s error=%s", path, exc)
        raise ValueError(f"proof-source-unreadable:{path.name}") from exc
    logger.debug("proof_core_bridge._read exit bytes=%d", len(result))
    return result


def _runtime_identity() -> str:
    logger.debug("proof_core_bridge._runtime_identity entry")
    actual = lean_runtime_digest()
    if actual != EXPECTED_LEAN_RUNTIME:
        raise ValueError("pinned-lean-runtime-closure-mismatch")
    result = f"merkle={actual[0]}|files={actual[1]}|bytes={actual[2]}"
    logger.debug("proof_core_bridge._runtime_identity exit result=%s", result)
    return result


def _clean_env(lean_paths: tuple[Path, ...] = ()) -> dict[str, str]:
    result = {
        "HOME": str(user_home()),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    if lean_paths:
        result["LEAN_PATH"] = os.pathsep.join(map(str, lean_paths))
    return result


def _runtime_absences() -> tuple[Path, ...]:
    filenames = tuple(row[0] for row in EXPECTED_LEAN_OBJECTS.values())
    return default_runtime_absences(filenames)


def _lean_command() -> list[str]:
    logger.debug("proof_core_bridge._lean_command entry")
    try:
        metadata = LEAN_BINARY.lstat()
        lean_bytes = LEAN_BINARY.read_bytes()
        valid = (
            stat.S_ISREG(metadata.st_mode)
            and metadata.st_nlink == 1
            and _sha(lean_bytes) == EXPECTED_LEAN_BINARY_SHA256
            and bool(_runtime_identity())
        )
    except (OSError, ValueError) as exc:
        logger.error("proof_core_bridge._lean_command pinned Lean unavailable=%s", exc)
        valid = False
    result = [str(LEAN_BINARY), "-DwarningAsError=true"] if valid else []
    logger.debug("proof_core_bridge._lean_command exit result=%r", result)
    return result


def _toolchain_identity(command: list[str]) -> str:
    logger.debug("proof_core_bridge._toolchain_identity entry command=%r", command)
    try:
        proc = guarded_lean_run(
            command + ["--version"],
            cwd=TOOLCHAIN_ROOT,
            env=_clean_env(),
            timeout=30,
            expected=EXPECTED_LEAN_RUNTIME,
            absent_runtime=_runtime_absences(),
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("pinned-lean-version-timeout") from exc
    version = (proc.stdout or proc.stderr).strip()
    match = re.fullmatch(r"Lean \(version ([^,\s)]+)(?:,.*)?\)", version)
    if proc.returncode or match is None or match.group(1) != LEAN_VERSION:
        logger.error("proof_core_bridge._toolchain_identity mismatch rc=%d version=%r", proc.returncode, version)
        raise ValueError("pinned-lean-version-mismatch")
    metadata = Path(command[0]).stat()
    runtime = (
        f"merkle={EXPECTED_LEAN_RUNTIME[0]}|files={EXPECTED_LEAN_RUNTIME[1]}|"
        f"bytes={EXPECTED_LEAN_RUNTIME[2]}"
    )
    result = (
        f"{version}|toolchain={LEAN_TOOLCHAIN}|binary=lean|"
        f"sha256={EXPECTED_LEAN_BINARY_SHA256}|{runtime}|size={metadata.st_size}"
    )
    logger.debug("proof_core_bridge._toolchain_identity exit result=%s", result)
    return result


def _forbidden_source(source: bytes) -> tuple[str, ...]:
    logger.debug("proof_core_bridge._forbidden_source entry bytes=%d", len(source))
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        logger.error("proof_core_bridge._forbidden_source invalid UTF-8 error=%s", exc)
        raise ValueError("lean-source-not-utf8") from exc
    result = tuple(sorted(set(PLACEHOLDER.findall(text))))
    if result:
        logger.error("proof_core_bridge._forbidden_source tokens=%r", result)
    logger.debug("proof_core_bridge._forbidden_source exit count=%d", len(result))
    return result


def _source_closure(
    snapshot: LeanSourceSnapshot, sources: dict[str, bytes],
) -> ProtectedClosure:
    records = tuple(
        (path, len(sources[name]), sha256(sources[name]).digest())
        for name, path in snapshot.paths
    )
    return ProtectedClosure(
        "r7-snapshot-source",
        tuple(path for _, path in snapshot.paths),
        snapshot.root,
        R7_GUARDED_DOMAIN,
        records_digest(records, snapshot.root, R7_GUARDED_DOMAIN),
        exact_parents=True,
    )


def _object_closure(
    run_root: Path, objects: tuple[tuple[str, Path], ...],
) -> ProtectedClosure:
    records = tuple(
        (
            path,
            EXPECTED_LEAN_OBJECTS[name][1],
            bytes.fromhex(EXPECTED_LEAN_OBJECTS[name][2]),
        )
        for name, path in objects
    )
    return ProtectedClosure(
        "r7-prior-object",
        tuple(path for _, path in objects),
        run_root,
        R7_GUARDED_DOMAIN,
        records_digest(records, run_root, R7_GUARDED_DOMAIN),
        exact_parents=True,
    )


def _validate_fresh_object(run_root: Path, name: str, path: Path) -> None:
    filename, size, digest = EXPECTED_LEAN_OBJECTS[name]
    try:
        entries = tuple(path.parent.iterdir())
        metadata = path.lstat()
    except OSError as exc:
        raise ValueError("r7-lean-object-unreadable") from exc
    if (
        path.name != filename
        or entries != (path,)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
    ):
        raise ValueError("r7-lean-object-shape-mismatch")
    expected = records_digest(
        ((path, size, bytes.fromhex(digest)),),
        run_root,
        R7_GUARDED_DOMAIN,
    )
    if paths_digest((path,), run_root, R7_GUARDED_DOMAIN) != expected:
        raise ValueError("r7-lean-object-digest-mismatch")


def _compile_chain(
    command: list[str], snapshot: LeanSourceSnapshot, sources: dict[str, bytes],
) -> tuple[bool, str]:
    logger.debug("proof_core_bridge._compile_chain entry sources=%d", len(snapshot.paths))
    diagnostics: list[str] = []
    source_closure = _source_closure(snapshot, sources)
    if tuple(EXPECTED_LEAN_OBJECTS) != tuple(name for name, _ in snapshot.paths[:-1]):
        return False, "r7-lean-object-manifest-shape-mismatch"
    try:
        with TemporaryDirectory(prefix="compile-", dir=snapshot.output_dir) as run:
            run_root = Path(run)
            prior: list[tuple[str, Path]] = []
            for index, (source_name, source) in enumerate(snapshot.paths, start=1):
                stage = run_root / f"{index:02d}-{source.stem}"
                stage.mkdir(mode=0o700)
                output_path = stage / f"{source.stem}.olean"
                emit = source_name != "export"
                output = ["-o", str(output_path)] if emit else []
                protected = [source_closure]
                if prior:
                    protected.append(_object_closure(run_root, tuple(prior)))
                try:
                    proc = guarded_lean_run(
                        command + ["-R", str(snapshot.root)] + output + [str(source)],
                        cwd=snapshot.root,
                        env=_clean_env(tuple(path.parent for _, path in prior)),
                        timeout=120,
                        expected=EXPECTED_LEAN_RUNTIME,
                        protected=tuple(protected),
                        absent_runtime=_runtime_absences(),
                    )
                except subprocess.TimeoutExpired:
                    return False, ";".join(diagnostics) + f":{source.stem}:timeout"
                combined = (proc.stderr or "") + (proc.stdout or "")
                diagnostics.append(f"{index}/4:{source.stem}:rc={proc.returncode}")
                if proc.returncode or "warning:" in combined.lower():
                    detail = combined.strip()[-600:]
                    return False, ";".join(diagnostics) + ":" + detail
                if emit:
                    _validate_fresh_object(run_root, source_name, output_path)
                    prior.append((source_name, output_path))
    except (OSError, ValueError) as exc:
        logger.error("proof_core_bridge._compile_chain integrity blocked error=%s", exc)
        return False, str(exc)
    result = ";".join(diagnostics)
    logger.debug("proof_core_bridge._compile_chain exit diagnostics=%s", result)
    return True, result


def _blocked(
    reason: str, digest: str = "", artifact: bool = False,
    source: bool = False, manifest: bool = False,
) -> ProofCoreBridgeReport:
    logger.error("proof_core_bridge blocked reason=%s", reason)
    return ProofCoreBridgeReport(
        "blocked", (), digest, "", "", "", "", artifact, source, manifest,
        False, LEAN_TOOLCHAIN, reason,
        "no promotion unless theorem replay, reviewed TCB, byte binding, pinned Lean, and soundness all pass",
    )


def check_proof_core_bridge(
    theorem: IntrinsicResonanceTheorem | None = None,
    export_path: Path | None = None,
    arithmetic_path: Path | None = None,
    kernel_path: Path | None = None,
    soundness_path: Path | None = None,
) -> ProofCoreBridgeReport:
    """Rehash every input, enforce the reviewed TCB, then compile the chain."""
    logger.debug("check_proof_core_bridge entry custom_theorem=%s custom_paths=%s", theorem is not None, any((export_path, arithmetic_path, kernel_path, soundness_path)))
    item = intrinsic_resonance_theorem() if theorem is None else theorem
    digest = item.artifact.proof_digest
    if not verify_intrinsic_theorem_binding(item):
        return _blocked("theorem-artifact-replay-mismatch", digest)
    paths = {
        "arithmetic": Path(arithmetic_path or LEAN_DIR / "VeyraNativeArithmetic.lean"),
        "kernel": Path(kernel_path or LEAN_DIR / "VeyraProofKernel.lean"),
        "soundness": Path(soundness_path or LEAN_DIR / "VeyraProofSoundness.lean"),
        "export": Path(export_path or LEAN_DIR / "VeyraProofResonance.lean"),
    }
    try:
        sources = {name: _read(path) for name, path in paths.items()}
    except ValueError as exc:
        return _blocked(str(exc), digest, artifact=True)
    expected = render_resonance_lean(item).encode()
    if sources["export"] != expected:
        return _blocked("generated-lean-source-drift", digest, artifact=True)
    placeholders = _forbidden_source(b"\n".join(sources.values()))
    if placeholders:
        return _blocked("forbidden-lean-placeholder:" + ",".join(placeholders), digest, True, True)
    tcb_digests = {name: _sha(sources[name]) for name in EXPECTED_TCB_DIGESTS}
    if tcb_digests != EXPECTED_TCB_DIGESTS:
        return _blocked("reviewed-lean-tcb-drift", digest, True, True)
    command = _lean_command()
    if not command:
        return _blocked("pinned-lean-runtime-not-found", digest, True, True, True)
    try:
        toolchain = _toolchain_identity(command)
    except (OSError, ValueError) as exc:
        return _blocked(str(exc), digest, True, True, True)
    snapshot_key = _sha(canonical_json({
        "schema": "veyra-proof-lean-snapshot-v1",
        "sources": {name: _sha(source) for name, source in sources.items()},
        "toolchain": toolchain,
    }).encode())
    try:
        snapshot = materialize_lean_snapshot(BUILD_DIR, sources, snapshot_key)
    except ValueError as exc:
        return _blocked(str(exc), digest, True, True, True)
    lean_checked, diagnostics = _compile_chain(command, snapshot, sources)
    if not lean_checked:
        return _blocked(diagnostics, digest, True, True, True)
    export_digest = _sha(sources["export"])
    binding = _sha(canonical_json({
        "schema": "veyra-proof-lean-binding-v1", "tcb_schema": TCB_SCHEMA,
        "artifact": digest, **tcb_digests, "export": export_digest,
        "toolchain": toolchain,
    }).encode())
    result = ProofCoreBridgeReport(
        "checked", THEOREM_IDS, digest, tcb_digests["kernel"],
        tcb_digests["soundness"], export_digest, binding, True, True, True,
        True, toolchain, diagnostics,
        CHECKED_BOUNDARY,
    )
    logger.debug("check_proof_core_bridge exit binding=%s", result.binding_digest)
    return result


def verify_proof_core_bridge_report(report: object) -> bool:
    """Independently rehash every trust field exposed by a cached checked report."""
    logger.debug("verify_proof_core_bridge_report entry type=%s", type(report).__name__)
    if type(report) is not ProofCoreBridgeReport or report.status != "checked":
        logger.error("verify_proof_core_bridge_report rejected shape/status")
        return False
    item = intrinsic_resonance_theorem()
    paths = {
        "arithmetic": LEAN_DIR / "VeyraNativeArithmetic.lean",
        "kernel": LEAN_DIR / "VeyraProofKernel.lean",
        "soundness": LEAN_DIR / "VeyraProofSoundness.lean",
        "export": LEAN_DIR / "VeyraProofResonance.lean",
    }
    try:
        sources = {name: _read(path) for name, path in paths.items()}
        command = _lean_command()
        if not command or sources["export"] != render_resonance_lean(item).encode():
            logger.error("verify_proof_core_bridge_report source/toolchain mismatch")
            return False
        toolchain = _toolchain_identity(command)
    except (OSError, ValueError):
        logger.exception("verify_proof_core_bridge_report trust input failure")
        return False
    tcb_digests = {name: _sha(sources[name]) for name in EXPECTED_TCB_DIGESTS}
    export_digest = _sha(sources["export"])
    binding = _sha(canonical_json({
        "schema": "veyra-proof-lean-binding-v1", "tcb_schema": TCB_SCHEMA,
        "artifact": item.artifact.proof_digest, **tcb_digests,
        "export": export_digest, "toolchain": toolchain,
    }).encode())
    expected = ProofCoreBridgeReport(
        "checked", THEOREM_IDS, item.artifact.proof_digest,
        EXPECTED_TCB_DIGESTS["kernel"], EXPECTED_TCB_DIGESTS["soundness"],
        export_digest, binding, True, True, True, True, toolchain,
        CHECKED_DIAGNOSTICS, CHECKED_BOUNDARY,
    )
    result = tcb_digests == EXPECTED_TCB_DIGESTS and report == expected
    if not result:
        logger.error("verify_proof_core_bridge_report exact report mismatch")
    logger.debug("verify_proof_core_bridge_report exit result=%s", result)
    return result


def _default_trust_key() -> str:
    logger.debug("proof_core_bridge._default_trust_key entry")
    item = intrinsic_resonance_theorem()
    command = _lean_command()
    if not command:
        result = "no-pinned-lean-runtime"
    else:
        try:
            toolchain = _toolchain_identity(command)
            files = [
                LEAN_DIR / "VeyraNativeArithmetic.lean", LEAN_DIR / "VeyraProofKernel.lean",
                LEAN_DIR / "VeyraProofSoundness.lean", LEAN_DIR / "VeyraProofResonance.lean",
            ]
            result = _sha(canonical_json({
                "artifact": item.artifact.proof_digest,
                "sources": [_sha(_read(path)) for path in files],
                "toolchain": toolchain,
            }).encode())
        except (OSError, ValueError) as exc:
            logger.error("proof_core_bridge._default_trust_key blocked error=%s", exc)
            result = "blocked:" + str(exc)
    logger.debug("proof_core_bridge._default_trust_key exit result=%s", result)
    return result


@lru_cache(maxsize=8)
def _cached_default_report(trust_key: str) -> ProofCoreBridgeReport:
    logger.debug("proof_core_bridge._cached_default_report entry key=%s", trust_key)
    result = check_proof_core_bridge()
    logger.debug("proof_core_bridge._cached_default_report exit status=%s", result.status)
    return result


def proof_core_bridge_report() -> ProofCoreBridgeReport:
    """Rehash trust inputs every call; cache compilation only by that exact key."""
    logger.debug("proof_core_bridge_report entry")
    result = _cached_default_report(_default_trust_key())
    if result.status == "checked" and not verify_proof_core_bridge_report(result):
        result = _blocked("cached-proof-bridge-integrity-mismatch", result.artifact_digest)
    logger.debug("proof_core_bridge_report exit status=%s", result.status)
    return result

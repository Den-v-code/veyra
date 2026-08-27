"""POSIX hostile tests for bounded local P3-OG selection authority."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path

import pytest

from src.core.prime_power_observer_genesis_p3og import TransitionKind, p3og_source
from src.core.prime_power_observer_genesis_p3og_one_shot_selection import (
    P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY,
    P3OGSelectionLocalAuthorityError,
    P3OGSelectionLocalAuthorityState,
    claim_p3og_selection_local_authority,
    consume_p3og_selection_capability_locally,
    p3og_initial_selection_capability,
    p3og_one_shot_selection_source,
    read_p3og_selection_local_authority,
    reserve_p3og_selection_local_authority,
    validate_p3og_selection_local_authority,
)

pytestmark = pytest.mark.requires_posix_file_locks


def _source(label: str = "local-authority"):
    return p3og_source(
        prime=3,
        depth=1,
        source_instance_label=label,
        seed_rows=(("alpha", (0, 1, 0)), ("beta", (0, 2, 0))),
        calibration_inputs=(0, 1),
        maintenance_credit=2,
        suffix=(TransitionKind.IDLE,),
    )


def _fixture():
    source = _source()
    selection_source = p3og_one_shot_selection_source(source, "a" * 64)
    available = p3og_initial_selection_capability(source, selection_source)
    return source, selection_source, available


def _secure(path: Path) -> Path:
    path.mkdir(mode=0o700)
    path.chmod(0o700)
    return path


def test_local_authority_burns_before_selection_and_fresh_store_validation_passes(tmp_path: Path) -> None:
    source, selection_source, available = _fixture()
    directory = _secure(tmp_path / "authority")
    secret = bytes(range(32))
    reserved = reserve_p3og_selection_local_authority(
        directory, source, selection_source, available, "selection-1", secret
    )
    seed, consumed, selection, evidence = consume_p3og_selection_capability_locally(
        directory,
        source,
        selection_source,
        available,
        "selection-1",
        secret,
        "attempt-1",
    )
    assert reserved.state is P3OGSelectionLocalAuthorityState.RESERVED
    assert evidence.claimed.state is P3OGSelectionLocalAuthorityState.CLAIMED
    assert evidence.terminal.state is P3OGSelectionLocalAuthorityState.CONSUMED
    assert evidence.claimed.previous_receipt == evidence.reserved.receipt_digest
    assert evidence.terminal.previous_receipt == evidence.claimed.receipt_digest
    assert evidence.terminal.selection_receipt_digest == selection.receipt_digest
    assert selection.selected_seed_digest == seed.seed_digest
    assert read_p3og_selection_local_authority(directory) == evidence.terminal
    assert validate_p3og_selection_local_authority(
        directory,
        source,
        selection_source,
        available,
        consumed,
        selection,
        evidence,
    ) == evidence
    assert evidence.boundary == P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY
    assert secret not in (directory / "p3og-selection-local-authority-v1.json").read_bytes()


def test_copied_available_and_secret_cannot_claim_twice_in_same_store(tmp_path: Path) -> None:
    source, selection_source, available = _fixture()
    directory = _secure(tmp_path / "authority")
    secret = b"x" * 32
    reserve_p3og_selection_local_authority(
        directory, source, selection_source, available, "selection-1", secret
    )
    consume_p3og_selection_capability_locally(
        directory,
        source,
        selection_source,
        available,
        "selection-1",
        secret,
        "attempt-1",
    )
    with pytest.raises(P3OGSelectionLocalAuthorityError, match="not-reserved|already-claimed"):
        consume_p3og_selection_capability_locally(
            directory,
            source,
            selection_source,
            available,
            "selection-1",
            secret,
            "attempt-2",
        )


def test_claim_is_crash_safe_and_permanently_blocks_retry(tmp_path: Path) -> None:
    source, selection_source, available = _fixture()
    directory = _secure(tmp_path / "authority")
    secret = b"c" * 32
    reserve_p3og_selection_local_authority(
        directory, source, selection_source, available, "selection-1", secret
    )
    claimed = claim_p3og_selection_local_authority(
        directory, "selection-1", secret, "attempt-1"
    )
    assert claimed.state is P3OGSelectionLocalAuthorityState.CLAIMED
    with pytest.raises(P3OGSelectionLocalAuthorityError, match="already-claimed"):
        claim_p3og_selection_local_authority(
            directory, "selection-1", secret, "attempt-2"
        )


def test_concurrent_claim_has_exactly_one_local_winner(tmp_path: Path) -> None:
    source, selection_source, available = _fixture()
    directory = _secure(tmp_path / "authority")
    secret = b"r" * 32
    reserve_p3og_selection_local_authority(
        directory, source, selection_source, available, "selection-1", secret
    )

    def attempt(index: int) -> str:
        try:
            claim_p3og_selection_local_authority(
                directory, "selection-1", secret, f"attempt-{index}"
            )
        except P3OGSelectionLocalAuthorityError as exc:
            return exc.reason
        return "claimed"

    with ThreadPoolExecutor(max_workers=16) as pool:
        outcomes = tuple(pool.map(attempt, range(16)))
    assert outcomes.count("claimed") == 1
    assert outcomes.count("p3og-selection-local-authority-already-claimed") == 15


def test_foreign_selection_source_cannot_reuse_reserved_authority(tmp_path: Path) -> None:
    source, selection_source, available = _fixture()
    directory = _secure(tmp_path / "authority")
    secret = b"f" * 32
    reserve_p3og_selection_local_authority(
        directory, source, selection_source, available, "selection-1", secret
    )
    foreign_selection = p3og_one_shot_selection_source(source, "b" * 64)
    foreign_available = p3og_initial_selection_capability(source, foreign_selection)
    with pytest.raises(P3OGSelectionLocalAuthorityError, match="reservation-drift"):
        consume_p3og_selection_capability_locally(
            directory,
            source,
            foreign_selection,
            foreign_available,
            "selection-1",
            secret,
            "attempt-1",
        )


def test_wrong_secret_and_insecure_directory_fail_closed(tmp_path: Path) -> None:
    source, selection_source, available = _fixture()
    directory = _secure(tmp_path / "authority")
    secret = b"k" * 32
    reserve_p3og_selection_local_authority(
        directory, source, selection_source, available, "selection-1", secret
    )
    with pytest.raises(P3OGSelectionLocalAuthorityError, match="capability-mismatch"):
        claim_p3og_selection_local_authority(
            directory, "selection-1", b"z" * 32, "attempt-1"
        )

    insecure = tmp_path / "insecure"
    insecure.mkdir(mode=0o755)
    insecure.chmod(0o755)
    with pytest.raises(P3OGSelectionLocalAuthorityError, match="insecure-directory"):
        reserve_p3og_selection_local_authority(
            insecure, source, selection_source, available, "selection-2", b"q" * 32
        )


def test_forged_evidence_or_store_drift_is_rejected(tmp_path: Path) -> None:
    source, selection_source, available = _fixture()
    directory = _secure(tmp_path / "authority")
    secret = b"v" * 32
    reserve_p3og_selection_local_authority(
        directory, source, selection_source, available, "selection-1", secret
    )
    _seed, consumed, selection, evidence = consume_p3og_selection_capability_locally(
        directory,
        source,
        selection_source,
        available,
        "selection-1",
        secret,
        "attempt-1",
    )
    forged = replace(evidence, selection_receipt_digest="0" * 64)
    with pytest.raises(P3OGSelectionLocalAuthorityError, match="chain-drift|evidence-drift"):
        validate_p3og_selection_local_authority(
            directory,
            source,
            selection_source,
            available,
            consumed,
            selection,
            forged,
        )

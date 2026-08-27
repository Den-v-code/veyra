"""Atomic local one-shot authority for bounded P3-OG selection.

This layer is deliberately narrower than historical/global authority.  It serializes
cooperating processes through one protected POSIX directory, burns the reservation at
CLAIMED before evaluating selection, and leaves a crash at CLAIMED permanently spent.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import replace
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import secrets
import stat
from typing import Iterator, NoReturn

from src.platform_capabilities import Capability, require_capability

from .platform_posix import exclusive_file_lock
from .prime_power_observer_genesis_p3og_codec import canonical_bytes, digest
from .prime_power_observer_genesis_p3og_one_shot_selection_types import (
    P3OGOneShotSelectionReceipt,
    P3OGOneShotSelectionSource,
    P3OGSelectionCapability,
    SelectionCapabilityState,
)
from .prime_power_observer_genesis_p3og_one_shot_selection_validation import (
    consume_p3og_selection_capability,
    validate_p3og_one_shot_selection_receipt,
    validate_p3og_selection_capability,
)
from .prime_power_observer_genesis_p3og_source import validate_source
from .prime_power_observer_genesis_p3og_types import P3OGSource, PrimitiveModeSeed
from .prime_power_observer_genesis_p3og_selection_local_authority_types import (
    P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY,
    P3OGSelectionLocalAuthorityEvidence,
    P3OGSelectionLocalAuthorityReceipt,
    P3OGSelectionLocalAuthorityReservation,
    P3OGSelectionLocalAuthorityState,
)
from .proof_core_codec import canonical_json, digest_data, load_canonical

_LEDGER_SCHEMA = "veyra.p3og.selection-local-authority.v1"
_STATE_NAME = "p3og-selection-local-authority-v1.json"
_LOCK_NAME = ".p3og-selection-local-authority-v1.lock"
_MAX_LEDGER_BYTES = 65_536
_MAX_TEXT_BYTES = 512
_MAX_PATH_BYTES = 4096
_CAPABILITY_MIN_BYTES = 32
_CAPABILITY_MAX_BYTES = 4096
_HEX = frozenset("0123456789abcdef")


class P3OGSelectionLocalAuthorityError(RuntimeError):
    """Stable fail-closed rejection for the bounded local authority store."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def p3og_selection_local_authority_reservation(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    reservation_id: str,
) -> P3OGSelectionLocalAuthorityReservation:
    """Bind one local reservation to the exact AVAILABLE selection cut."""
    source = validate_source(source)
    _, selection_source = _validated_selection_source(source, selection_source)
    available = validate_p3og_selection_capability(source, selection_source, available)
    if available.state is not SelectionCapabilityState.AVAILABLE:
        _reject("p3og-selection-local-authority-capability-consumed")
    _bounded_text(reservation_id, "p3og-selection-local-authority-reservation-id")
    return P3OGSelectionLocalAuthorityReservation(
        reservation_id,
        source.source_digest,
        selection_source.source_digest,
        selection_source.source_closure.closure_digest,
        available.capability_digest,
        selection_source.capability_id,
    )


def reserve_p3og_selection_local_authority(
    directory: Path,
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    reservation_id: str,
    capability_secret: bytes,
) -> P3OGSelectionLocalAuthorityReceipt:
    """Reserve one secret-backed local authority before any selection evaluation."""
    reservation = p3og_selection_local_authority_reservation(
        source,
        selection_source,
        available,
        reservation_id,
    )
    capability_digest = _capability_digest(capability_secret)
    with _locked_directory(directory) as directory_fd:
        if _load_receipt(directory_fd, required=False) is not None:
            _reject("p3og-selection-local-authority-reservation-exists")
        draft = P3OGSelectionLocalAuthorityReceipt(
            reservation,
            P3OGSelectionLocalAuthorityState.RESERVED,
            capability_digest,
            "",
            "",
            0,
            "",
            P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY,
            "",
        )
        reserved = _bind_receipt(draft)
        _write_receipt(directory_fd, reserved)
    return reserved


def claim_p3og_selection_local_authority(
    directory: Path,
    reservation_id: str,
    capability_secret: bytes,
    attempt_id: str,
) -> P3OGSelectionLocalAuthorityReceipt:
    """Atomically burn the one local reservation before selection is evaluated."""
    _bounded_text(reservation_id, "p3og-selection-local-authority-reservation-id")
    _bounded_text(attempt_id, "p3og-selection-local-authority-attempt-id")
    capability_digest = _capability_digest(capability_secret)
    with _locked_directory(directory) as directory_fd:
        current = _load_receipt(directory_fd, required=True)
        assert current is not None
        if current.reservation.reservation_id != reservation_id:
            _reject("p3og-selection-local-authority-reservation-mismatch")
        _authenticate(current, capability_digest)
        if current.state is not P3OGSelectionLocalAuthorityState.RESERVED:
            _reject("p3og-selection-local-authority-already-claimed")
        attempt_digest = digest_data(
            {"reservation_receipt": current.receipt_digest, "attempt_id": attempt_id},
            "veyra.p3og.selection-local-attempt.v1",
        )
        claimed = _bind_receipt(
            replace(
                current,
                state=P3OGSelectionLocalAuthorityState.CLAIMED,
                attempt_digest=attempt_digest,
                revision=1,
                previous_receipt=current.receipt_digest,
                receipt_digest="",
            )
        )
        _write_receipt(directory_fd, claimed)
    return claimed


def finalize_p3og_selection_local_authority(
    directory: Path,
    reservation_id: str,
    capability_secret: bytes,
    claimed_receipt_digest: str,
    selection_receipt_digest: str,
) -> P3OGSelectionLocalAuthorityReceipt:
    """Bind the one burned attempt to exactly one completed selection receipt."""
    _bounded_text(reservation_id, "p3og-selection-local-authority-reservation-id")
    _require_digest(claimed_receipt_digest, "p3og-selection-local-authority-claimed-receipt")
    _require_digest(selection_receipt_digest, "p3og-selection-local-authority-selection-receipt")
    capability_digest = _capability_digest(capability_secret)
    with _locked_directory(directory) as directory_fd:
        current = _load_receipt(directory_fd, required=True)
        assert current is not None
        if current.reservation.reservation_id != reservation_id:
            _reject("p3og-selection-local-authority-reservation-mismatch")
        _authenticate(current, capability_digest)
        if current.state is not P3OGSelectionLocalAuthorityState.CLAIMED:
            _reject("p3og-selection-local-authority-not-finalizable")
        if not hmac.compare_digest(current.receipt_digest, claimed_receipt_digest):
            _reject("p3og-selection-local-authority-claimed-receipt-mismatch")
        terminal = _bind_receipt(
            replace(
                current,
                state=P3OGSelectionLocalAuthorityState.CONSUMED,
                selection_receipt_digest=selection_receipt_digest,
                revision=2,
                previous_receipt=current.receipt_digest,
                receipt_digest="",
            )
        )
        _write_receipt(directory_fd, terminal)
    return terminal


def consume_p3og_selection_capability_locally(
    directory: Path,
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    reservation_id: str,
    capability_secret: bytes,
    attempt_id: str,
) -> tuple[
    PrimitiveModeSeed,
    P3OGSelectionCapability,
    P3OGOneShotSelectionReceipt,
    P3OGSelectionLocalAuthorityEvidence,
]:
    """Burn local authority first, then evaluate exactly one deterministic selection."""
    expected_reservation = p3og_selection_local_authority_reservation(
        source,
        selection_source,
        available,
        reservation_id,
    )
    reserved = read_p3og_selection_local_authority(directory)
    if reserved.state is not P3OGSelectionLocalAuthorityState.RESERVED:
        _reject("p3og-selection-local-authority-not-reserved")
    if canonical_bytes(reserved.reservation) != canonical_bytes(expected_reservation):
        _reject("p3og-selection-local-authority-reservation-drift")
    claimed = claim_p3og_selection_local_authority(
        directory,
        reservation_id,
        capability_secret,
        attempt_id,
    )
    # Selection is intentionally evaluated only after the irreversible CLAIMED write.
    selected_seed, consumed, selection = consume_p3og_selection_capability(
        source,
        selection_source,
        available,
    )
    terminal = finalize_p3og_selection_local_authority(
        directory,
        reservation_id,
        capability_secret,
        claimed.receipt_digest,
        selection.receipt_digest,
    )
    evidence = _authority_evidence(reserved, claimed, terminal, selection.receipt_digest)
    return selected_seed, consumed, selection, evidence


def validate_p3og_selection_local_authority(
    directory: Path,
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
    available: P3OGSelectionCapability,
    consumed: P3OGSelectionCapability,
    selection: P3OGOneShotSelectionReceipt,
    evidence: P3OGSelectionLocalAuthorityEvidence,
) -> P3OGSelectionLocalAuthorityEvidence:
    """Freshly validate the immutable chain and the current protected store terminal."""
    source = validate_source(source)
    _, selection_source = _validated_selection_source(source, selection_source)
    expected_reservation = p3og_selection_local_authority_reservation(
        source,
        selection_source,
        available,
        evidence.reserved.reservation.reservation_id,
    )
    _seed, expected_consumed, expected_selection = validate_p3og_one_shot_selection_receipt(
        source,
        selection_source,
        available,
        consumed,
        selection,
    )
    if expected_consumed != consumed or expected_selection != selection:
        _reject("p3og-selection-local-authority-selection-drift")
    if type(evidence) is not P3OGSelectionLocalAuthorityEvidence:
        _reject("p3og-selection-local-authority-evidence-type")
    for receipt in (evidence.reserved, evidence.claimed, evidence.terminal):
        if not validate_p3og_selection_local_authority_receipt(receipt):
            _reject("p3og-selection-local-authority-receipt-invalid")
    if canonical_bytes(evidence.reserved.reservation) != canonical_bytes(expected_reservation):
        _reject("p3og-selection-local-authority-reservation-drift")
    if evidence.claimed.reservation != evidence.reserved.reservation or evidence.terminal.reservation != evidence.reserved.reservation:
        _reject("p3og-selection-local-authority-reservation-chain-drift")
    if (
        evidence.reserved.state is not P3OGSelectionLocalAuthorityState.RESERVED
        or evidence.claimed.state is not P3OGSelectionLocalAuthorityState.CLAIMED
        or evidence.terminal.state is not P3OGSelectionLocalAuthorityState.CONSUMED
        or evidence.claimed.previous_receipt != evidence.reserved.receipt_digest
        or evidence.terminal.previous_receipt != evidence.claimed.receipt_digest
        or evidence.selection_receipt_digest != selection.receipt_digest
        or evidence.terminal.selection_receipt_digest != selection.receipt_digest
        or evidence.boundary != P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY
    ):
        _reject("p3og-selection-local-authority-chain-drift")
    current = read_p3og_selection_local_authority(directory)
    if canonical_bytes(current) != canonical_bytes(evidence.terminal):
        _reject("p3og-selection-local-authority-store-drift")
    expected = _authority_evidence(
        evidence.reserved,
        evidence.claimed,
        evidence.terminal,
        selection.receipt_digest,
    )
    if canonical_bytes(expected) != canonical_bytes(evidence):
        _reject("p3og-selection-local-authority-evidence-drift")
    return replace(expected)


def read_p3og_selection_local_authority(directory: Path) -> P3OGSelectionLocalAuthorityReceipt:
    """Read the single current local authority row while holding the producer lock."""
    with _locked_directory(directory) as directory_fd:
        receipt = _load_receipt(directory_fd, required=True)
    assert receipt is not None
    return receipt


def validate_p3og_selection_local_authority_receipt(receipt: object) -> bool:
    """Validate one local receipt structurally without claiming store authority."""
    try:
        return _validate_receipt_shape(receipt) and _bind_receipt(replace(receipt, receipt_digest="")) == receipt
    except (AttributeError, TypeError, ValueError):
        return False


def _validated_selection_source(
    source: P3OGSource,
    selection_source: P3OGOneShotSelectionSource,
) -> tuple[P3OGSource, P3OGOneShotSelectionSource]:
    from .prime_power_observer_genesis_p3og_one_shot_selection_source import (
        validate_p3og_one_shot_selection_source,
    )
    return validate_p3og_one_shot_selection_source(source, selection_source)


def _authority_evidence(
    reserved: P3OGSelectionLocalAuthorityReceipt,
    claimed: P3OGSelectionLocalAuthorityReceipt,
    terminal: P3OGSelectionLocalAuthorityReceipt,
    selection_receipt_digest: str,
) -> P3OGSelectionLocalAuthorityEvidence:
    fields = (
        reserved,
        claimed,
        terminal,
        selection_receipt_digest,
        P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY,
    )
    return P3OGSelectionLocalAuthorityEvidence(
        *fields,
        digest("selection-local-authority-evidence", *fields),
    )


@contextmanager
def _locked_directory(directory: Path) -> Iterator[int]:
    directory_fd = _open_directory(directory)
    lock_fd = -1
    try:
        lock_fd = os.open(
            _LOCK_NAME,
            os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        _validate_owned_regular_fd(lock_fd, "p3og-selection-local-authority-lock-file")
        exclusive_file_lock(lock_fd)
        yield directory_fd
    except P3OGSelectionLocalAuthorityError:
        raise
    except (OSError, ValueError) as exc:
        raise P3OGSelectionLocalAuthorityError("p3og-selection-local-authority-io") from exc
    finally:
        if lock_fd >= 0:
            os.close(lock_fd)
        os.close(directory_fd)


def _open_directory(directory: Path) -> int:
    require_capability(Capability.POSIX_FILE_LOCKS)
    if not isinstance(directory, Path):
        _reject("p3og-selection-local-authority-directory-type")
    raw = os.fsencode(directory)
    if not raw or len(raw) > _MAX_PATH_BYTES or not hasattr(os, "O_NOFOLLOW"):
        _reject("p3og-selection-local-authority-directory-path")
    metadata = os.lstat(directory)
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != os.getuid() or metadata.st_mode & 0o077:
        _reject("p3og-selection-local-authority-insecure-directory")
    descriptor = os.open(
        directory,
        os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
    )
    opened = os.fstat(descriptor)
    if (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino):
        os.close(descriptor)
        _reject("p3og-selection-local-authority-directory-race")
    return descriptor


def _load_receipt(directory_fd: int, *, required: bool) -> P3OGSelectionLocalAuthorityReceipt | None:
    try:
        state_fd = os.open(
            _STATE_NAME,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
            dir_fd=directory_fd,
        )
    except FileNotFoundError:
        if required:
            _reject("p3og-selection-local-authority-reservation-not-found")
        return None
    try:
        metadata = _validate_owned_regular_fd(state_fd, "p3og-selection-local-authority-state-file")
        if metadata.st_size > _MAX_LEDGER_BYTES:
            _reject("p3og-selection-local-authority-ledger-size")
        payload = bytearray()
        while len(payload) <= metadata.st_size:
            chunk = os.read(state_fd, min(65_536, metadata.st_size + 1 - len(payload)))
            if not chunk:
                break
            payload.extend(chunk)
        if len(payload) != metadata.st_size:
            _reject("p3og-selection-local-authority-ledger-read")
    finally:
        os.close(state_fd)
    try:
        data = load_canonical(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise P3OGSelectionLocalAuthorityError("p3og-selection-local-authority-ledger-format") from exc
    if type(data) is not dict or set(data) != {"schema", "receipt"} or data["schema"] != _LEDGER_SCHEMA:
        _reject("p3og-selection-local-authority-ledger-schema")
    receipt = _receipt_from_data(data["receipt"])
    return receipt


def _write_receipt(directory_fd: int, receipt: P3OGSelectionLocalAuthorityReceipt) -> None:
    payload = canonical_json(
        {"schema": _LEDGER_SCHEMA, "receipt": _receipt_data(receipt, include_digest=True)}
    ).encode("utf-8")
    if len(payload) > _MAX_LEDGER_BYTES:
        _reject("p3og-selection-local-authority-ledger-size")
    temporary = f".p3og-selection-authority-{os.getpid()}-{secrets.token_hex(8)}.tmp"
    temp_fd = -1
    try:
        temp_fd = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        view = memoryview(payload)
        while view:
            written = os.write(temp_fd, view)
            if written <= 0:
                _reject("p3og-selection-local-authority-ledger-write")
            view = view[written:]
        os.fsync(temp_fd)
        os.close(temp_fd)
        temp_fd = -1
        os.replace(temporary, _STATE_NAME, src_dir_fd=directory_fd, dst_dir_fd=directory_fd)
        os.fsync(directory_fd)
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        try:
            os.unlink(temporary, dir_fd=directory_fd)
        except FileNotFoundError:
            pass


def _validate_owned_regular_fd(descriptor: int, reason: str) -> os.stat_result:
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or metadata.st_nlink != 1
        or metadata.st_mode & 0o077
    ):
        _reject(reason)
    return metadata


def _capability_digest(capability_secret: bytes) -> str:
    if type(capability_secret) is not bytes or not _CAPABILITY_MIN_BYTES <= len(capability_secret) <= _CAPABILITY_MAX_BYTES:
        _reject("p3og-selection-local-authority-capability-shape")
    return sha256(b"veyra.p3og.selection-local-capability.v1\0" + capability_secret).hexdigest()


def _authenticate(receipt: P3OGSelectionLocalAuthorityReceipt, capability_digest: str) -> None:
    if not hmac.compare_digest(receipt.capability_digest, capability_digest):
        _reject("p3og-selection-local-authority-capability-mismatch")


def _bind_receipt(receipt: P3OGSelectionLocalAuthorityReceipt) -> P3OGSelectionLocalAuthorityReceipt:
    value = digest_data(
        _receipt_data(receipt, include_digest=False),
        "veyra.p3og.selection-local-authority-receipt.v1",
    )
    return replace(receipt, receipt_digest=value)


def _validate_receipt_shape(receipt: object) -> bool:
    if type(receipt) is not P3OGSelectionLocalAuthorityReceipt or not _valid_reservation(receipt.reservation):
        return False
    common = (
        type(receipt.state) is P3OGSelectionLocalAuthorityState
        and _is_digest(receipt.capability_digest)
        and type(receipt.revision) is int
        and 0 <= receipt.revision <= 2
        and receipt.boundary == P3OG_SELECTION_LOCAL_AUTHORITY_BOUNDARY
        and _is_digest(receipt.receipt_digest)
        and (not receipt.previous_receipt or _is_digest(receipt.previous_receipt))
        and (not receipt.attempt_digest or _is_digest(receipt.attempt_digest))
        and (not receipt.selection_receipt_digest or _is_digest(receipt.selection_receipt_digest))
    )
    if receipt.state is P3OGSelectionLocalAuthorityState.RESERVED:
        state_valid = receipt.revision == 0 and not receipt.attempt_digest and not receipt.selection_receipt_digest and not receipt.previous_receipt
    elif receipt.state is P3OGSelectionLocalAuthorityState.CLAIMED:
        state_valid = receipt.revision == 1 and _is_digest(receipt.attempt_digest) and not receipt.selection_receipt_digest and _is_digest(receipt.previous_receipt)
    else:
        state_valid = receipt.revision == 2 and _is_digest(receipt.attempt_digest) and _is_digest(receipt.selection_receipt_digest) and _is_digest(receipt.previous_receipt)
    return common and state_valid


def _valid_reservation(reservation: object) -> bool:
    try:
        return (
            type(reservation) is P3OGSelectionLocalAuthorityReservation
            and _text_valid(reservation.reservation_id)
            and all(
                _is_digest(value)
                for value in (
                    reservation.pressure_source_digest,
                    reservation.selection_source_digest,
                    reservation.source_closure_digest,
                    reservation.available_capability_digest,
                    reservation.capability_id,
                )
            )
        )
    except AttributeError:
        return False


def _receipt_data(receipt: P3OGSelectionLocalAuthorityReceipt, *, include_digest: bool) -> dict[str, object]:
    data = {
        "reservation": {
            "reservation_id": receipt.reservation.reservation_id,
            "pressure_source_digest": receipt.reservation.pressure_source_digest,
            "selection_source_digest": receipt.reservation.selection_source_digest,
            "source_closure_digest": receipt.reservation.source_closure_digest,
            "available_capability_digest": receipt.reservation.available_capability_digest,
            "capability_id": receipt.reservation.capability_id,
        },
        "state": receipt.state.value,
        "capability_digest": receipt.capability_digest,
        "attempt_digest": receipt.attempt_digest,
        "selection_receipt_digest": receipt.selection_receipt_digest,
        "revision": receipt.revision,
        "previous_receipt": receipt.previous_receipt,
        "boundary": receipt.boundary,
    }
    if include_digest:
        data["receipt_digest"] = receipt.receipt_digest
    return data


def _receipt_from_data(data: object) -> P3OGSelectionLocalAuthorityReceipt:
    expected = {
        "reservation", "state", "capability_digest", "attempt_digest",
        "selection_receipt_digest", "revision", "previous_receipt", "boundary", "receipt_digest",
    }
    if type(data) is not dict or set(data) != expected or type(data["reservation"]) is not dict:
        _reject("p3og-selection-local-authority-receipt-shape")
    reservation_keys = {
        "reservation_id", "pressure_source_digest", "selection_source_digest",
        "source_closure_digest", "available_capability_digest", "capability_id",
    }
    row = data["reservation"]
    if set(row) != reservation_keys:
        _reject("p3og-selection-local-authority-reservation-shape")
    try:
        receipt = P3OGSelectionLocalAuthorityReceipt(
            P3OGSelectionLocalAuthorityReservation(**row),
            P3OGSelectionLocalAuthorityState(data["state"]),
            data["capability_digest"],
            data["attempt_digest"],
            data["selection_receipt_digest"],
            data["revision"],
            data["previous_receipt"],
            data["boundary"],
            data["receipt_digest"],
        )
    except (TypeError, ValueError) as exc:
        raise P3OGSelectionLocalAuthorityError("p3og-selection-local-authority-receipt-shape") from exc
    if not validate_p3og_selection_local_authority_receipt(receipt):
        _reject("p3og-selection-local-authority-receipt-invalid")
    return receipt


def _bounded_text(value: object, reason: str) -> None:
    if not _text_valid(value):
        _reject(reason)


def _text_valid(value: object) -> bool:
    try:
        return type(value) is str and bool(value) and len(value) <= _MAX_TEXT_BYTES and len(value.encode("utf-8")) <= _MAX_TEXT_BYTES
    except UnicodeError:
        return False


def _require_digest(value: object, reason: str) -> None:
    if not _is_digest(value):
        _reject(reason)


def _is_digest(value: object) -> bool:
    return type(value) is str and len(value) == 64 and all(character in _HEX for character in value)


def _reject(reason: str) -> NoReturn:
    raise P3OGSelectionLocalAuthorityError(reason)

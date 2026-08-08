"""Canonical KEB1 encoder and manifest-only source-root machinery."""

from __future__ import annotations

from hashlib import sha256
import logging
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Protocol, cast
import unicodedata

from . import omegaa_keb1_types as _syntax
from . import omegaa_kpt1_codec as _kpt_codec_module
from . import omegaa_kpt1_common as _kpt_common_module
from . import omegaa_kpt1_types as _kpt_syntax_module
from .omegaa_keb1_builder import validate_keb1_builder_integrity_v1
from .omegaa_keb1_common import (
    DEFAULT_KEB1_LIMITS_V1, KEB1_PREFIX, MAX_COMPOSITE_DEPTH, MAX_COMPOSITE_NODES,
    MAX_EXPECTED_WIRE, MAX_KPT_LIST, MAX_KPT_NAT, MAX_NESTED_KPT, MAX_OUTPUT,
    KEB1DecodeCodeV1, KEB1LimitsV1, KEB1ResourceKindV1, FirstUnsignedDifferenceV1,
    _decode_error, _frame, _integrity_error, _resource, _snapshot_limits,
)
from .omegaa_keb1_preflight import preflight_kpt_wire_v1, validate_keb1_preflight_integrity_v1
from .omegaa_kpt1_common import KPT1LimitsV1
from .omegaa_kpt1_types import KernelProofTermV1, KernelUniverseLevelV1

logger = logging.getLogger(__name__)
_LOGGER = logger
_BINDING_CLASS = _syntax.ExpectedBindingSyntaxV1
_KPT_CLASS, _LEVEL_CLASS = KernelProofTermV1, KernelUniverseLevelV1
_TERM_SLOT = vars(_BINDING_CLASS)["expected_term"]
_WIRE_SLOT = vars(_BINDING_CLASS)["expected_wire"]
_KPT_CODEC = _kpt_codec_module.codec_kernel_proof_term_v1
_KPT_CODEC_CODE = _KPT_CODEC.__code__
_KPT_CODEC_NS = vars(_kpt_codec_module)
_KPT_CODEC_FUNCTION_NAMES = ("_check_slot_descriptors", "_mag_size", "_preflight", "_u64", "_frame")
_KPT_CODEC_FUNCTIONS = tuple(_KPT_CODEC_NS[name] for name in _KPT_CODEC_FUNCTION_NAMES)
_KPT_CODEC_FUNCTION_CODES = tuple(function.__code__ for function in _KPT_CODEC_FUNCTIONS)
_KPT_CODEC_STATIC_NAMES = (
    "_snapshot_limits", "_resource", "_host_error", "_slot", "_FIELD_KINDS",
    "KernelLevelTagV1", "KernelProofTermV1", "KernelTermTagV1",
    "KernelUniverseLevelV1", "kpt1_level_arity_v1", "kpt1_level_ordinal_v1",
    "kpt1_term_ordinal_v1", "validate_kpt1_enum_integrity_v1", "KPT1_PREFIX",
    "MAX_DEPTH", "MAX_LIST", "MAX_NAT", "MAX_NODES", "MAX_OUTPUT", "logger",
)
_KPT_CODEC_STATICS = tuple(_KPT_CODEC_NS[name] for name in _KPT_CODEC_STATIC_NAMES)
_KPT_LIMIT_CLASS = KPT1LimitsV1
_KPT_LIMIT_NAMES = ("max_input_bytes", "max_output_bytes", "max_depth", "max_nodes", "max_list_items", "max_nat_bytes")
_KPT_LIMIT_SLOTS = tuple(vars(_KPT_LIMIT_CLASS)[name] for name in _KPT_LIMIT_NAMES)
_OBJECT_NEW_FROZEN = object.__new__
_OBJECT_NEW = _OBJECT_NEW_FROZEN
_PREFIX = KEB1_PREFIX
_KPT_SOURCE_ROOT_FROZEN = bytes.fromhex("55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a")
_KPT_SOURCE_ROOT = _KPT_SOURCE_ROOT_FROZEN
KEB1_SOURCE_PATHS_V1 = (
    "src/core/omegaa_keb1_builder.py", "src/core/omegaa_keb1_codec.py",
    "src/core/omegaa_keb1_common.py", "src/core/omegaa_keb1_parser.py",
    "src/core/omegaa_keb1_preflight.py", "src/core/omegaa_keb1_types.py",
)
_SOURCE_PATHS = KEB1_SOURCE_PATHS_V1
_REPOSITORY_ROOT = Path(__file__).parents[2]
_SHA256_FROZEN = sha256
_OS_MODULE = os
_OS_OPEN = os.open
_OS_CLOSE = os.close
_OS_READ = os.read
_OS_FSTAT = os.fstat
_PATH_FROZEN = Path
_PATH_TYPE = type(_REPOSITORY_ROOT)
_PURE_PATH_FROZEN = PurePosixPath
_STAT_MODULE = stat
_STAT_ISREG = stat.S_ISREG
_UNICODE_MODULE = unicodedata
_UNICODE_NORMALIZE = unicodedata.normalize
_FRAME_FROZEN = _frame
_FRAME_CODE = _FRAME_FROZEN.__code__
_DEFAULT_LIMITS_FROZEN = DEFAULT_KEB1_LIMITS_V1
_VALIDATE_BUILDER_FROZEN = validate_keb1_builder_integrity_v1
_VALIDATE_BUILDER_CODE = _VALIDATE_BUILDER_FROZEN.__code__
_PREFLIGHT_FROZEN = preflight_kpt_wire_v1
_PREFLIGHT_CODE = _PREFLIGHT_FROZEN.__code__
_VALIDATE_PREFLIGHT_FROZEN = validate_keb1_preflight_integrity_v1
_VALIDATE_PREFLIGHT_CODE = _VALIDATE_PREFLIGHT_FROZEN.__code__
_FIRST_DIFF_FROZEN = FirstUnsignedDifferenceV1
_FIRST_DIFF_CODE = _FIRST_DIFF_FROZEN.__code__
_DECODE_ERROR_FROZEN, _RESOURCE_FROZEN = _decode_error, _resource
_SNAPSHOT_FROZEN, _INTEGRITY_FROZEN = _snapshot_limits, _integrity_error
_COMMON_FUNCTIONS = (_DECODE_ERROR_FROZEN, _RESOURCE_FROZEN, _SNAPSHOT_FROZEN, _INTEGRITY_FROZEN)
_COMMON_FUNCTION_CODES = tuple(function.__code__ for function in _COMMON_FUNCTIONS)


class _SlotSetter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def _make_permissive_kpt_limits_v1() -> KPT1LimitsV1:
    _LOGGER.debug("_make_permissive_kpt_limits_v1 entry")
    if any(vars(_KPT_LIMIT_CLASS).get(name) is not slot for name, slot in zip(_KPT_LIMIT_NAMES, _KPT_LIMIT_SLOTS, strict=True)):
        _integrity_error("keb1-kpt-limits-integrity")
    result = _OBJECT_NEW_FROZEN(_KPT_LIMIT_CLASS)
    for slot, value in zip(_KPT_LIMIT_SLOTS, (2**64 - 1, 2**64 - 1, 128, 2**64 - 1, 2**64 - 1, 2**64 - 1), strict=True):
        cast(_SlotSetter, slot).__set__(result, value)
    _LOGGER.debug("_make_permissive_kpt_limits_v1 exit")
    return result


def _resource_candidates_v1(payload: bytes, values: tuple[int, ...]) -> list[tuple[int, int, KEB1ResourceKindV1, int, int]]:
    _LOGGER.debug("_resource_candidates_v1 entry bytes=%d", len(payload))
    report = _PREFLIGHT_FROZEN(payload)
    if report.decode_candidates or not report.root_consumed:
        _integrity_error("keb1-host-kpt-noncanonical")
    candidates: list[tuple[int, int, KEB1ResourceKindV1, int, int]] = []
    rows = (
        (KEB1ResourceKindV1.OUTPUT_BYTES, values[MAX_OUTPUT], 22 + 2 * len(payload), 0),
        (KEB1ResourceKindV1.NESTED_KPT_BYTES, values[MAX_NESTED_KPT], len(payload), 14),
        (KEB1ResourceKindV1.EXPECTED_WIRE_BYTES, values[MAX_EXPECTED_WIRE], len(payload), 22 + len(payload)),
    )
    for kind, allowed, required, offset in rows:
        if required > allowed:
            candidates.append((offset, int(kind), kind, allowed, required))
    for metric in report.nodes:
        required_depth = 1 + metric.depth
        if required_depth > values[MAX_COMPOSITE_DEPTH]:
            kind = KEB1ResourceKindV1.COMPOSITE_DEPTH
            candidates.append((14 + metric.node_start, int(kind), kind, values[MAX_COMPOSITE_DEPTH], required_depth))
        required_nodes = 1 + metric.running_node_count
        if required_nodes > values[MAX_COMPOSITE_NODES]:
            kind = KEB1ResourceKindV1.COMPOSITE_NODES
            candidates.append((14 + metric.node_start, int(kind), kind, values[MAX_COMPOSITE_NODES], required_nodes))
    for list_metric in report.lists:
        if list_metric.count > values[MAX_KPT_LIST]:
            kind = KEB1ResourceKindV1.KPT_LIST_ITEMS
            candidates.append((14 + list_metric.count_start, int(kind), kind, values[MAX_KPT_LIST], list_metric.count))
    for nat_metric in report.nats:
        if nat_metric.count > values[MAX_KPT_NAT]:
            kind = KEB1ResourceKindV1.KPT_NAT_BYTES
            candidates.append((14 + nat_metric.count_start, int(kind), kind, values[MAX_KPT_NAT], nat_metric.count))
    _LOGGER.debug("_resource_candidates_v1 exit candidates=%d", len(candidates))
    return candidates


_MAKE_LIMITS_FROZEN = _make_permissive_kpt_limits_v1
_MAKE_LIMITS_CODE = _MAKE_LIMITS_FROZEN.__code__
_RESOURCE_CANDIDATES_FROZEN = _resource_candidates_v1
_RESOURCE_CANDIDATES_CODE = _RESOURCE_CANDIDATES_FROZEN.__code__


def validate_keb1_codec_integrity_v1() -> None:
    _LOGGER.debug("validate_keb1_codec_integrity_v1 entry")
    drift = (
        globals().get("logger") is not _LOGGER or vars(_syntax).get("ExpectedBindingSyntaxV1") is not _BINDING_CLASS
        or vars(_kpt_codec_module).get("codec_kernel_proof_term_v1") is not _KPT_CODEC or _KPT_CODEC.__code__ is not _KPT_CODEC_CODE
        or any(_KPT_CODEC_NS.get(name) is not function or function.__code__ is not code for name, function, code in zip(_KPT_CODEC_FUNCTION_NAMES, _KPT_CODEC_FUNCTIONS, _KPT_CODEC_FUNCTION_CODES, strict=True))
        or any(_KPT_CODEC_NS.get(name) is not value for name, value in zip(_KPT_CODEC_STATIC_NAMES, _KPT_CODEC_STATICS, strict=True))
        or _kpt_common_module.KPT1LimitsV1 is not _KPT_LIMIT_CLASS
        or _kpt_syntax_module.KernelProofTermV1 is not _KPT_CLASS
        or _kpt_syntax_module.KernelUniverseLevelV1 is not _LEVEL_CLASS
        or vars(_BINDING_CLASS).get("expected_term") is not _TERM_SLOT or vars(_BINDING_CLASS).get("expected_wire") is not _WIRE_SLOT
        or globals().get("KEB1_PREFIX") is not _PREFIX or _PREFIX != b"KEB1"
        or globals().get("KEB1_SOURCE_PATHS_V1") is not _SOURCE_PATHS
        or _SOURCE_PATHS != tuple(sorted((
            "src/core/omegaa_keb1_builder.py", "src/core/omegaa_keb1_codec.py",
            "src/core/omegaa_keb1_common.py", "src/core/omegaa_keb1_parser.py",
            "src/core/omegaa_keb1_preflight.py", "src/core/omegaa_keb1_types.py",
        )))
        or globals().get("sha256") is not _SHA256_FROZEN
        or globals().get("os") is not _OS_MODULE or os.open is not _OS_OPEN or os.close is not _OS_CLOSE or os.read is not _OS_READ or os.fstat is not _OS_FSTAT
        or globals().get("Path") is not _PATH_FROZEN or globals().get("PurePosixPath") is not _PURE_PATH_FROZEN
        or globals().get("stat") is not _STAT_MODULE or stat.S_ISREG is not _STAT_ISREG
        or globals().get("unicodedata") is not _UNICODE_MODULE or unicodedata.normalize is not _UNICODE_NORMALIZE
        or globals().get("_frame") is not _FRAME_FROZEN or _FRAME_FROZEN.__code__ is not _FRAME_CODE
        or globals().get("DEFAULT_KEB1_LIMITS_V1") is not _DEFAULT_LIMITS_FROZEN
        or globals().get("_OBJECT_NEW") is not _OBJECT_NEW_FROZEN or object.__new__ is not _OBJECT_NEW_FROZEN
        or globals().get("_KPT_SOURCE_ROOT") is not _KPT_SOURCE_ROOT_FROZEN
        or _KPT_SOURCE_ROOT_FROZEN.hex() != "55e2e0be76a65458e3f58388a5602d1aa41b0407b66b132b26b49439b731942a"
        or globals().get("validate_keb1_builder_integrity_v1") is not _VALIDATE_BUILDER_FROZEN or _VALIDATE_BUILDER_FROZEN.__code__ is not _VALIDATE_BUILDER_CODE
        or globals().get("preflight_kpt_wire_v1") is not _PREFLIGHT_FROZEN or _PREFLIGHT_FROZEN.__code__ is not _PREFLIGHT_CODE
        or globals().get("validate_keb1_preflight_integrity_v1") is not _VALIDATE_PREFLIGHT_FROZEN or _VALIDATE_PREFLIGHT_FROZEN.__code__ is not _VALIDATE_PREFLIGHT_CODE
        or globals().get("FirstUnsignedDifferenceV1") is not _FIRST_DIFF_FROZEN or _FIRST_DIFF_FROZEN.__code__ is not _FIRST_DIFF_CODE
        or tuple(function.__code__ for function in _COMMON_FUNCTIONS) != _COMMON_FUNCTION_CODES
        or (globals().get("_decode_error"), globals().get("_resource"), globals().get("_snapshot_limits"), globals().get("_integrity_error")) != _COMMON_FUNCTIONS
        or globals().get("_make_permissive_kpt_limits_v1") is not _MAKE_LIMITS_FROZEN or _MAKE_LIMITS_FROZEN.__code__ is not _MAKE_LIMITS_CODE
        or globals().get("_resource_candidates_v1") is not _RESOURCE_CANDIDATES_FROZEN or _RESOURCE_CANDIDATES_FROZEN.__code__ is not _RESOURCE_CANDIDATES_CODE
        or type(_REPOSITORY_ROOT) is not _PATH_TYPE or not _REPOSITORY_ROOT.is_absolute()
        or _REPOSITORY_ROOT != _PATH_FROZEN(__file__).parents[2]
        or globals().get("codec_expected_binding_v1") is not _CODEC_PUBLIC
        or _CODEC_PUBLIC.__code__ is not _CODEC_PUBLIC_CODE
        or _CODEC_PUBLIC.__defaults__ is not _CODEC_PUBLIC_DEFAULTS
        or _CODEC_PUBLIC_DEFAULTS != (_DEFAULT_LIMITS_FROZEN,)
    )
    if drift:
        _integrity_error("keb1-codec-integrity")
    _VALIDATE_BUILDER_FROZEN()
    _VALIDATE_PREFLIGHT_FROZEN()
    _LOGGER.debug("validate_keb1_codec_integrity_v1 exit")


_VALIDATE_CODEC_FROZEN = validate_keb1_codec_integrity_v1
_VALIDATE_CODEC_CODE = _VALIDATE_CODEC_FROZEN.__code__


def codec_expected_binding_v1(binding: _syntax.ExpectedBindingSyntaxV1, limits: KEB1LimitsV1 = DEFAULT_KEB1_LIMITS_V1) -> bytes:
    """Encode one exact binding after global canonical and resource checks."""
    _LOGGER.debug("codec_expected_binding_v1 entry")
    if globals().get("validate_keb1_codec_integrity_v1") is not _VALIDATE_CODEC_FROZEN or _VALIDATE_CODEC_FROZEN.__code__ is not _VALIDATE_CODEC_CODE:
        _INTEGRITY_FROZEN("keb1-codec-validator-integrity")
    _VALIDATE_CODEC_FROZEN()
    values = _SNAPSHOT_FROZEN(limits)
    if type(binding) is not _BINDING_CLASS:
        _integrity_error("keb1-binding-host-shape")
    term = cast(KernelProofTermV1, _TERM_SLOT.__get__(binding, _BINDING_CLASS))
    wire = _WIRE_SLOT.__get__(binding, _BINDING_CLASS)
    if type(term) is not _KPT_CLASS or type(wire) is not bytes:
        _integrity_error("keb1-binding-host-shape")
    try:
        payload = _KPT_CODEC(term, _MAKE_LIMITS_FROZEN())
    except Exception as exc:
        _LOGGER.error("codec_expected_binding_v1 error dependency=%s", type(exc).__name__)
        _integrity_error("keb1-kpt-codec-refusal")
    if type(payload) is not bytes:
        _integrity_error("keb1-kpt-codec-result")
    if wire != payload:
        difference = _FIRST_DIFF_FROZEN(wire, payload)
        if type(difference) is not int:
            _integrity_error("keb1-first-difference-integrity")
        _DECODE_ERROR_FROZEN(KEB1DecodeCodeV1.DEPENDENCY, 22 + len(payload) + difference)
    candidates = _RESOURCE_CANDIDATES_FROZEN(payload, values)
    if candidates:
        offset, _, kind, allowed, required = min(candidates)
        _RESOURCE_FROZEN(kind, allowed, required, offset)
    result = _PREFIX + b"\x00\x02" + _FRAME_FROZEN(payload) + _FRAME_FROZEN(payload)
    _LOGGER.debug("codec_expected_binding_v1 exit bytes=%d", len(result))
    return result


_CODEC_PUBLIC = codec_expected_binding_v1
_CODEC_PUBLIC_CODE = _CODEC_PUBLIC.__code__
_CODEC_PUBLIC_DEFAULTS = _CODEC_PUBLIC.__defaults__


def _open_absolute_root_v1(root: Path) -> int:
    """Open every absolute-root component with no-follow directory FDs."""
    _LOGGER.debug("_open_absolute_root_v1 entry")
    if type(root) is not _PATH_TYPE or not root.is_absolute():
        _integrity_error("keb1-manifest-root-shape")
    flags = _OS_MODULE.O_RDONLY | _OS_MODULE.O_CLOEXEC | _OS_MODULE.O_NOFOLLOW | _OS_MODULE.O_DIRECTORY
    descriptor = _OS_OPEN("/", flags)
    try:
        for part in root.parts[1:]:
            next_descriptor = _OS_OPEN(part, flags, dir_fd=descriptor)
            _OS_CLOSE(descriptor)
            descriptor = next_descriptor
    except OSError:
        _OS_CLOSE(descriptor)
        _integrity_error("keb1-manifest-root-integrity")
    _LOGGER.debug("_open_absolute_root_v1 exit")
    return descriptor


_OPEN_ROOT = _open_absolute_root_v1
_OPEN_ROOT_CODE = _OPEN_ROOT.__code__


def _manifest_v1(paths: tuple[str, ...] = _SOURCE_PATHS, root: Path = _REPOSITORY_ROOT) -> bytes:
    _LOGGER.debug("_manifest_v1 entry paths=%d", len(paths))
    if paths is not _SOURCE_PATHS or paths != tuple(sorted(paths)) or len(paths) != len(set(paths)) or type(root) is not _PATH_TYPE or root != _REPOSITORY_ROOT:
        _integrity_error("keb1-manifest-closed-input")
    chunks: list[bytes] = []
    flags = _OS_MODULE.O_RDONLY | _OS_MODULE.O_CLOEXEC | _OS_MODULE.O_NOFOLLOW
    for name in paths:
        if type(name) is not str or _UNICODE_NORMALIZE("NFC", name) != name:
            _integrity_error("keb1-manifest-path-text")
        pure = _PURE_PATH_FROZEN(name)
        if pure.is_absolute() or str(pure) != name or any(part in {"", ".", ".."} for part in pure.parts):
            _integrity_error("keb1-manifest-path-relative")
        directory_fd = _OPEN_ROOT(root)
        file_fd = -1
        try:
            for part in pure.parts[:-1]:
                next_fd = _OS_OPEN(part, flags | _OS_MODULE.O_DIRECTORY, dir_fd=directory_fd)
                _OS_CLOSE(directory_fd)
                directory_fd = next_fd
            file_fd = _OS_OPEN(pure.parts[-1], flags, dir_fd=directory_fd)
            before = _OS_FSTAT(file_fd)
            if not _STAT_ISREG(before.st_mode):
                _integrity_error("keb1-manifest-path-integrity")
            data_parts: list[bytes] = []
            while True:
                chunk = _OS_READ(file_fd, 131_072)
                if not chunk:
                    break
                data_parts.append(chunk)
            after = _OS_FSTAT(file_fd)
            if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                _integrity_error("keb1-manifest-read-drift")
            chunks.append(_FRAME_FROZEN(name.encode("utf-8")) + _FRAME_FROZEN(b"".join(data_parts)))
        except OSError:
            _integrity_error("keb1-manifest-path-integrity")
        finally:
            if file_fd >= 0:
                _OS_CLOSE(file_fd)
            _OS_CLOSE(directory_fd)
    result = len(paths).to_bytes(8, "big") + b"".join(chunks)
    _LOGGER.debug("_manifest_v1 exit bytes=%d", len(result))
    return result


_MANIFEST = _manifest_v1
_MANIFEST_CODE = _MANIFEST.__code__
_MANIFEST_DEFAULTS = _MANIFEST.__defaults__


def keb1_source_root_v1() -> bytes:
    """Recompute ``RootV1(label,[KPT1_SOURCE_ROOT,SourceManifest])``."""
    _LOGGER.debug("keb1_source_root_v1 entry")
    validate_keb1_codec_integrity_v1()
    if (
        globals().get("_open_absolute_root_v1") is not _OPEN_ROOT
        or _OPEN_ROOT.__code__ is not _OPEN_ROOT_CODE
        or globals().get("_manifest_v1") is not _MANIFEST
        or _MANIFEST.__code__ is not _MANIFEST_CODE
        or _MANIFEST.__defaults__ is not _MANIFEST_DEFAULTS
        or _MANIFEST_DEFAULTS != (_SOURCE_PATHS, _REPOSITORY_ROOT)
    ):
        _integrity_error("keb1-manifest-helper-integrity")
    label = _FRAME_FROZEN(b"omegaa.keb1-source.v1")
    result = _SHA256_FROZEN(label + _FRAME_FROZEN(_KPT_SOURCE_ROOT) + _FRAME_FROZEN(_MANIFEST())).digest()
    _LOGGER.debug("keb1_source_root_v1 exit")
    return result


ExpectedBindingSyntaxV1 = _BINDING_CLASS

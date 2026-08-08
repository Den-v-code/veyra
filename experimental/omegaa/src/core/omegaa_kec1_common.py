"""Captured integrity, internal control flow and request accounting for KEC1."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from types import MemberDescriptorType
from typing import Callable, Generator, Generic, NoReturn, Protocol, TypeVar, cast

from . import omegaa_kpt1_types as _kpt
from . import omegaa_kpt1_codec as _kpt_codec
from . import omegaa_kec1_types as _types
from .omegaa_kpt1_codec import codec_kernel_proof_term_v1
from .omegaa_kpt1_common import KPT1LimitsV1, KPT1_MAX_SAFE_DEPTH
from .omegaa_kpt1_types import KernelProofTermV1, KernelUniverseLevelV1
from .omegaa_kec1_types import (
    DEFAULT_KEC1_LIMITS_V1,
    KEC1ApiV1,
    KEC1IntegrityCodeV1,
    KEC1IntegrityV1,
    KEC1LimitsV1,
    KEC1LocusV1,
    KEC1OffsetSpaceV1,
    KEC1OriginTagV1,
    KEC1OriginV1,
    KEC1RefusalCodeV1,
    KEC1RefusalV1,
    KEC1ResourceKindV1,
    KEC1ResourceV1,
    KEC1ResultTagV1,
    KEC1ResultV1,
    KEC1_EQUATION_BYTES_V1,
    KEC1_EQUATION_ROWS_V1,
)

logger = logging.getLogger(__name__)
_TERM_CLASS = KernelProofTermV1
_LEVEL_CLASS = KernelUniverseLevelV1
_TERM_TAG_SLOT = vars(_TERM_CLASS)["tag"]
_TERM_FIELDS_SLOT = vars(_TERM_CLASS)["fields"]
_LEVEL_TAG_SLOT = vars(_LEVEL_CLASS)["tag"]
_LEVEL_FIELDS_SLOT = vars(_LEVEL_CLASS)["fields"]
_FIELD_KINDS = _kpt.KPT1_FIELD_KINDS
_KPT_CODEC_MODULE = _kpt_codec
_KPT_CODEC = codec_kernel_proof_term_v1
_KPT_CODEC_CODE = _KPT_CODEC.__code__
_LIMIT_NAMES = tuple(KEC1LimitsV1.__slots__)
_LIMIT_SLOTS = tuple(vars(KEC1LimitsV1)[name] for name in _LIMIT_NAMES)
_DEFAULT = DEFAULT_KEC1_LIMITS_V1
_TYPES_MODULE = _types
_DEFAULT_VALUES = (
    1048576,
    10000,
    128,
    4096,
    64,
    10000,
    10000,
    128,
    10000,
    1048576,
    4096,
    64,
    128,
    10000,
    1048576,
    4096,
    64,
)
_ENUMS = (
    KEC1ApiV1,
    KEC1ResultTagV1,
    KEC1RefusalCodeV1,
    KEC1IntegrityCodeV1,
    KEC1OriginTagV1,
    KEC1OffsetSpaceV1,
    KEC1ResourceKindV1,
)
_ENUM_COUNTS = (6, 7, 9, 11, 5, 2, 17)
_ENUM_NAMES = (
    "KEC1ApiV1",
    "KEC1ResultTagV1",
    "KEC1RefusalCodeV1",
    "KEC1IntegrityCodeV1",
    "KEC1OriginTagV1",
    "KEC1OffsetSpaceV1",
    "KEC1ResourceKindV1",
)
_RECORD_CLASSES = (
    KEC1OriginV1,
    KEC1LocusV1,
    KEC1RefusalV1,
    KEC1ResourceV1,
    KEC1IntegrityV1,
    KEC1ResultV1,
    KEC1LimitsV1,
)
_RECORD_NAMES = (
    "KEC1OriginV1",
    "KEC1LocusV1",
    "KEC1RefusalV1",
    "KEC1ResourceV1",
    "KEC1IntegrityV1",
    "KEC1ResultV1",
    "KEC1LimitsV1",
)
_RECORD_SLOTS = tuple(tuple(vars(cls)["__slots__"]) for cls in _RECORD_CLASSES)
_RECORD_DESCRIPTORS = tuple(
    tuple(vars(cls)[name] for name in names) for cls, names in zip(_RECORD_CLASSES, _RECORD_SLOTS, strict=True)
)
_RECORD_INITS = tuple(vars(cls)["__init__"] for cls in _RECORD_CLASSES)
_RECORD_INIT_CODES = tuple(function.__code__ for function in _RECORD_INITS)
_RECORD_POSTS = tuple(vars(cls)["__post_init__"] for cls in _RECORD_CLASSES)
_RECORD_POST_CODES = tuple(function.__code__ for function in _RECORD_POSTS)
_EQUATION_ROWS = KEC1_EQUATION_ROWS_V1
_EQUATION_BYTES = KEC1_EQUATION_BYTES_V1


class _Slot(Protocol):
    def __get__(self, instance: object, owner: type[object]) -> object: ...


class _Setter(Protocol):
    def __set__(self, instance: object, value: object) -> None: ...


def _record(index: int, values: tuple[object, ...]) -> object:
    """Construct one captured exact record without generated/user hooks."""
    logger.debug("_record entry index=%d fields=%d", index, len(values))
    cls = _RECORD_CLASSES[index]
    descriptors = _RECORD_DESCRIPTORS[index]
    if len(values) != len(descriptors):
        logger.error("_record error arity index=%d", index)
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    result = object.__new__(cls)
    for descriptor, value in zip(descriptors, values, strict=True):
        cast(_Setter, descriptor).__set__(result, value)
    logger.debug("_record exit index=%d", index)
    return result


class _Abort(Exception):
    pass


class _Refuse(_Abort):
    def __init__(self, code: KEC1RefusalCodeV1, locus: KEC1LocusV1) -> None:
        logger.debug("_Refuse.__init__ entry")
        self.code, self.locus = code, locus
        logger.debug("_Refuse.__init__ exit")


class _Resource(_Abort):
    def __init__(self, kind: KEC1ResourceKindV1, allowed: int, current: int, locus: KEC1LocusV1) -> None:
        logger.debug("_Resource.__init__ entry kind=%s", kind.name)
        self.kind, self.allowed, self.current, self.locus = kind, allowed, current, locus
        logger.debug("_Resource.__init__ exit kind=%s", kind.name)


class _Integrity(_Abort):
    def __init__(self, code: KEC1IntegrityCodeV1) -> None:
        logger.debug("_Integrity.__init__ entry code=%s", code.name)
        self.code = code
        logger.debug("_Integrity.__init__ exit code=%s", code.name)


@dataclass(frozen=True, slots=True)
class Metrics:
    depth: int
    nodes: int
    wire_bytes: int
    list_items: int
    nat_bytes: int


_T = TypeVar("_T")
WorkGenerator = Generator["WorkRequest", object, _T]
WorkFactory = Callable[[], WorkGenerator[object]]


@dataclass(frozen=True, slots=True)
class WorkRequest:
    """A delayed child batch; factories and generators allocate after gating."""

    count: int
    locus: KEC1LocusV1
    allocate: Callable[[], tuple[WorkFactory, ...]]


@dataclass(slots=True)
class _Batch:
    parent: _WorkFrame
    results: list[object]
    remaining: int


@dataclass(slots=True)
class _WorkFrame:
    generator: WorkGenerator[object]
    kind: str
    batch: _Batch | None = None
    index: int = 0
    started: bool = False
    ready: bool = False
    pending: object = None
    waiting: _Batch | None = None


_WORK_KINDS = frozenset(("WF", "INFER", "CHECK", "HEAD", "REDUCE", "REBUILD", "OUTPUT"))


def _work_kind(generator: WorkGenerator[object]) -> str:
    """Map one exact generator code name to the frozen semantic frame kind."""
    logger.debug("_work_kind entry")
    code = getattr(generator, "gi_code", None)
    name = getattr(code, "co_name", None)
    if type(name) is not str:
        logger.error("_work_kind error generator-code")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    if name.startswith("_wf"):
        result = "WF"
    elif "output" in name or "checked" in name:
        result = "OUTPUT"
    elif "check" in name:
        result = "CHECK"
    elif "infer" in name:
        result = "INFER"
    elif "whnf" in name:
        result = "HEAD"
    elif "reduce" in name or "redex" in name or name.startswith("nf_") or "defeq" in name or "require" in name:
        result = "REDUCE"
    else:
        result = "REBUILD"
    if result not in _WORK_KINDS:
        logger.error("_work_kind error name=%s", name)
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    logger.debug("_work_kind exit kind=%s", result)
    return result


def work_request(count: int, where: KEC1LocusV1, allocate: Callable[[], tuple[WorkFactory, ...]]) -> WorkRequest:
    """Describe a batch without allocating its child factories or generators."""
    logger.debug("work_request entry count=%d", count)
    if type(count) is not int or count <= 0 or not callable(allocate):
        logger.error("work_request error invalid-request")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
    result = WorkRequest(count, where, allocate)
    logger.debug("work_request exit count=%d", count)
    return result


class WorkMachine(Generic[_T]):
    """Explicit deterministic LIFO scheduler for every semantic work frame."""

    def __init__(self, engine: Engine) -> None:
        logger.debug("WorkMachine.__init__ entry")
        self.engine = engine
        self.trace: list[tuple[str, int]] = []
        self.batches: list[tuple[int, int]] = []
        logger.debug("WorkMachine.__init__ exit")

    def run(self, root: Callable[[], WorkGenerator[_T]], where: KEC1LocusV1) -> _T:
        """Gate, allocate and execute the root plus delayed child batches."""
        logger.debug("WorkMachine.run entry")
        self.engine.gate_batch(0, 1, where)
        root_generator = root()
        if not hasattr(root_generator, "send"):
            logger.error("WorkMachine.run error root-generator")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
        root_cast = cast(WorkGenerator[object], root_generator)
        root_kind = _work_kind(root_cast)
        stack: list[_WorkFrame] = [_WorkFrame(root_cast, root_kind)]
        self.trace.append((root_kind, 1))
        while stack:
            frame = stack[-1]
            if frame.waiting is not None:
                logger.error("WorkMachine.run error resumed-waiting-parent")
                raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
            try:
                if not frame.started:
                    frame.started = True
                    event = next(frame.generator)
                elif frame.ready:
                    frame.ready = False
                    pending = frame.pending
                    frame.pending = None
                    event = frame.generator.send(pending)
                else:
                    logger.error("WorkMachine.run error frame-not-ready")
                    raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
            except StopIteration as stop:
                value = stop.value
                stack.pop()
                if frame.batch is None:
                    if stack:
                        logger.error("WorkMachine.run error orphan-root")
                        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
                    logger.debug("WorkMachine.run exit")
                    return cast(_T, value)
                batch = frame.batch
                batch.results[frame.index] = value
                batch.remaining -= 1
                logger.debug("WorkMachine.run state child-complete remaining=%d", batch.remaining)
                if batch.remaining == 0:
                    batch.parent.waiting = None
                    batch.parent.pending = tuple(batch.results)
                    batch.parent.ready = True
                continue
            if type(event) is not WorkRequest or frame.waiting is not None:
                logger.error("WorkMachine.run error invalid-event")
                raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
            self.engine.gate_batch(len(stack), event.count, event.locus)
            self.batches.append((len(stack), event.count))
            try:
                factories = event.allocate()
            except _Abort:
                logger.error("WorkMachine.run error batch-allocation-abort")
                raise
            except BaseException:
                logger.error("WorkMachine.run error batch-allocation")
                raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT) from None
            if (
                type(factories) is not tuple
                or len(factories) != event.count
                or any(not callable(factory) for factory in factories)
            ):
                logger.error("WorkMachine.run error factory-batch")
                raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
            state = _Batch(frame, [None] * event.count, event.count)
            children: list[_WorkFrame] = []
            for index, factory in enumerate(factories):
                generator = factory()
                if not hasattr(generator, "send"):
                    logger.error("WorkMachine.run error child-generator")
                    raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
                kind = _work_kind(generator)
                children.append(_WorkFrame(generator, kind, state, index))
                self.trace.append((kind, len(stack) + event.count))
            frame.waiting = state
            stack.extend(reversed(children))
            logger.debug("WorkMachine.run state batch-pushed count=%d depth=%d", event.count, len(stack))
        logger.error("WorkMachine.run error empty-without-result")
        raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)


def locus(
    origin: KEC1OriginV1,
    path: tuple[int, ...] = (),
    offset: int = 4,
    space: KEC1OffsetSpaceV1 = KEC1OffsetSpaceV1.KPT_WIRE,
) -> KEC1LocusV1:
    """Create one internal exact locus without inspecting hostile objects."""
    logger.debug("locus entry path_depth=%d", len(path))
    result = cast(KEC1LocusV1, _record(1, (origin, path, space, offset)))
    logger.debug("locus exit")
    return result


def origin_v1(tag: KEC1OriginTagV1, index: int = 0) -> KEC1OriginV1:
    """Construct one trusted exact origin without generated hooks."""
    logger.debug("origin_v1 entry tag=%s index=%d", tag.name, index)
    result = cast(KEC1OriginV1, _record(0, (tag, index)))
    logger.debug("origin_v1 exit")
    return result


def term_slot(node: object) -> tuple[object, object]:
    """Read captured KPT term slots without invoking instance lookup."""
    try:
        return (_TERM_TAG_SLOT.__get__(node, _TERM_CLASS), _TERM_FIELDS_SLOT.__get__(node, _TERM_CLASS))
    except BaseException:
        logger.error("term_slot error")
        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE) from None


def level_slot(node: object) -> tuple[object, object]:
    """Read captured KPT level slots without invoking instance lookup."""
    try:
        return (_LEVEL_TAG_SLOT.__get__(node, _LEVEL_CLASS), _LEVEL_FIELDS_SLOT.__get__(node, _LEVEL_CLASS))
    except BaseException:
        logger.error("level_slot error")
        raise _Integrity(KEC1IntegrityCodeV1.HOST_SHAPE) from None


def validate_integrity(limits: object, publics: tuple[Callable[..., object], ...] | None = None) -> tuple[int, ...]:
    """Reject all frozen enum, descriptor, default and public-default drift first."""
    logger.debug("validate_integrity entry")
    types_namespace = vars(_TYPES_MODULE)
    if any(types_namespace.get(name) is not enum for name, enum in zip(_ENUM_NAMES, _ENUMS, strict=True)):
        raise _Integrity(KEC1IntegrityCodeV1.ENUM_DRIFT)
    if any(types_namespace.get(name) is not cls for name, cls in zip(_RECORD_NAMES, _RECORD_CLASSES, strict=True)):
        raise _Integrity(KEC1IntegrityCodeV1.TABLE_DRIFT)
    for cls, names, descriptors, init, init_code, post, post_code in zip(
        _RECORD_CLASSES,
        _RECORD_SLOTS,
        _RECORD_DESCRIPTORS,
        _RECORD_INITS,
        _RECORD_INIT_CODES,
        _RECORD_POSTS,
        _RECORD_POST_CODES,
        strict=True,
    ):
        namespace = vars(cls)
        if (
            tuple(namespace.get("__slots__", ())) != names
            or any(namespace.get(name) is not descriptor for name, descriptor in zip(names, descriptors, strict=True))
            or namespace.get("__init__") is not init
            or init.__code__ is not init_code
            or namespace.get("__post_init__") is not post
            or post.__code__ is not post_code
        ):
            raise _Integrity(KEC1IntegrityCodeV1.SLOT_DRIFT)
    if (
        types_namespace.get("KEC1_EQUATION_ROWS_V1") is not _EQUATION_ROWS
        or types_namespace.get("KEC1_EQUATION_BYTES_V1") is not _EQUATION_BYTES
        or len(_EQUATION_ROWS) != 43
    ):
        raise _Integrity(KEC1IntegrityCodeV1.TABLE_DRIFT)
    if (
        vars(_TERM_CLASS).get("tag") is not _TERM_TAG_SLOT
        or vars(_TERM_CLASS).get("fields") is not _TERM_FIELDS_SLOT
        or vars(_LEVEL_CLASS).get("tag") is not _LEVEL_TAG_SLOT
        or vars(_LEVEL_CLASS).get("fields") is not _LEVEL_FIELDS_SLOT
        or any(
            type(slot) is not MemberDescriptorType
            for slot in (*_LIMIT_SLOTS, _TERM_TAG_SLOT, _TERM_FIELDS_SLOT, _LEVEL_TAG_SLOT, _LEVEL_FIELDS_SLOT)
        )
    ):
        raise _Integrity(KEC1IntegrityCodeV1.SLOT_DRIFT)
    if (
        vars(_kpt).get("KPT1_FIELD_KINDS") is not _FIELD_KINDS
        or vars(_kpt).get("KernelProofTermV1") is not _TERM_CLASS
        or vars(_kpt).get("KernelUniverseLevelV1") is not _LEVEL_CLASS
    ):
        raise _Integrity(KEC1IntegrityCodeV1.TABLE_DRIFT)
    if (
        vars(_KPT_CODEC_MODULE).get("codec_kernel_proof_term_v1") is not _KPT_CODEC
        or _KPT_CODEC.__code__ is not _KPT_CODEC_CODE
    ):
        raise _Integrity(KEC1IntegrityCodeV1.CODEC_DRIFT)
    for enum, count in zip(_ENUMS, _ENUM_COUNTS, strict=True):
        try:
            if tuple(enum(i) for i in range(count)) != tuple(enum) or any(enum(i).value != i for i in range(count)):
                raise _Integrity(KEC1IntegrityCodeV1.ENUM_DRIFT)
        except BaseException as exc:
            if isinstance(exc, _Integrity):
                raise
            raise _Integrity(KEC1IntegrityCodeV1.ENUM_DRIFT) from None
    if (
        globals().get("DEFAULT_KEC1_LIMITS_V1", _DEFAULT) is not _DEFAULT
        or vars(_TYPES_MODULE).get("DEFAULT_KEC1_LIMITS_V1") is not _DEFAULT
        or vars(_TYPES_MODULE).get("KEC1LimitsV1") is not KEC1LimitsV1
    ):
        raise _Integrity(KEC1IntegrityCodeV1.LIMIT_DRIFT)
    if type(limits) is not KEC1LimitsV1 or any(
        vars(KEC1LimitsV1).get(n) is not s for n, s in zip(_LIMIT_NAMES, _LIMIT_SLOTS, strict=True)
    ):
        raise _Integrity(KEC1IntegrityCodeV1.LIMIT_DRIFT)
    try:
        raw_values = tuple(cast(_Slot, slot).__get__(limits, KEC1LimitsV1) for slot in _LIMIT_SLOTS)
        defaults = tuple(cast(_Slot, slot).__get__(_DEFAULT, KEC1LimitsV1) for slot in _LIMIT_SLOTS)
    except BaseException:
        raise _Integrity(KEC1IntegrityCodeV1.LIMIT_DRIFT) from None
    if defaults != _DEFAULT_VALUES or any(type(x) is not int or x <= 0 for x in raw_values):
        raise _Integrity(KEC1IntegrityCodeV1.LIMIT_DRIFT)
    values = cast(tuple[int, ...], raw_values)
    if any(values[i] > KPT1_MAX_SAFE_DEPTH for i in (2, 7, 12)):
        raise _Integrity(KEC1IntegrityCodeV1.LIMIT_DRIFT)
    if publics is not None and any(
        getattr(fn, "__defaults__", None) != (_DEFAULT,)
        or cast(tuple[object, ...], getattr(fn, "__defaults__"))[0] is not _DEFAULT
        for fn in publics
    ):
        raise _Integrity(KEC1IntegrityCodeV1.LIMIT_DRIFT)
    logger.debug("validate_integrity exit")
    return values


def kpt_limits(values: tuple[int, ...], phase: str) -> KPT1LimitsV1:
    """Map one exact KEC phase allowance to the frozen six-field KPT order."""
    logger.debug("kpt_limits entry phase=%s", phase)
    if phase == "input":
        b, n, d, items, mag = values[0:5]
    elif phase == "generated":
        d, n, b, items, mag = values[7:12]
    elif phase == "output":
        d, n, b, items, mag = values[12:17]
    else:
        raise _Integrity(KEC1IntegrityCodeV1.MAPPING_DRIFT)
    try:
        result = KPT1LimitsV1(max(1, b), max(1, b), max(1, d), max(1, n), max(1, items), max(1, mag))
    except BaseException:
        raise _Integrity(KEC1IntegrityCodeV1.MAPPING_DRIFT) from None
    logger.debug("kpt_limits exit")
    return result


class Engine:
    """One request-global deterministic work/normalization/generated budget."""

    def __init__(self, values: tuple[int, ...]) -> None:
        logger.debug("Engine.__init__ entry")
        self.values = values
        self.work = 0
        self.steps = 0
        self.generated_nodes = 0
        self.generated_bytes = 0
        self.production = 0
        self.current_origin = cast(KEC1OriginV1, _record(0, (KEC1OriginTagV1.SYNTHETIC, 0)))
        logger.debug("Engine.__init__ exit")

    def enter(self, where: KEC1LocusV1, batch: int = 1) -> None:
        logger.debug("Engine.enter entry work=%d batch=%d", self.work, batch)
        required = self.work + batch
        if required > self.values[5]:
            logger.error("Engine.enter resource work allowed=%d current=%d", self.values[5], required)
            raise _Resource(KEC1ResourceKindV1.WORK_DEPTH, self.values[5], required, where)
        self.work = required
        logger.debug("Engine.enter exit work=%d", self.work)

    def gate_batch(self, stack_depth: int, batch_size: int, where: KEC1LocusV1) -> None:
        """Prospectively gate an explicit LIFO batch before child allocation."""
        logger.debug("Engine.gate_batch entry depth=%d batch=%d", stack_depth, batch_size)
        if type(stack_depth) is not int or type(batch_size) is not int or stack_depth < 0 or batch_size <= 0:
            logger.error("Engine.gate_batch error invalid-count")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
        required = stack_depth + batch_size
        if required > self.values[5]:
            logger.error("Engine.gate_batch resource work allowed=%d current=%d", self.values[5], required)
            raise _Resource(KEC1ResourceKindV1.WORK_DEPTH, self.values[5], required, where)
        logger.debug("Engine.gate_batch exit required=%d", required)

    def leave(self, batch: int = 1) -> None:
        logger.debug("Engine.leave entry work=%d batch=%d", self.work, batch)
        self.work -= batch
        if self.work < 0:
            logger.error("Engine.leave invariant negative-work")
            raise _Integrity(KEC1IntegrityCodeV1.INTERNAL_INVARIANT)
        logger.debug("Engine.leave exit work=%d", self.work)

    def begin(self) -> KEC1OriginV1:
        logger.debug("Engine.begin entry production=%d", self.production)
        self.production += 1
        self.current_origin = cast(
            KEC1OriginV1,
            _record(0, (KEC1OriginTagV1.SYNTHETIC, self.production)),
        )
        logger.debug("Engine.begin exit production=%d", self.production)
        return self.current_origin

    def contraction(self, where: KEC1LocusV1) -> None:
        logger.debug("Engine.contraction entry steps=%d", self.steps)
        required = self.steps + 1
        if required > self.values[6]:
            logger.error("Engine.contraction resource allowed=%d current=%d", self.values[6], required)
            raise _Resource(KEC1ResourceKindV1.NORMALIZE_STEPS, self.values[6], required, where)
        self.steps = required
        logger.debug("Engine.contraction exit steps=%d", self.steps)

    def generated(self, metrics: Metrics, where: KEC1LocusV1) -> None:
        logger.debug("Engine.generated entry nodes=%d bytes=%d", self.generated_nodes, self.generated_bytes)
        checks = (
            (KEC1ResourceKindV1.GENERATED_DEPTH, self.values[7], metrics.depth),
            (KEC1ResourceKindV1.GENERATED_NODES, self.values[8], self.generated_nodes + 1),
            (KEC1ResourceKindV1.GENERATED_BYTES, self.values[9], self.generated_bytes + metrics.wire_bytes),
            (KEC1ResourceKindV1.GENERATED_LIST_ITEMS, self.values[10], metrics.list_items),
            (KEC1ResourceKindV1.GENERATED_NAT_BYTES, self.values[11], metrics.nat_bytes),
        )
        for kind, allowed, current in checks:
            if current > allowed:
                logger.error("Engine.generated resource kind=%s allowed=%d current=%d", kind.name, allowed, current)
                raise _Resource(kind, allowed, current, where)
        self.generated_nodes += 1
        self.generated_bytes += metrics.wire_bytes
        logger.debug("Engine.generated exit nodes=%d bytes=%d", self.generated_nodes, self.generated_bytes)


def abort_result(api: KEC1ApiV1, exc: _Abort) -> KEC1ResultV1:
    """Convert sanitized internal flow into the exact public sum."""
    logger.error("KEC1 abort api=%s channel=%s", api.name, type(exc).__name__)
    if type(exc) is _Refuse:
        payload = _record(2, (exc.code, exc.locus))
        return cast(KEC1ResultV1, _record(5, (api, KEC1ResultTagV1.REFUSAL, payload)))
    if type(exc) is _Resource:
        payload = _record(3, (exc.kind, exc.allowed, exc.current, exc.locus))
        return cast(KEC1ResultV1, _record(5, (api, KEC1ResultTagV1.RESOURCE, payload)))
    code = exc.code if type(exc) is _Integrity else KEC1IntegrityCodeV1.INTERNAL_INVARIANT
    payload = _record(4, (code,))
    return cast(KEC1ResultV1, _record(5, (api, KEC1ResultTagV1.INTEGRITY, payload)))


def result_v1(api: KEC1ApiV1, tag: KEC1ResultTagV1, payload: object) -> KEC1ResultV1:
    """Construct one already-validated public result without class hooks."""
    logger.debug("result_v1 entry api=%s tag=%s", api.name, tag.name)
    result = cast(KEC1ResultV1, _record(5, (api, tag, payload)))
    logger.debug("result_v1 exit")
    return result


def refuse(code: KEC1RefusalCodeV1, where: KEC1LocusV1) -> NoReturn:
    logger.info("KEC1 semantic refusal code=%s", code.name)
    raise _Refuse(code, where)


def encode_exact(term: KernelProofTermV1, values: tuple[int, ...], phase: str) -> bytes:
    """Invoke the captured KPT codec only after KEC gating and sanitize drift."""
    logger.debug("encode_exact entry phase=%s", phase)
    try:
        result: bytes = _KPT_CODEC(term, kpt_limits(values, phase))
    except BaseException:
        logger.error("encode_exact error phase=%s", phase)
        raise _Integrity(KEC1IntegrityCodeV1.CODEC_DRIFT) from None
    logger.debug("encode_exact exit bytes=%d", len(result))
    return result

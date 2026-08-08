"""Exact nominal KCS1 checker-state, report, and codec result syntax."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from typing import TypeAlias, final

from .omegaa_kcc1_types import EmptyCheckerConfigV1
from .omegaa_kcf1_types import KernelContinuationFrameV1
from .omegaa_kci1_types import CheckerInputSyntaxV1
from .omegaa_keb1_types import ExpectedBindingSyntaxV1
from .omegaa_kpt1_types import KernelProofTermV1

logger = logging.getLogger(__name__)


class KCS1NodeTagV1(IntEnum):
    ENTRY = 0
    PARSE = 1
    INFER = 2
    REDUCE = 3
    COMPARE_TYPES = 4
    RETURN_TYPED = 5


class KCS1StateTagV1(IntEnum):
    RUN = 0
    ACCEPT = 1
    REJECT = 2


class KCS1ReductionTagV1(IntEnum):
    NF = 0
    STEP = 1


class KCS1LocusTagV1(IntEnum):
    INPUT_OFFSET = 0
    STATE_STEP = 1
    STRUCTURAL_COUNT = 2
    NONE = 3


class KCS1RejectCodeSyntaxV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


class KCS1AttemptResourceKindV1(IntEnum):
    INPUT_BYTES = 0
    OUTPUT_BYTES = 1
    COMPOSITE_DEPTH = 2
    COMPOSITE_NODES = 3
    VECTOR_ITEMS = 4
    NESTED_KPT_BYTES = 5
    KPT_LIST_ITEMS = 6
    KPT_NAT_BYTES = 7
    STEPS = 8
    DEADLINE_NS = 9
    MEMORY_BYTES = 10


class KCS1InternalCodeV1(IntEnum):
    INTEGRITY = 0
    INVARIANT = 1
    HOST_EXCEPTION = 2


class KCS1CodecResourceKindV1(IntEnum):
    INPUT_BYTES = 0
    OUTPUT_BYTES = 1
    COMPOSITE_DEPTH = 2
    COMPOSITE_NODES = 3
    VECTOR_ITEMS = 4
    NESTED_WIRE_BYTES = 5
    NESTED_LIST_ITEMS = 6
    NESTED_NAT_BYTES = 7


class KCS1IntegrityCodeV1(IntEnum):
    HOST_SHAPE = 0
    GRAPH_CYCLE = 1
    GRAPH_SHARED = 2
    TABLE_DRIFT = 3
    SLOT_DRIFT = 4
    ENUM_DRIFT = 5
    CODE_DRIFT = 6
    LIMIT_DRIFT = 7
    NESTED_MAP_DRIFT = 8
    INTERNAL_INVARIANT = 9


def _u64(value: object) -> bool:
    logger.debug("_u64 entry")
    result = type(value) is int and 0 <= value < 2**64
    logger.debug("_u64 exit valid=%s", result)
    return result


def _nat(value: object) -> bool:
    logger.debug("_nat entry")
    result = type(value) is int and value >= 0
    logger.debug("_nat exit valid=%s", result)
    return result


def _bytes32(value: object) -> bool:
    logger.debug("_bytes32 entry")
    result = type(value) is bytes and len(value) == 32
    logger.debug("_bytes32 exit valid=%s", result)
    return result


def _reject(reason: str) -> None:
    logger.debug("_reject entry reason=%s", reason)
    logger.error("KCS1 nominal syntax rejected reason=%s", reason)
    raise ValueError(reason)


@final
@dataclass(frozen=True, slots=True)
class KCS1EntryNodeV1:
    binding: ExpectedBindingSyntaxV1

    def __post_init__(self) -> None:
        logger.debug("KCS1EntryNodeV1.__post_init__ entry")
        if type(self.binding) is not ExpectedBindingSyntaxV1:
            _reject("entry-binding")
        logger.debug("KCS1EntryNodeV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCS1ParseNodeV1:
    payload: bytes

    def __post_init__(self) -> None:
        logger.debug("KCS1ParseNodeV1.__post_init__ entry")
        if type(self.payload) is not bytes:
            _reject("parse-payload")
        logger.debug("KCS1ParseNodeV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCS1InferNodeV1:
    term: KernelProofTermV1

    def __post_init__(self) -> None:
        logger.debug("KCS1InferNodeV1.__post_init__ entry")
        if type(self.term) is not KernelProofTermV1:
            _reject("infer-term")
        logger.debug("KCS1InferNodeV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCS1ReduceNodeV1:
    term: KernelProofTermV1

    def __post_init__(self) -> None:
        logger.debug("KCS1ReduceNodeV1.__post_init__ entry")
        if type(self.term) is not KernelProofTermV1:
            _reject("reduce-term")
        logger.debug("KCS1ReduceNodeV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCS1CompareTypesNodeV1:
    term: KernelProofTermV1
    expected_nf: KernelProofTermV1
    inferred_nf: KernelProofTermV1

    def __post_init__(self) -> None:
        logger.debug("KCS1CompareTypesNodeV1.__post_init__ entry")
        if any(type(x) is not KernelProofTermV1 for x in (self.term, self.expected_nf, self.inferred_nf)):
            _reject("compare-terms")
        logger.debug("KCS1CompareTypesNodeV1.__post_init__ exit")


@final
@dataclass(frozen=True, slots=True)
class KCS1ReturnTypedNodeV1:
    kernel_type_id: bytes

    def __post_init__(self) -> None:
        logger.debug("KCS1ReturnTypedNodeV1.__post_init__ entry")
        if not _bytes32(self.kernel_type_id):
            _reject("return-type-id")
        logger.debug("KCS1ReturnTypedNodeV1.__post_init__ exit")


CheckerNodeSyntaxV1: TypeAlias = (
    KCS1EntryNodeV1
    | KCS1ParseNodeV1
    | KCS1InferNodeV1
    | KCS1ReduceNodeV1
    | KCS1CompareTypesNodeV1
    | KCS1ReturnTypedNodeV1
)


@final
@dataclass(frozen=True, slots=True)
class KCS1RunStateV1:
    node: CheckerNodeSyntaxV1
    config: EmptyCheckerConfigV1
    input: CheckerInputSyntaxV1
    ctx: tuple[KernelProofTermV1, ...]
    value_stack: tuple[KernelProofTermV1, ...]
    continuation: tuple[KernelContinuationFrameV1, ...]
    offset: int


@final
@dataclass(frozen=True, slots=True)
class KCS1AcceptStateV1:
    kernel_nf: KernelProofTermV1
    kernel_type_id: bytes


@final
@dataclass(frozen=True, slots=True)
class KCS1RejectStateV1:
    code: KCS1RejectCodeSyntaxV1
    input_offset: int


CheckerStateSyntaxV1: TypeAlias = KCS1RunStateV1 | KCS1AcceptStateV1 | KCS1RejectStateV1


@final
@dataclass(frozen=True, slots=True)
class KCS1NFResultSyntaxV1:
    term: KernelProofTermV1


@final
@dataclass(frozen=True, slots=True)
class KCS1StepResultSyntaxV1:
    term: KernelProofTermV1


ReductionResultSyntaxV1: TypeAlias = KCS1NFResultSyntaxV1 | KCS1StepResultSyntaxV1


@final
@dataclass(frozen=True, slots=True)
class KCS1InputOffsetLocusV1:
    offset: int


@final
@dataclass(frozen=True, slots=True)
class KCS1StateStepLocusV1:
    step: int


@final
@dataclass(frozen=True, slots=True)
class KCS1StructuralCountLocusV1:
    count: int


@final
@dataclass(frozen=True, slots=True)
class KCS1NoLocusV1:
    pass


ResourceLocusSyntaxV1: TypeAlias = (
    KCS1InputOffsetLocusV1 | KCS1StateStepLocusV1 | KCS1StructuralCountLocusV1 | KCS1NoLocusV1
)


@final
@dataclass(frozen=True, slots=True)
class KCS1AttemptResourceSyntaxV1:
    kind: KCS1AttemptResourceKindV1
    allowed: int
    required: int
    locus: ResourceLocusSyntaxV1


@final
@dataclass(frozen=True, slots=True)
class KCS1TerminalAttemptV1:
    state: KCS1AcceptStateV1 | KCS1RejectStateV1


@final
@dataclass(frozen=True, slots=True)
class KCS1ResourceAttemptV1:
    resource: KCS1AttemptResourceSyntaxV1


@final
@dataclass(frozen=True, slots=True)
class KCS1InternalAttemptV1:
    code: KCS1InternalCodeV1
    locus: ResourceLocusSyntaxV1


CheckerAttemptSyntaxV1: TypeAlias = KCS1TerminalAttemptV1 | KCS1ResourceAttemptV1 | KCS1InternalAttemptV1


@final
@dataclass(frozen=True, slots=True)
class KCS1CodecResourceV1:
    kind: KCS1CodecResourceKindV1
    allowed: int
    required: int
    absolute_offset: int


@final
@dataclass(frozen=True, slots=True)
class KCS1IntegrityV1:
    code: KCS1IntegrityCodeV1


@final
@dataclass(frozen=True, slots=True)
class KCS1CodecLimitsV1:
    max_input_bytes: int = 1_048_576
    max_output_bytes: int = 1_048_576
    max_composite_depth: int = 132
    max_composite_nodes: int = 20_000
    max_vector_items: int = 4096
    max_nested_wire_bytes: int = 1_048_576
    max_nested_list_items: int = 4096
    max_nested_nat_bytes: int = 64

    def __post_init__(self) -> None:
        logger.debug("KCS1CodecLimitsV1.__post_init__ entry")
        values = tuple(getattr(self, name) for name in self.__slots__)
        if any(type(value) is not int or not 0 < value < 2**64 for value in values):
            _reject("limits-positive-u64")
        if self.max_composite_depth > 132:
            _reject("limits-safe-depth")
        logger.debug("KCS1CodecLimitsV1.__post_init__ exit")


DEFAULT_KCS1_CODEC_LIMITS_V1 = KCS1CodecLimitsV1()


# These six families are deliberately literal and distinct.  Cross-domain
# equality of ordinals is not cross-domain authority.
class KCN1DecodeCodeV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


class KCS1DecodeCodeV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


class KRR1DecodeCodeV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


class KRL1DecodeCodeV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


class KRF1DecodeCodeV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


class KAR1DecodeCodeV1(IntEnum):
    BAD_VERSION = 0
    BAD_DOMAIN = 1
    BAD_TAG = 2
    BAD_ARITY = 3
    BAD_ORDER = 4
    BAD_LENGTH = 5
    NONCANONICAL_NAT = 6
    NONCANONICAL_INT = 7
    DIGEST_MISMATCH = 8
    DEPENDENCY = 9
    TRAILING = 10


@final
@dataclass(frozen=True, slots=True)
class KCN1DecodeErrorV1:
    code: KCN1DecodeCodeV1
    absolute_offset: int


@final
@dataclass(frozen=True, slots=True)
class KCS1DecodeErrorV1:
    code: KCS1DecodeCodeV1
    absolute_offset: int


@final
@dataclass(frozen=True, slots=True)
class KRR1DecodeErrorV1:
    code: KRR1DecodeCodeV1
    absolute_offset: int


@final
@dataclass(frozen=True, slots=True)
class KRL1DecodeErrorV1:
    code: KRL1DecodeCodeV1
    absolute_offset: int


@final
@dataclass(frozen=True, slots=True)
class KRF1DecodeErrorV1:
    code: KRF1DecodeCodeV1
    absolute_offset: int


@final
@dataclass(frozen=True, slots=True)
class KAR1DecodeErrorV1:
    code: KAR1DecodeCodeV1
    absolute_offset: int


@final
@dataclass(frozen=True, slots=True)
class KCN1DecodedResultV1:
    value: CheckerNodeSyntaxV1
    end: int


@final
@dataclass(frozen=True, slots=True)
class KCS1DecodedResultV1:
    value: CheckerStateSyntaxV1
    end: int


@final
@dataclass(frozen=True, slots=True)
class KRR1DecodedResultV1:
    value: ReductionResultSyntaxV1
    end: int


@final
@dataclass(frozen=True, slots=True)
class KRL1DecodedResultV1:
    value: ResourceLocusSyntaxV1
    end: int


@final
@dataclass(frozen=True, slots=True)
class KRF1DecodedResultV1:
    value: KCS1AttemptResourceSyntaxV1
    end: int


@final
@dataclass(frozen=True, slots=True)
class KAR1DecodedResultV1:
    value: CheckerAttemptSyntaxV1
    end: int


@final
@dataclass(frozen=True, slots=True)
class KCN1DecodeErrorResultV1:
    error: KCN1DecodeErrorV1


@final
@dataclass(frozen=True, slots=True)
class KCS1DecodeErrorResultV1:
    error: KCS1DecodeErrorV1


@final
@dataclass(frozen=True, slots=True)
class KRR1DecodeErrorResultV1:
    error: KRR1DecodeErrorV1


@final
@dataclass(frozen=True, slots=True)
class KRL1DecodeErrorResultV1:
    error: KRL1DecodeErrorV1


@final
@dataclass(frozen=True, slots=True)
class KRF1DecodeErrorResultV1:
    error: KRF1DecodeErrorV1


@final
@dataclass(frozen=True, slots=True)
class KAR1DecodeErrorResultV1:
    error: KAR1DecodeErrorV1


@final
@dataclass(frozen=True, slots=True)
class KCN1CodecResourceResultV1:
    resource: KCS1CodecResourceV1


@final
@dataclass(frozen=True, slots=True)
class KCS1CodecResourceResultV1:
    resource: KCS1CodecResourceV1


@final
@dataclass(frozen=True, slots=True)
class KRR1CodecResourceResultV1:
    resource: KCS1CodecResourceV1


@final
@dataclass(frozen=True, slots=True)
class KRL1CodecResourceResultV1:
    resource: KCS1CodecResourceV1


@final
@dataclass(frozen=True, slots=True)
class KRF1CodecResourceResultV1:
    resource: KCS1CodecResourceV1


@final
@dataclass(frozen=True, slots=True)
class KAR1CodecResourceResultV1:
    resource: KCS1CodecResourceV1


@final
@dataclass(frozen=True, slots=True)
class KCN1IntegrityResultV1:
    error: KCS1IntegrityV1


@final
@dataclass(frozen=True, slots=True)
class KCS1IntegrityResultV1:
    error: KCS1IntegrityV1


@final
@dataclass(frozen=True, slots=True)
class KRR1IntegrityResultV1:
    error: KCS1IntegrityV1


@final
@dataclass(frozen=True, slots=True)
class KRL1IntegrityResultV1:
    error: KCS1IntegrityV1


@final
@dataclass(frozen=True, slots=True)
class KRF1IntegrityResultV1:
    error: KCS1IntegrityV1


@final
@dataclass(frozen=True, slots=True)
class KAR1IntegrityResultV1:
    error: KCS1IntegrityV1


@final
@dataclass(frozen=True, slots=True)
class KCN1EncodedResultV1:
    wire: bytes


@final
@dataclass(frozen=True, slots=True)
class KCS1EncodedResultV1:
    wire: bytes


@final
@dataclass(frozen=True, slots=True)
class KRR1EncodedResultV1:
    wire: bytes


@final
@dataclass(frozen=True, slots=True)
class KRL1EncodedResultV1:
    wire: bytes


@final
@dataclass(frozen=True, slots=True)
class KRF1EncodedResultV1:
    wire: bytes


@final
@dataclass(frozen=True, slots=True)
class KAR1EncodedResultV1:
    wire: bytes


KCN1ParseResultV1: TypeAlias = (
    KCN1DecodedResultV1 | KCN1DecodeErrorResultV1 | KCN1CodecResourceResultV1 | KCN1IntegrityResultV1
)
KCS1ParseResultV1: TypeAlias = (
    KCS1DecodedResultV1 | KCS1DecodeErrorResultV1 | KCS1CodecResourceResultV1 | KCS1IntegrityResultV1
)
KRR1ParseResultV1: TypeAlias = (
    KRR1DecodedResultV1 | KRR1DecodeErrorResultV1 | KRR1CodecResourceResultV1 | KRR1IntegrityResultV1
)
KRL1ParseResultV1: TypeAlias = (
    KRL1DecodedResultV1 | KRL1DecodeErrorResultV1 | KRL1CodecResourceResultV1 | KRL1IntegrityResultV1
)
KRF1ParseResultV1: TypeAlias = (
    KRF1DecodedResultV1 | KRF1DecodeErrorResultV1 | KRF1CodecResourceResultV1 | KRF1IntegrityResultV1
)
KAR1ParseResultV1: TypeAlias = (
    KAR1DecodedResultV1 | KAR1DecodeErrorResultV1 | KAR1CodecResourceResultV1 | KAR1IntegrityResultV1
)
KCN1EncodeResultV1: TypeAlias = KCN1EncodedResultV1 | KCN1CodecResourceResultV1 | KCN1IntegrityResultV1
KCS1EncodeResultV1: TypeAlias = KCS1EncodedResultV1 | KCS1CodecResourceResultV1 | KCS1IntegrityResultV1
KRR1EncodeResultV1: TypeAlias = KRR1EncodedResultV1 | KRR1CodecResourceResultV1 | KRR1IntegrityResultV1
KRL1EncodeResultV1: TypeAlias = KRL1EncodedResultV1 | KRL1CodecResourceResultV1 | KRL1IntegrityResultV1
KRF1EncodeResultV1: TypeAlias = KRF1EncodedResultV1 | KRF1CodecResourceResultV1 | KRF1IntegrityResultV1
KAR1EncodeResultV1: TypeAlias = KAR1EncodedResultV1 | KAR1CodecResourceResultV1 | KAR1IntegrityResultV1

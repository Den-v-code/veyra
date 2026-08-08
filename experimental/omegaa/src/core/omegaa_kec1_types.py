"""Exact public sums, limits and equation bytes for the KEC1 empty calculus."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import logging
from typing import cast
import unicodedata

from .omegaa_kpt1_common import KPT1_MAX_SAFE_DEPTH
from .omegaa_kpt1_types import KernelProofTermV1

logger = logging.getLogger(__name__)


class KEC1ApiV1(IntEnum):
    INFER = 0
    CHECK = 1
    REDUCE_ONE = 2
    WHNF = 3
    NF = 4
    REQUIRE_NORMAL = 5


class KEC1ResultTagV1(IntEnum):
    INFERRED = 0
    CHECKED = 1
    STEP = 2
    NORMAL = 3
    REFUSAL = 4
    RESOURCE = 5
    INTEGRITY = 6


class KEC1RefusalCodeV1(IntEnum):
    UNSCOPED = 0
    EXPECTED_SORT = 1
    EXPECTED_PI = 2
    EXPECTED_SIGMA = 3
    TYPE_MISMATCH = 4
    CANNOT_INFER = 5
    EMPTY_DEPENDENCY = 6
    J_RULE_UNFROZEN = 7
    NOT_NORMAL = 8


class KEC1IntegrityCodeV1(IntEnum):
    HOST_SHAPE = 0
    GRAPH_CYCLE = 1
    GRAPH_SHARED = 2
    TABLE_DRIFT = 3
    SLOT_DRIFT = 4
    ENUM_DRIFT = 5
    CODE_DRIFT = 6
    LIMIT_DRIFT = 7
    CODEC_DRIFT = 8
    MAPPING_DRIFT = 9
    INTERNAL_INVARIANT = 10


class KEC1OriginTagV1(IntEnum):
    CONTEXT = 0
    TERM = 1
    EXPECTED = 2
    SYNTHETIC = 3
    OUTPUT = 4


class KEC1OffsetSpaceV1(IntEnum):
    ORIGIN_FRAME = 0
    KPT_WIRE = 1


class KEC1ResourceKindV1(IntEnum):
    INPUT_BYTES = 0
    INPUT_NODES = 1
    INPUT_DEPTH = 2
    INPUT_LIST_ITEMS = 3
    INPUT_NAT_BYTES = 4
    WORK_DEPTH = 5
    NORMALIZE_STEPS = 6
    GENERATED_DEPTH = 7
    GENERATED_NODES = 8
    GENERATED_BYTES = 9
    GENERATED_LIST_ITEMS = 10
    GENERATED_NAT_BYTES = 11
    OUTPUT_DEPTH = 12
    OUTPUT_NODES = 13
    OUTPUT_BYTES = 14
    OUTPUT_LIST_ITEMS = 15
    OUTPUT_NAT_BYTES = 16


@dataclass(frozen=True, slots=True)
class KEC1OriginV1:
    tag: KEC1OriginTagV1
    index: int

    def __post_init__(self) -> None:
        logger.debug("KEC1OriginV1.__post_init__ entry")
        if (
            type(self) is not KEC1OriginV1
            or type(self.tag) is not KEC1OriginTagV1
            or type(self.index) is not int
            or self.index < 0
        ):
            logger.error("KEC1OriginV1.__post_init__ error shape")
            raise TypeError("invalid KEC1 origin")
        if self.tag not in (KEC1OriginTagV1.CONTEXT, KEC1OriginTagV1.SYNTHETIC) and self.index != 0:
            logger.error("KEC1OriginV1.__post_init__ error index")
            raise ValueError("non-indexed KEC1 origin")
        logger.debug("KEC1OriginV1.__post_init__ exit")


@dataclass(frozen=True, slots=True)
class KEC1LocusV1:
    origin: KEC1OriginV1
    path: tuple[int, ...]
    space: KEC1OffsetSpaceV1
    offset: int

    def __post_init__(self) -> None:
        logger.debug("KEC1LocusV1.__post_init__ entry")
        if (
            type(self) is not KEC1LocusV1
            or type(self.origin) is not KEC1OriginV1
            or type(self.path) is not tuple
            or any(type(x) is not int or x < 0 for x in self.path)
            or type(self.space) is not KEC1OffsetSpaceV1
            or type(self.offset) is not int
            or self.offset < 0
        ):
            logger.error("KEC1LocusV1.__post_init__ error shape")
            raise TypeError("invalid KEC1 locus")
        if self.space is KEC1OffsetSpaceV1.ORIGIN_FRAME and (
            self.offset > 7 or self.origin.tag in (KEC1OriginTagV1.SYNTHETIC, KEC1OriginTagV1.OUTPUT)
        ):
            logger.error("KEC1LocusV1.__post_init__ error frame")
            raise ValueError("invalid KEC1 frame locus")
        logger.debug("KEC1LocusV1.__post_init__ exit")


@dataclass(frozen=True, slots=True)
class KEC1RefusalV1:
    code: KEC1RefusalCodeV1
    locus: KEC1LocusV1

    def __post_init__(self) -> None:
        logger.debug("KEC1RefusalV1.__post_init__ entry")
        if (
            type(self) is not KEC1RefusalV1
            or type(self.code) is not KEC1RefusalCodeV1
            or type(self.locus) is not KEC1LocusV1
        ):
            logger.error("KEC1RefusalV1.__post_init__ error shape")
            raise TypeError("invalid KEC1 refusal")
        logger.debug("KEC1RefusalV1.__post_init__ exit")


@dataclass(frozen=True, slots=True)
class KEC1ResourceV1:
    kind: KEC1ResourceKindV1
    allowed: int
    current: int
    locus: KEC1LocusV1

    def __post_init__(self) -> None:
        logger.debug("KEC1ResourceV1.__post_init__ entry")
        if (
            type(self) is not KEC1ResourceV1
            or type(self.kind) is not KEC1ResourceKindV1
            or type(self.allowed) is not int
            or type(self.current) is not int
            or self.allowed < 0
            or self.current < 0
            or type(self.locus) is not KEC1LocusV1
        ):
            logger.error("KEC1ResourceV1.__post_init__ error shape")
            raise TypeError("invalid KEC1 resource")
        if self.current <= self.allowed:
            logger.error("KEC1ResourceV1.__post_init__ error nonexceeded")
            raise ValueError("non-exceeded KEC1 resource")
        logger.debug("KEC1ResourceV1.__post_init__ exit")


@dataclass(frozen=True, slots=True)
class KEC1IntegrityV1:
    code: KEC1IntegrityCodeV1

    def __post_init__(self) -> None:
        logger.debug("KEC1IntegrityV1.__post_init__ entry")
        if type(self) is not KEC1IntegrityV1 or type(self.code) is not KEC1IntegrityCodeV1:
            logger.error("KEC1IntegrityV1.__post_init__ error shape")
            raise TypeError("invalid KEC1 integrity")
        logger.debug("KEC1IntegrityV1.__post_init__ exit")


_TERM_PAYLOAD_TAGS = frozenset((KEC1ResultTagV1.INFERRED, KEC1ResultTagV1.STEP, KEC1ResultTagV1.NORMAL))


@dataclass(frozen=True, slots=True)
class KEC1ResultV1:
    api: KEC1ApiV1
    tag: KEC1ResultTagV1
    payload: object

    def __post_init__(self) -> None:
        logger.debug("KEC1ResultV1.__post_init__ entry")
        if type(self) is not KEC1ResultV1 or type(self.api) is not KEC1ApiV1 or type(self.tag) is not KEC1ResultTagV1:
            logger.error("KEC1ResultV1.__post_init__ error tag")
            raise TypeError("invalid KEC1 result tag")
        legal = {
            KEC1ApiV1.INFER: {0, 4, 5, 6},
            KEC1ApiV1.CHECK: {1, 4, 5, 6},
            KEC1ApiV1.REDUCE_ONE: {2, 3, 4, 5, 6},
            KEC1ApiV1.WHNF: {3, 4, 5, 6},
            KEC1ApiV1.NF: {3, 4, 5, 6},
            KEC1ApiV1.REQUIRE_NORMAL: {1, 4, 5, 6},
        }
        if int(self.tag) not in legal[self.api]:
            logger.error("KEC1ResultV1.__post_init__ error cross-api")
            raise ValueError("cross-api KEC1 result")
        expected: type[object]
        if self.tag in _TERM_PAYLOAD_TAGS:
            expected = KernelProofTermV1
        elif self.tag is KEC1ResultTagV1.CHECKED:
            if self.payload is not None:
                logger.error("KEC1ResultV1.__post_init__ error checked-payload")
                raise TypeError("checked KEC1 payload must be None")
            logger.debug("KEC1ResultV1.__post_init__ exit checked")
            return
        elif self.tag is KEC1ResultTagV1.REFUSAL:
            expected = KEC1RefusalV1
        elif self.tag is KEC1ResultTagV1.RESOURCE:
            expected = KEC1ResourceV1
        else:
            expected = KEC1IntegrityV1
        if type(self.payload) is not expected:
            logger.error("KEC1ResultV1.__post_init__ error payload")
            raise TypeError("invalid KEC1 payload")
        if self.tag is KEC1ResultTagV1.REFUSAL:
            code = cast(KEC1RefusalV1, self.payload).code
            infer_codes = frozenset(KEC1RefusalCodeV1(i) for i in range(8))
            reduce_codes = frozenset((KEC1RefusalCodeV1.EMPTY_DEPENDENCY, KEC1RefusalCodeV1.J_RULE_UNFROZEN))
            allowed = (
                infer_codes
                if self.api in (KEC1ApiV1.INFER, KEC1ApiV1.CHECK)
                else reduce_codes
                if self.api in (KEC1ApiV1.REDUCE_ONE, KEC1ApiV1.WHNF, KEC1ApiV1.NF)
                else reduce_codes | {KEC1RefusalCodeV1.NOT_NORMAL}
            )
            if code not in allowed:
                logger.error("KEC1ResultV1.__post_init__ error refusal")
                raise ValueError("unreachable KEC1 refusal")
        logger.debug("KEC1ResultV1.__post_init__ exit")


@dataclass(frozen=True, slots=True)
class KEC1LimitsV1:
    max_input_bytes: int = 1_048_576
    max_input_nodes: int = 10_000
    max_input_depth: int = 128
    max_input_list_items: int = 4096
    max_input_nat_bytes: int = 64
    max_work_depth: int = 10_000
    max_normalize_steps: int = 10_000
    max_generated_depth: int = 128
    max_generated_nodes: int = 10_000
    max_generated_bytes: int = 1_048_576
    max_generated_list_items: int = 4096
    max_generated_nat_bytes: int = 64
    max_output_depth: int = 128
    max_output_nodes: int = 10_000
    max_output_bytes: int = 1_048_576
    max_output_list_items: int = 4096
    max_output_nat_bytes: int = 64

    def __post_init__(self) -> None:
        logger.debug("KEC1LimitsV1.__post_init__ entry")
        if type(self) is not KEC1LimitsV1:
            logger.error("KEC1LimitsV1.__post_init__ error class")
            raise TypeError("invalid KEC1 limits class")
        values = tuple(getattr(self, name) for name in self.__slots__)
        if any(type(x) is not int or x <= 0 for x in values):
            logger.error("KEC1LimitsV1.__post_init__ error value")
            raise ValueError("KEC1 limits must be exact positive integers")
        if any(values[i] > KPT1_MAX_SAFE_DEPTH for i in (2, 7, 12)):
            logger.error("KEC1LimitsV1.__post_init__ error depth")
            raise ValueError("KEC1 depth exceeds KPT1 safe depth")
        logger.debug("KEC1LimitsV1.__post_init__ exit")


DEFAULT_KEC1_LIMITS_V1 = KEC1LimitsV1()
ContextV1 = tuple[KernelProofTermV1, ...]


KEC1_EQUATION_ROWS_V1 = (
    "WF:[];A::G if WF(G) and WHNF(Infer(G,A))=Sort(u)",
    "WF-SCHEDULE:outermost-to-innermost;once-public;internal-inherits",
    "QL:0=0;S(u)=S(QL(u));M(u,v)=M(QL(u),QL(v))",
    "I-VAR:k<|G|=>Infer(G,Var(k))=shift(0,k+1,G[k])",
    "I-SORT:Infer(G,Sort(u))=Sort(Succ(u))",
    "I-PI:A=>Sort(u);B=>Sort(v)in A::G;result=Sort(Max(u,v))",
    "I-SIGMA:A=>Sort(u);B=>Sort(v)in A::G;result=Sort(Max(u,v))",
    "I-LAM:A=>Sort(u);Infer(A::G,b)=B;result=Pi(A,B)",
    "I-APP:Infer(G,f)=>Pi(A,B);Check(G,a,A);result=subst0(B,a)",
    "I-FST:Infer(G,p)=>Sigma(A,B);result=A",
    "I-SND:Infer(G,p)=>Sigma(A,B);result=subst0(B,Fst(p))",
    "I-LET:A=>Sort(u);Check(G,v,A);Infer(A::G,b)=B;result=subst0(B,v)",
    "I-EQ:A=>Sort(u);Check(G,x,A);Check(G,y,A);result=Sort(Zero)",
    "I-REFL:Infer(G,x)=A;result=Eq(A,x,x)",
    "CHECK:Infer(expected)=>Sort;E=WHNF(expected);dispatch-once",
    "C-LAM:E=Pi(D,C);A=>Sort;A~=D;Check(A::G,b,C)",
    "C-PAIR:E=Sigma(A,B);Check(G,x,A);Check(G,y,subst0(B,x))",
    "C-GEN:Infer(G,t)=B;B~=expected;premises-left-to-right",
    "U:Const,Ctor,Rec=EMPTY_DEPENDENCY;J=J_RULE_UNFROZEN;PairInfer=CANNOT_INFER",
    "EQ:Codec(NF(left))=Codec(NF(right));unsigned-exact-bytes;left-before-right",
    "SHIFT:cutoff;binders+1;Nat-unbounded;generated-nat-gate",
    "SUBST:k<j:k;k=j:fresh(s);k>j:k-1;binder=(j+1,shift(s))",
    "REDUCE:beta,zeta,fst,snd;root-then-proper-children-left-to-right",
    "WHNF:H=[]|App(H,a)|Fst(H)|Snd(H);NF=repeat-ReduceOne",
    "REQUIRE-NORMAL:n=NF(t);Codec(n)=Codec(t)=>Checked;else NotNormal@Term,root,KptWire,d;d=least-unsigned-difference-or-min-length",
    "RESULT:Infer=Inferred|Refusal|Resource|Integrity;Check=Checked|Refusal|Resource|Integrity;Reduce=Step|Normal|Refusal|Resource|Integrity;Whnf,Nf=Normal|Refusal|Resource|Integrity;RequireNormal=Checked|Refusal|Resource|Integrity",
    "PUBLIC:Infer(G,t,L=D);Check(G,t,A,L=D);ReduceOne(t,L=D);Whnf(t,L=D);Nf(t,L=D);RequireNormal(t,L=D)",
    "DEFAULT:(1048576,10000,128,4096,64,10000,10000,128,10000,1048576,4096,64,128,10000,1048576,4096,64);same-object-six-defaults",
    "REACHABLE:Infer,Check=0,1,2,3,4,5,6,7;ReduceOne,Whnf,Nf=6,7;RequireNormal=6,7,8",
    "REFUSAL:0..8=UNSCOPED,EXPECTED_SORT,EXPECTED_PI,EXPECTED_SIGMA,TYPE_MISMATCH,CANNOT_INFER,EMPTY_DEPENDENCY,J_RULE_UNFROZEN,NOT_NORMAL",
    "REFUSAL-LOCUS:outer-tag|type-subject|demanding-tag|checked-term|retained-premise",
    "INTEGRITY:0..10=HOST_SHAPE,GRAPH_CYCLE,GRAPH_SHARED,TABLE_DRIFT,SLOT_DRIFT,ENUM_DRIFT,CODE_DRIFT,LIMIT_DRIFT,CODEC_DRIFT,MAPPING_DRIFT,INTERNAL_INVARIANT",
    "RESOURCE:0..16=INPUT_BYTES,INPUT_NODES,INPUT_DEPTH,INPUT_LIST_ITEMS,INPUT_NAT_BYTES,WORK_DEPTH,NORMALIZE_STEPS,GENERATED_DEPTH,GENERATED_NODES,GENERATED_BYTES,GENERATED_LIST_ITEMS,GENERATED_NAT_BYTES,OUTPUT_DEPTH,OUTPUT_NODES,OUTPUT_BYTES,OUTPUT_LIST_ITEMS,OUTPUT_NAT_BYTES",
    "RESOURCE-ORDER:integrity;input-ordinal;event;step;generated-ordinal;output-ordinal",
    "INPUT:origins-outer-context-first;Frame=U64BE(len)||KPT;bytes,nodes,depth,list,nat",
    "PREFLIGHT:hard-safe-uncharged-cursor;one-child;no-work|normalize|generated",
    "WORK:semantic-WF|Infer|Check|Head|Reduce|Rebuild|Output;prospective-stack;push-reversed",
    "GENERATED:prospective-before-allocation;origin=production-ordinal;node+=1;bytes+=candidate-wire;depth,list,nat=candidate-max",
    "OUTPUT:depth,nodes,bytes,list,nat;origin=OUTPUT;gate-before-result-wrapper",
    "KPT-MAP:(b,n,d,l,m)->Limits(max(1,b),max(1,b),max(1,d),max(1,n),max(1,l),max(1,m))",
    "LOCUS:Origin(tag,index);Path(child-ordinals);Space(frame|kpt);Offset(Nat)",
    "TRANSPORT:A~=D then Check(A::G,b,C);C unchanged;no evidence object",
    "AUTHORITY:none;soundness,normalization,consistency,checker,registry,basis,admission=open",
)


def _u64(value: int) -> bytes:
    logger.debug("_u64 entry")
    if type(value) is not int or not 0 <= value < 2**64:
        logger.error("_u64 error range")
        raise ValueError("KEC1 U64 range")
    result = value.to_bytes(8, "big")
    logger.debug("_u64 exit")
    return result


def _frame(value: bytes) -> bytes:
    logger.debug("_frame entry bytes=%d", len(value))
    result = _u64(len(value)) + value
    logger.debug("_frame exit")
    return result


def _equation_bytes() -> bytes:
    logger.debug("_equation_bytes entry")
    rows: list[bytes] = []
    for row in KEC1_EQUATION_ROWS_V1:
        if type(row) is not str or unicodedata.normalize("NFC", row) != row or not row.isascii():
            logger.error("_equation_bytes error row")
            raise ValueError("KEC1 equation row")
        rows.append(_frame(row.encode("utf-8")))
    if len(rows) != 43:
        logger.error("_equation_bytes error count")
        raise ValueError("KEC1 equation count")
    result = b"KEC1EQ\x00" + _u64(43) + b"".join(rows)
    logger.debug("_equation_bytes exit bytes=%d", len(result))
    return result


KEC1_EQUATION_BYTES_V1 = _equation_bytes()

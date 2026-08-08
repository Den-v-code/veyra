"""Reference VAM v0.2 interpreter."""
from __future__ import annotations

import logging
import json
from typing import Any, Sequence

from .assembly import parse_vmasm
from .model import Instruction, VamExecutionError, VamObject, VamState

logger = logging.getLogger(__name__)


def obstruction(claim: str, witness: Any) -> VamObject:
    """Build an obstruction object instead of silently coercing invalid claims."""
    logger.debug("obstruction claim=%s witness_type=%s", claim, type(witness).__name__)
    return VamObject("Obstruction", {"claim": claim, "witness": witness})


def _is_reg(arg: Any) -> bool:
    return isinstance(arg, str) and arg.startswith("%r")


def _resolve(state: VamState, arg: Any) -> VamObject:
    if _is_reg(arg) and arg in state.registers:
        return state.registers[arg]
    if _is_reg(arg):
        return obstruction("missing-register", arg)
    return VamObject("Literal", {"value": arg})


def _expect(obj: VamObject, kind: str, claim: str) -> VamObject | None:
    if obj.kind == kind:
        return None
    return obstruction(claim, {"expected": kind, "actual": obj.kind})


def _shadow(obj: VamObject, obs: VamObject) -> VamObject:
    logger.debug("shadow entry kind=%s observer_kind=%s", obj.kind, obs.kind)
    if obs.kind != "Observer":
        result = obstruction("observe-requires-observer", obs.kind)
        logger.error("shadow blocked result=%r", result); return result
    kind = obs.field("kind")
    if kind == "length":
        value = _length_shadow(obj)
    elif kind == "kind":
        value = obj.kind.lower()
    elif kind == "label":
        value = _label_shadow(obj)
    elif kind == "trace":
        value = _trace_shadow(obj)
    elif kind == "boundary":
        value = _boundary_shadow(obj)
    else:
        value = repr(obj.data)
    result = VamObject("Shadow", {"observer": kind, "value": value, "source_kind": obj.kind})
    logger.debug("shadow exit result=%r", result); return result


def _length_shadow(obj: VamObject) -> int:
    logger.debug("length_shadow entry kind=%s", obj.kind)
    if obj.kind == "Breath":
        result = len(obj.field("tacts", ()))
    elif obj.kind == "Mode":
        result = _length_shadow(obj.field("breath"))
    else:
        result = 1
    logger.debug("length_shadow exit result=%d", result)
    return result


def _label_shadow(obj: VamObject) -> str | None:
    logger.debug("label_shadow entry kind=%s", obj.kind)
    if obj.kind in {"Rez", "Nod", "Tact"}:
        result = obj.field("label")
    elif obj.kind == "Observer":
        result = obj.field("kind")
    else:
        result = "unlabelled"
    logger.debug("label_shadow exit result=%r", result)
    return result


def _trace_shadow(obj: VamObject) -> str:
    logger.debug("trace_shadow entry kind=%s", obj.kind)
    result = json.dumps(_stable_native(obj), ensure_ascii=False, separators=(",", ":")) if obj.kind in {"Rez", "Nod", "Tact", "Breath", "Mode", "Observer"} else obj.kind
    logger.debug("trace_shadow exit result=%s", result)
    return result


def _boundary_shadow(obj: VamObject) -> tuple[object, ...] | str:
    logger.debug("boundary_shadow entry kind=%s", obj.kind)
    if obj.kind == "Tact":
        result: tuple[object, ...] | str = ("tact", _nod_key(obj.field("left")), _nod_key(obj.field("right")))
    elif obj.kind == "Breath" and obj.field("tacts"):
        tacts = obj.field("tacts")
        result = ("breath", _nod_key(tacts[0].field("left")), _nod_key(tacts[-1].field("right")))
    elif obj.kind == "Mode":
        result = ("mode", _boundary_shadow(obj.field("breath")), obj.field("observer", "native-cycle"))
    elif obj.kind == "Nod":
        result = ("nod", _nod_key(obj))
    elif obj.kind == "Rez":
        result = ("rez", obj.field("label"))
    elif obj.kind == "Observer":
        result = ("observer", obj.field("kind"))
    else:
        result = "opaque"
    logger.debug("boundary_shadow exit result=%r", result)
    return result


def _nod_key(obj: VamObject) -> str:
    logger.debug("nod_key entry kind=%s", obj.kind)
    residue = obj.field("rez"); name = residue.field("label") if isinstance(residue, VamObject) else "unknown"
    result = f"{name}:{obj.field('label')}"
    logger.debug("nod_key exit result=%s", result); return result


def _stable_native(obj: VamObject) -> object:
    logger.debug("stable_native entry kind=%s", obj.kind)
    if obj.kind == "Rez": result: object = ["rez", obj.field("label")]
    elif obj.kind == "Nod": result = ["nod", _stable_native(obj.field("rez")), obj.field("label")]
    elif obj.kind == "Tact": result = ["tact", _stable_native(obj.field("left")), _stable_native(obj.field("right")), obj.field("label")]
    elif obj.kind == "Breath": result = ["breath", *[_stable_native(item) for item in obj.field("tacts", ())]]
    elif obj.kind == "Mode": result = ["mode", _stable_native(obj.field("breath")), obj.field("observer", "native-cycle")]
    elif obj.kind == "Observer": result = ["observer", obj.field("kind")]
    else: result = ["unknown", repr(obj)]
    logger.debug("stable_native exit kind=%s", obj.kind); return result


def _execute_instruction(state: VamState, inst: Instruction) -> None:
    op, args = inst.op, inst.args
    if not args or not _is_reg(args[0]):
        logger.error("execute instruction invalid_dst line=%s op=%s", inst.line, op)
        raise VamExecutionError(f"line {inst.line}: first operand must be destination register")
    dst = args[0]
    rest = args[1:]
    logger.debug("execute instruction pc=%d op=%s dst=%s argc=%d", state.pc, op, dst, len(rest))
    obj = _dispatch(state, op, rest)
    state.put(dst, obj, op, _detail(obj))


def _dispatch(state: VamState, op: str, args: tuple[Any, ...]) -> VamObject:
    logger.debug("dispatch entry op=%s argc=%d", op, len(args))
    if op == "REZ" and len(args) == 1:
        return VamObject("Rez", {"label": args[0]})
    if op == "NOD" and len(args) == 2:
        rez = _resolve(state, args[0])
        return _expect(rez, "Rez", "nod-requires-rez") or VamObject("Nod", {"rez": rez, "label": args[1]})
    if op == "TACT" and len(args) == 3:
        left, right = _resolve(state, args[0]), _resolve(state, args[1])
        bad = _expect(left, "Nod", "tact-left") or _expect(right, "Nod", "tact-right")
        return bad or VamObject("Tact", {"left": left, "right": right, "label": args[2]})
    if op == "BREATH" and args:
        tacts = tuple(_resolve(state, arg) for arg in args)
        bad = next((_expect(tact, "Tact", "breath-requires-tacts") for tact in tacts if tact.kind != "Tact"), None)
        return bad or VamObject("Breath", {"tacts": tacts})
    if op == "MODE" and len(args) == 1:
        breath = _resolve(state, args[0])
        return _expect(breath, "Breath", "mode-requires-breath") or VamObject("Mode", {"breath": breath})
    if op == "OBSERVER" and len(args) == 1:
        return VamObject("Observer", {"kind": args[0]})
    if op == "OBSERVE" and len(args) == 2:
        return _shadow(_resolve(state, args[0]), _resolve(state, args[1]))
    if op == "ECHO" and len(args) == 3:
        left, right, obs = (_resolve(state, args[0]), _resolve(state, args[1]), _resolve(state, args[2]))
        left_s, right_s = _shadow(left, obs), _shadow(right, obs)
        passed = left_s.kind == right_s.kind == "Shadow" and left_s.field("value") == right_s.field("value")
        return VamObject("Echo", {"passed": passed, "left": left_s, "right": right_s, "observer": obs.field("kind")})
    if op == "OBSTRUCT" and len(args) == 2:
        return obstruction(str(args[0]), _resolve(state, args[1]).data)
    if op == "COMPRESS" and len(args) == 2:
        shadow = _shadow(_resolve(state, args[0]), _resolve(state, args[1]))
        return VamObject("Compressed", {"shadow": shadow, "observer": shadow.field("observer"), "lossless": True})
    if op == "CERT" and len(args) == 3:
        evidence = _resolve(state, args[1])
        accepted = evidence.kind == "Echo" and evidence.field("passed") is True
        return VamObject("Certificate", {"claim": args[0], "evidence": evidence, "boundary": args[2], "accepted": accepted})
    logger.error("dispatch unsupported op=%s argc=%d", op, len(args) + 1)
    raise VamExecutionError(f"unsupported or malformed instruction: {op}/{len(args) + 1}")


def _detail(obj: VamObject) -> str:
    if obj.kind == "Echo":
        return f"passed={obj.field('passed')} observer={obj.field('observer')}"
    if obj.kind == "Certificate":
        return f"claim={obj.field('claim')} accepted={obj.field('accepted')}"
    if obj.kind == "Obstruction":
        return f"claim={obj.field('claim')}"
    return obj.kind


def execute(program: Sequence[Instruction]) -> VamState:
    """Execute a parsed VAM program deterministically."""
    logger.debug("execute entry instructions=%d", len(program))
    state = VamState()
    for pc, inst in enumerate(program):
        state.pc = pc
        _execute_instruction(state, inst)
    state.pc = len(program)
    logger.debug("execute exit trace=%d certs=%d obstructions=%d", len(state.trace), len(state.certs), len(state.obstructions))
    return state


def execute_with_definition_objects(program: Sequence[Instruction]) -> tuple[VamState, dict[int, VamObject]]:
    """Execute once and capture each destination object's post-instruction value."""
    logger.debug("execute_with_definition_objects entry instructions=%d", len(program))
    state = VamState()
    objects: dict[int, VamObject] = {}
    for pc, inst in enumerate(program):
        state.pc = pc
        _execute_instruction(state, inst)
        if inst.args and _is_reg(inst.args[0]):
            objects[pc] = state.registers[inst.args[0]]
    state.pc = len(program)
    logger.debug(
        "execute_with_definition_objects exit trace=%d definitions=%d obstructions=%d",
        len(state.trace),
        len(objects),
        len(state.obstructions),
    )
    return state, objects


def run_vmasm(source: str) -> VamState:
    """Parse and execute VAM assembly text."""
    logger.debug("run_vmasm entry chars=%d", len(source))
    state = execute(parse_vmasm(source))
    logger.debug("run_vmasm exit certs=%d obstructions=%d", len(state.certs), len(state.obstructions))
    return state

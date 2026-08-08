use std::collections::BTreeMap;

use crate::{Instruction, WireArg};

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) struct AbstractObject {
    pub kind: &'static str,
    pub contains_obstruction: bool,
    pub observer_kind: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) struct ProgramAnalysis {
    pub by_index: Vec<Option<AbstractObject>>,
    pub by_reg: BTreeMap<i64, AbstractObject>,
}

pub(super) fn analyze_program(program: &[Instruction]) -> ProgramAnalysis {
    let mut by_index = Vec::with_capacity(program.len());
    let mut by_reg = BTreeMap::new();
    for inst in program {
        let obj = abstract_dispatch(inst, &by_reg);
        if let Some(id) = dst(inst) {
            by_reg.insert(id, obj.clone());
            by_index.push(Some(obj));
        } else {
            by_index.push(None);
        }
    }
    ProgramAnalysis { by_index, by_reg }
}

fn abstract_dispatch(inst: &Instruction, regs: &BTreeMap<i64, AbstractObject>) -> AbstractObject {
    match (inst.op.as_str(), inst.args.len().saturating_sub(1)) {
        ("REZ", 1) => object("Rez", false),
        ("NOD", 2) => {
            let rez = resolve(&inst.args[1], regs);
            if rez.kind != "Rez" {
                obstruction()
            } else {
                object("Nod", rez.contains_obstruction)
            }
        }
        ("TACT", 3) => {
            let left = resolve(&inst.args[1], regs);
            let right = resolve(&inst.args[2], regs);
            if left.kind != "Nod" || right.kind != "Nod" {
                obstruction()
            } else {
                object(
                    "Tact",
                    left.contains_obstruction || right.contains_obstruction,
                )
            }
        }
        ("BREATH", n) if n > 0 => abstract_breath(inst, regs),
        ("MODE", 1) => {
            let breath = resolve(&inst.args[1], regs);
            if breath.kind != "Breath" {
                obstruction()
            } else {
                object("Mode", breath.contains_obstruction)
            }
        }
        ("OBSERVER", 1) => AbstractObject {
            kind: "Observer",
            contains_obstruction: false,
            observer_kind: Some(wire_text(&inst.args[1])),
        },
        ("OBSERVE", 2) => shadow(&resolve(&inst.args[1], regs), &resolve(&inst.args[2], regs)),
        ("ECHO", 3) => {
            let left = shadow(&resolve(&inst.args[1], regs), &resolve(&inst.args[3], regs));
            let right = shadow(&resolve(&inst.args[2], regs), &resolve(&inst.args[3], regs));
            object(
                "Echo",
                left.contains_obstruction || right.contains_obstruction,
            )
        }
        ("OBSTRUCT", 2) => obstruction(),
        ("COMPRESS", 2) => {
            let shadow = shadow(&resolve(&inst.args[1], regs), &resolve(&inst.args[2], regs));
            object("Compressed", shadow.contains_obstruction)
        }
        ("CERT", 3) => {
            let evidence = resolve(&inst.args[2], regs);
            object("Certificate", evidence.contains_obstruction)
        }
        _ => obstruction(),
    }
}

fn abstract_breath(inst: &Instruction, regs: &BTreeMap<i64, AbstractObject>) -> AbstractObject {
    let mut contains = false;
    for item in inst.args.iter().skip(1).map(|arg| resolve(arg, regs)) {
        if item.kind != "Tact" {
            return obstruction();
        }
        contains |= item.contains_obstruction;
    }
    object("Breath", contains)
}

fn resolve(arg: &WireArg, regs: &BTreeMap<i64, AbstractObject>) -> AbstractObject {
    match arg {
        WireArg::Reg(id) => regs.get(id).cloned().unwrap_or_else(obstruction),
        _ => object("Literal", false),
    }
}

fn shadow(_src: &AbstractObject, observer: &AbstractObject) -> AbstractObject {
    if observer.kind != "Observer" {
        obstruction()
    } else {
        object("Shadow", false)
    }
}

fn object(kind: &'static str, contains_obstruction: bool) -> AbstractObject {
    AbstractObject {
        kind,
        contains_obstruction,
        observer_kind: None,
    }
}

fn obstruction() -> AbstractObject {
    object("Obstruction", true)
}

fn dst(inst: &Instruction) -> Option<i64> {
    match inst.args.first() {
        Some(WireArg::Reg(id)) => Some(*id),
        _ => None,
    }
}

fn wire_text(arg: &WireArg) -> String {
    match arg {
        WireArg::Int(v) => v.to_string(),
        WireArg::Reg(id) => format!("%r{id}"),
        WireArg::Str(s) => s.clone(),
    }
}

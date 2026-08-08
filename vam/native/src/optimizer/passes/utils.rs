use std::collections::{BTreeMap, BTreeSet};

use crate::optimizer::analysis::ProgramAnalysis;
use crate::optimizer::OptimizationRow;
use crate::{Instruction, WireArg};

pub(super) fn same_observer_use_reason(
    id: i64,
    observer: i64,
    use_map: &BTreeMap<i64, Vec<(usize, Instruction)>>,
    after: usize,
) -> Option<String> {
    let mut saw = false;
    for (_, inst) in use_map
        .get(&id)
        .into_iter()
        .flat_map(|r| r.iter())
        .filter(|(i, _)| *i > after)
    {
        saw = true;
        for (pos, arg) in inst.args.iter().enumerate().skip(1) {
            if arg_reg(arg) != Some(id) {
                continue;
            }
            match inst.op.as_str() {
                "OBSERVE" | "COMPRESS"
                    if inst.args.len() == 3
                        && pos == 1
                        && arg_reg(&inst.args[2]) == Some(observer) => {}
                "OBSERVE" | "COMPRESS" => {
                    return Some(format!(
                        "{} used outside same-observer {}",
                        reg(id),
                        inst.op
                    ))
                }
                "ECHO"
                    if inst.args.len() == 4
                        && matches!(pos, 1 | 2)
                        && arg_reg(&inst.args[3]) == Some(observer) => {}
                "ECHO" => return Some(format!("{} used outside same-observer ECHO", reg(id))),
                "OBSTRUCT" => return Some("candidate feeds OBSTRUCT evidence boundary".into()),
                "CERT" => return Some("candidate feeds CERT directly".into()),
                _ => return Some(format!("unsupported use {}", inst.op)),
            }
        }
    }
    if saw {
        None
    } else {
        Some("unused candidate is handled by dead-shadow".into())
    }
}

pub(super) fn rewired(inst: &Instruction, aliases: &BTreeMap<i64, i64>) -> Instruction {
    Instruction {
        op: inst.op.clone(),
        args: rewrite_args(&inst.args, aliases),
        line: inst.line,
    }
}

fn rewrite_args(args: &[WireArg], aliases: &BTreeMap<i64, i64>) -> Vec<WireArg> {
    args.iter()
        .enumerate()
        .map(|(i, a)| match (i, a) {
            (0, _) => a.clone(),
            (_, WireArg::Reg(id)) => WireArg::Reg(*aliases.get(id).unwrap_or(id)),
            _ => a.clone(),
        })
        .collect()
}

pub(super) fn definition_counts(program: &[Instruction]) -> BTreeMap<i64, usize> {
    let mut counts = BTreeMap::new();
    for inst in program {
        if let Some(id) = dst(inst) {
            *counts.entry(id).or_insert(0) += 1;
        }
    }
    counts
}

pub(super) fn use_contexts(program: &[Instruction]) -> BTreeMap<i64, Vec<(usize, Instruction)>> {
    let mut uses: BTreeMap<i64, Vec<(usize, Instruction)>> = BTreeMap::new();
    for (index, inst) in program.iter().enumerate() {
        for id in used_regs(inst) {
            uses.entry(id).or_default().push((index, inst.clone()));
        }
    }
    uses
}

pub(super) fn compress_defs(program: &[Instruction]) -> BTreeMap<i64, (i64, i64, usize)> {
    let mut defs = BTreeMap::new();
    for (index, inst) in program.iter().enumerate() {
        if inst.op == "COMPRESS" && inst.args.len() == 3 {
            if let (Some(a), Some(b), Some(c)) =
                (dst(inst), arg_reg(&inst.args[1]), arg_reg(&inst.args[2]))
            {
                defs.insert(a, (b, c, index));
            }
        }
    }
    defs
}

pub(super) fn has_single_definition(reg_id: i64, counts: &BTreeMap<i64, usize>) -> bool {
    counts.get(&reg_id).copied().unwrap_or(0) == 1
}

pub(super) fn used_regs(inst: &Instruction) -> BTreeSet<i64> {
    inst.args.iter().skip(1).filter_map(arg_reg).collect()
}

pub(super) fn contains_obstruction_at(analysis: &ProgramAnalysis, index: usize) -> bool {
    analysis
        .by_index
        .get(index)
        .and_then(Option::as_ref)
        .is_some_and(|obj| obj.contains_obstruction)
}

pub(super) fn dst(inst: &Instruction) -> Option<i64> {
    match inst.args.first() {
        Some(WireArg::Reg(id)) => Some(*id),
        _ => None,
    }
}

pub(super) fn arg_reg(arg: &WireArg) -> Option<i64> {
    match arg {
        WireArg::Reg(id) => Some(*id),
        _ => None,
    }
}

pub(super) fn wire_text(arg: &WireArg) -> String {
    match arg {
        WireArg::Int(v) => v.to_string(),
        WireArg::Reg(id) => reg(*id),
        WireArg::Str(s) => s.clone(),
    }
}

pub(super) fn reg(id: i64) -> String {
    format!("%r{id}")
}

pub(super) fn row(
    pass_name: &'static str,
    action: &'static str,
    detail: String,
    accepted: bool,
) -> OptimizationRow {
    OptimizationRow {
        pass_name,
        action,
        detail,
        accepted,
    }
}

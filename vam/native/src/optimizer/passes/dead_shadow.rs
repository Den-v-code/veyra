use std::collections::BTreeSet;

use super::utils::{
    contains_obstruction_at, definition_counts, dst, has_single_definition, reg, row, used_regs,
};
use crate::optimizer::analysis::analyze_program;
use crate::optimizer::OptimizationRow;
use crate::Instruction;

pub(crate) fn dead_shadow_pass(
    program: &[Instruction],
) -> (Vec<Instruction>, Vec<OptimizationRow>) {
    let counts = definition_counts(program);
    let analysis = analyze_program(program);
    let mut live: BTreeSet<i64> = BTreeSet::new();
    let mut output = Vec::with_capacity(program.len());
    let mut rows = Vec::new();
    for (index, inst) in program.iter().enumerate().rev() {
        let inst_dst = dst(inst);
        let removable = inst_dst.is_some()
            && !live.contains(&inst_dst.expect("checked"))
            && matches!(inst.op.as_str(), "OBSERVE" | "COMPRESS");
        if removable {
            let id = inst_dst.expect("checked");
            if !has_single_definition(id, &counts) {
                rows.push(row(
                    "dead-shadow",
                    "reject",
                    format!("keep {}: multiple definitions", reg(id)),
                    false,
                ));
            } else if contains_obstruction_at(&analysis, index) {
                rows.push(row(
                    "dead-shadow",
                    "reject",
                    format!("keep {}: obstruction would be erased", reg(id)),
                    false,
                ));
            } else {
                rows.push(row(
                    "dead-shadow",
                    "remove",
                    format!("drop unused {} {}", inst.op, reg(id)),
                    true,
                ));
                live.extend(used_regs(inst));
                continue;
            }
        }
        output.push(inst.clone());
        if let Some(id) = inst_dst {
            if !matches!(inst.op.as_str(), "CERT" | "OBSTRUCT" | "ECHO") {
                live.remove(&id);
            }
        }
        live.extend(used_regs(inst));
    }
    output.reverse();
    (output, rows)
}

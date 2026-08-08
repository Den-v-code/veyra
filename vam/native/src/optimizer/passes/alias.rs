use std::collections::BTreeMap;

use super::utils::{definition_counts, dst, reg, rewired, row, wire_text};
use crate::optimizer::OptimizationRow;
use crate::Instruction;

pub(crate) fn observer_alias_pass(
    program: &[Instruction],
) -> (Vec<Instruction>, Vec<OptimizationRow>) {
    let counts = definition_counts(program);
    let mut aliases: BTreeMap<i64, i64> = BTreeMap::new();
    let mut observer_by_kind: BTreeMap<String, i64> = BTreeMap::new();
    let mut output = Vec::with_capacity(program.len());
    let mut rows = Vec::new();
    for inst in program {
        let current = rewired(inst, &aliases);
        let current_dst = dst(&current);
        if current.op == "OBSERVER" && current_dst.is_some() && current.args.len() == 2 {
            let id = current_dst.expect("checked");
            if counts.get(&id).copied().unwrap_or(0) == 1 {
                let kind = wire_text(&current.args[1]);
                if let Some(prior) = observer_by_kind.get(&kind).copied() {
                    aliases.insert(id, prior);
                    rows.push(row(
                        "observer-alias",
                        "remove",
                        format!("{}->{} kind={kind}", reg(id), reg(prior)),
                        true,
                    ));
                    continue;
                }
                observer_by_kind.insert(kind, id);
            }
        }
        output.push(current);
    }
    (output, rows)
}

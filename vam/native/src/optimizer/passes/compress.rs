use std::collections::BTreeMap;

use super::utils::{
    arg_reg, compress_defs, contains_obstruction_at, definition_counts, dst, has_single_definition,
    reg, rewired, row, same_observer_use_reason, use_contexts,
};
use crate::optimizer::analysis::{analyze_program, ProgramAnalysis};
use crate::optimizer::OptimizationRow;
use crate::Instruction;

const IDEMPOTENT_OBSERVER_KINDS: &[&str] = &["boundary", "kind", "label", "length", "trace"];

pub(crate) fn compress_alias_pass(
    program: &[Instruction],
) -> (Vec<Instruction>, Vec<OptimizationRow>) {
    let counts = definition_counts(program);
    let analysis = analyze_program(program);
    let mut aliases: BTreeMap<i64, i64> = BTreeMap::new();
    let mut compress_by_pair: BTreeMap<(i64, i64), (i64, usize)> = BTreeMap::new();
    let mut output = Vec::with_capacity(program.len());
    let mut rows = Vec::new();
    for (index, inst) in program.iter().enumerate() {
        let current = rewired(inst, &aliases);
        let Some(id) = dst(&current) else {
            output.push(current);
            continue;
        };
        if current.op != "COMPRESS" || current.args.len() != 3 {
            output.push(current);
            continue;
        }
        let (Some(source), Some(observer)) = (arg_reg(&current.args[1]), arg_reg(&current.args[2]))
        else {
            output.push(current);
            continue;
        };
        if let Some((prior_dst, prior_index)) = compress_by_pair.get(&(source, observer)).copied() {
            let safe_defs = [id, prior_dst, source, observer]
                .into_iter()
                .all(|r| has_single_definition(r, &counts));
            let safe_objects = !contains_obstruction_at(&analysis, index)
                && !contains_obstruction_at(&analysis, prior_index);
            if safe_defs && safe_objects {
                aliases.insert(id, prior_dst);
                rows.push(row(
                    "compress-alias",
                    "remove",
                    format!(
                        "{}->{} source={} observer={}",
                        reg(id),
                        reg(prior_dst),
                        reg(source),
                        reg(observer)
                    ),
                    true,
                ));
                continue;
            }
            let reason = if safe_defs {
                "obstruction would be erased"
            } else {
                "multiple definitions"
            };
            rows.push(row(
                "compress-alias",
                "reject",
                format!("keep {}: {reason}", reg(id)),
                false,
            ));
        } else {
            compress_by_pair.insert((source, observer), (id, index));
        }
        output.push(current);
    }
    (output, rows)
}

pub(crate) fn compress_idempotent_pass(
    program: &[Instruction],
) -> (Vec<Instruction>, Vec<OptimizationRow>) {
    let counts = definition_counts(program);
    let analysis = analyze_program(program);
    let use_map = use_contexts(program);
    let defs = compress_defs(program);
    let mut aliases: BTreeMap<i64, i64> = BTreeMap::new();
    let mut output = Vec::with_capacity(program.len());
    let mut rows = Vec::new();
    for (index, inst) in program.iter().enumerate() {
        let current = rewired(inst, &aliases);
        let Some(id) = dst(&current) else {
            output.push(current);
            continue;
        };
        if current.op != "COMPRESS" || current.args.len() != 3 {
            output.push(current);
            continue;
        }
        let (Some(source), Some(observer)) = (arg_reg(&current.args[1]), arg_reg(&current.args[2]))
        else {
            output.push(current);
            continue;
        };
        let Some((prior_source, prior_observer, _)) = defs.get(&source).copied() else {
            output.push(current);
            continue;
        };
        if prior_observer != observer {
            rows.push(row(
                "compress-idempotent",
                "reject",
                format!(
                    "keep {}: observer differs source={} observer={} prior={}",
                    reg(id),
                    reg(source),
                    reg(observer),
                    reg(prior_observer)
                ),
                false,
            ));
            output.push(current);
            continue;
        }
        if let Some(reason) = idempotent_reject_reason(
            id,
            source,
            observer,
            prior_source,
            &counts,
            &analysis,
            &use_map,
            index,
        ) {
            rows.push(row(
                "compress-idempotent",
                "reject",
                format!("keep {}: {reason}", reg(id)),
                false,
            ));
            output.push(current);
            continue;
        }
        aliases.insert(id, source);
        rows.push(row(
            "compress-idempotent",
            "remove",
            format!(
                "{}->{} prior_source={} observer={} reason=same-observer-visible",
                reg(id),
                reg(source),
                reg(prior_source),
                reg(observer)
            ),
            true,
        ));
    }
    (output, rows)
}

#[allow(clippy::too_many_arguments)]
fn idempotent_reject_reason(
    id: i64,
    source: i64,
    observer: i64,
    prior_source: i64,
    counts: &BTreeMap<i64, usize>,
    analysis: &ProgramAnalysis,
    use_map: &BTreeMap<i64, Vec<(usize, Instruction)>>,
    index: usize,
) -> Option<String> {
    if ![id, source, observer, prior_source]
        .into_iter()
        .all(|r| has_single_definition(r, counts))
    {
        return Some("multiple definitions".into());
    }
    let (Some(target), Some(src), Some(candidate)) = (
        analysis.by_reg.get(&prior_source),
        analysis.by_reg.get(&source),
        analysis.by_reg.get(&id),
    ) else {
        return Some("missing definition object".into());
    };
    if target.contains_obstruction {
        return Some("compression target obstruction would be hidden".into());
    }
    if src.contains_obstruction || candidate.contains_obstruction {
        return Some("nested obstruction would be erased".into());
    }
    let Some(observer_obj) = analysis.by_reg.get(&observer) else {
        return Some("observer missing or malformed".into());
    };
    if observer_obj.kind != "Observer" {
        return Some("observer missing or malformed".into());
    }
    let kind = observer_obj.observer_kind.as_deref().unwrap_or("");
    if !IDEMPOTENT_OBSERVER_KINDS.contains(&kind) {
        return Some(format!("observer kind '{kind}' lacks idempotent contract"));
    }
    same_observer_use_reason(id, observer, use_map, index)
}

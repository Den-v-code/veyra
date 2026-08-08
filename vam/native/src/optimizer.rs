mod analysis;
mod passes;
#[cfg(test)]
mod tests;

use crate::json::{push_json_string, semantic_report_json};
use crate::{FrameReport, VamError};
use passes::{
    compress_alias_pass, compress_idempotent_pass, dead_shadow_pass, observer_alias_pass,
};

const CONTRACT: &str = "native-optimizer-parity-v1";
const SLICE: &str = "observer-alias-v1";

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OptimizationRow {
    pub pass_name: &'static str,
    pub action: &'static str,
    pub detail: String,
    pub accepted: bool,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OptimizationReport {
    pub contract: &'static str,
    pub slice: &'static str,
    pub original: FrameReport,
    pub optimized: FrameReport,
    pub rows: Vec<OptimizationRow>,
}

pub struct OptimizedFrameEmission<'a> {
    pub magic: &'static str,
    pub version: u16,
    pub boundary: &'static str,
    pub path: &'a str,
    pub bytes: usize,
    pub payload_len: usize,
    pub instruction_count: usize,
    pub crc32: u32,
}

pub fn optimize_observer_alias(report: &FrameReport) -> Result<OptimizationReport, VamError> {
    if !matches!(report.magic, "VAM0" | "VAMD") {
        return Err(VamError::new(
            "unsupported-profile",
            "native optimizer observer-alias-v1 accepts decoded VAM0/VAMD frames only",
        ));
    }
    let (output, mut rows) = observer_alias_pass(&report.instructions);
    let (output, compress_rows) = compress_alias_pass(&output);
    rows.extend(compress_rows);
    let (output, idempotent_rows) = compress_idempotent_pass(&output);
    rows.extend(idempotent_rows);
    let (output, dead_rows) = dead_shadow_pass(&output);
    rows.extend(dead_rows);
    let mut optimized = report.clone();
    optimized.instructions = output;
    Ok(OptimizationReport {
        contract: CONTRACT,
        slice: SLICE,
        original: report.clone(),
        optimized,
        rows,
    })
}

pub fn optimize_slice(report: &FrameReport, slice: &str) -> Result<OptimizationReport, VamError> {
    if slice != SLICE && slice != "observer-alias" {
        return Err(VamError::new(
            "unsupported-profile",
            format!("unsupported native optimizer slice: {slice}"),
        ));
    }
    optimize_observer_alias(report)
}

pub fn optimizer_slice_json(report: &FrameReport, slice: &str) -> Result<String, VamError> {
    let opt = optimize_slice(report, slice)?;
    Ok(optimizer_report_json(&opt, None))
}

pub fn optimizer_report_json(
    opt: &OptimizationReport,
    emitted_frame: Option<&OptimizedFrameEmission<'_>>,
) -> String {
    let mut out = String::from("{\"ok\":true,\"profile\":\"vam0-ref-v1\"");
    out.push_str(",\"optimizer_contract\":");
    push_json_string(&mut out, opt.contract);
    out.push_str(",\"optimizer_slice\":");
    push_json_string(&mut out, opt.slice);
    out.push_str(",\"input_magic\":");
    push_json_string(&mut out, opt.original.magic);
    out.push_str(",\"optimizer_boundary\":\"decoded-ir-report-only\"");
    out.push_str(&format!(
        ",\"original_instruction_count\":{},\"optimized_instruction_count\":{}",
        opt.original.instructions.len(),
        opt.optimized.instructions.len()
    ));
    out.push_str(",\"rows\":");
    push_rows(&mut out, &opt.rows);
    out.push_str(",\"optimized_report\":");
    out.push_str(&semantic_report_json(&opt.optimized));
    if let Some(frame) = emitted_frame {
        out.push_str(",\"emitted_frame\":{\"magic\":");
        push_json_string(&mut out, frame.magic);
        out.push_str(&format!(",\"version\":{}", frame.version));
        out.push_str(",\"boundary\":");
        push_json_string(&mut out, frame.boundary);
        out.push_str(",\"path\":");
        push_json_string(&mut out, frame.path);
        out.push_str(&format!(
            ",\"bytes\":{},\"payload_len\":{},\"instruction_count\":{},\"crc32\":\"{:08x}\",\"source\":\"native-optimized-instructions\"}}",
            frame.bytes, frame.payload_len, frame.instruction_count, frame.crc32
        ));
    }
    out.push('}');
    out
}

fn push_rows(out: &mut String, rows: &[OptimizationRow]) {
    out.push('[');
    for (i, row) in rows.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        out.push_str("{\"pass_name\":");
        push_json_string(out, row.pass_name);
        out.push_str(",\"action\":");
        push_json_string(out, row.action);
        out.push_str(",\"detail\":");
        push_json_string(out, &row.detail);
        out.push_str(",\"accepted\":");
        out.push_str(if row.accepted { "true" } else { "false" });
        out.push('}');
    }
    out.push(']');
}

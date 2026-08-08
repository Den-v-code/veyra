use crate::intrinsic_types::{IntrinsicFrameReport, IntrinsicNode, Mark, Obstruction, PathStep};
use crate::VamError;

pub const INTRINSIC_PROFILE: &str = "veyra.vami.intrinsic-r12.4.v1";

pub fn intrinsic_success_json(report: &IntrinsicFrameReport) -> String {
    let mut out = String::new();
    out.push_str("{\"ok\":true,\"profile\":\"");
    out.push_str(INTRINSIC_PROFILE);
    out.push_str("\",\"frame\":{\"magic\":\"VAMI\",\"version\":");
    out.push_str(&report.version.to_string());
    out.push_str(",\"size\":");
    out.push_str(&report.size.to_string());
    out.push_str(",\"crc32\":\"");
    out.push_str(&format!("{:08x}", report.crc32));
    out.push_str("\"},\"execution\":{\"status\":\"");
    out.push_str(report.value.status());
    out.push_str("\",\"tag\":\"");
    out.push_str(report.value.tag());
    out.push_str("\",\"nodes\":");
    out.push_str(&report.nodes.to_string());
    out.push_str(",\"obstructions\":");
    out.push_str(&report.obstructions.to_string());
    out.push_str(",\"value\":");
    push_node(&mut out, &report.value);
    out.push_str(
        ",\"evidence_accepted\":false,\"promotion_ready\":false,\"taxonomy_changed\":false}}",
    );
    out
}

pub fn intrinsic_error_json(error: &VamError) -> String {
    let mut out = String::new();
    out.push_str("{\"ok\":false,\"profile\":\"");
    out.push_str(INTRINSIC_PROFILE);
    out.push_str("\",\"error\":{\"kind\":");
    push_string(&mut out, error.kind);
    out.push_str(",\"message\":");
    push_string(&mut out, &error.message);
    out.push_str("}}");
    out
}

fn push_node(out: &mut String, value: &IntrinsicNode) {
    match value {
        IntrinsicNode::Anchor => {
            out.push_str(
                "{\"tag\":\"anchor\",\"name\":\"intrinsic-origin\",\"mark\":\"intrinsic-origin\"}",
            );
        }
        IntrinsicNode::Tact => {
            out.push_str("{\"tag\":\"tact\",\"start\":\"intrinsic-origin\",\"end\":\"intrinsic-origin\",\"mark\":\"intrinsic-successor\"}");
        }
        IntrinsicNode::Recurrence { tacts, anchor } => {
            out.push_str("{\"tag\":\"recurrence\",\"tacts\":[");
            for index in 0..*tacts {
                if index > 0 {
                    out.push(',');
                }
                push_node(out, &IntrinsicNode::Tact);
            }
            out.push_str("],\"anchor\":");
            if *anchor {
                push_node(out, &IntrinsicNode::Anchor);
            } else {
                out.push_str("null");
            }
            out.push('}');
        }
        IntrinsicNode::Mark(mark) => {
            out.push_str("{\"tag\":\"mark\",\"value\":\"");
            out.push_str(mark_name(mark));
            out.push_str("\"}");
        }
        IntrinsicNode::RecurrenceValue(recurrence) => {
            out.push_str("{\"tag\":\"recurrence-value\",\"recurrence\":");
            push_node(out, recurrence);
            out.push('}');
        }
        IntrinsicNode::MarkValue(mark) => {
            out.push_str("{\"tag\":\"mark-value\",\"mark\":\"");
            out.push_str(mark_name(mark));
            out.push_str("\"}");
        }
        IntrinsicNode::PairValue(left, right) => {
            out.push_str("{\"tag\":\"pair-value\",\"left\":");
            push_node(out, left);
            out.push_str(",\"right\":");
            push_node(out, right);
            out.push('}');
        }
        IntrinsicNode::Obstruction(obstruction) => push_obstruction(out, obstruction),
        IntrinsicNode::Ready(response) => {
            out.push_str("{\"tag\":\"ready\",\"value\":");
            push_node(out, response);
            out.push('}');
        }
        IntrinsicNode::Blocked(obstructions) => {
            out.push_str("{\"tag\":\"blocked\",\"obstructions\":");
            push_obstructions(out, obstructions);
            out.push('}');
        }
        IntrinsicNode::Echo(response) => {
            out.push_str("{\"tag\":\"echo\",\"value\":");
            push_node(out, response);
            out.push('}');
        }
        IntrinsicNode::Mismatch(left, right) => {
            out.push_str("{\"tag\":\"mismatch\",\"left\":");
            push_node(out, left);
            out.push_str(",\"right\":");
            push_node(out, right);
            out.push('}');
        }
        IntrinsicNode::DomainBlocked { left, right } => {
            out.push_str("{\"tag\":\"domain-blocked\",\"left\":");
            push_obstructions(out, left);
            out.push_str(",\"right\":");
            push_obstructions(out, right);
            out.push('}');
        }
    }
}

fn push_obstructions(out: &mut String, values: &[Obstruction]) {
    out.push('[');
    for (index, value) in values.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        push_obstruction(out, value);
    }
    out.push(']');
}

fn push_obstruction(out: &mut String, value: &Obstruction) {
    out.push_str("{\"tag\":\"obstruction\",\"code\":\"tail-of-silence\",\"path\":[");
    for (index, step) in value.path.iter().enumerate() {
        if index > 0 {
            out.push(',');
        }
        push_string(
            out,
            match step {
                PathStep::ApplyTail => "apply-tail",
                PathStep::ApplyCrest => "apply-crest",
                PathStep::PairLeft => "pair-left",
                PathStep::PairRight => "pair-right",
            },
        );
    }
    out.push_str("]}");
}

fn mark_name(mark: &Mark) -> &'static str {
    match mark {
        Mark::Silent => "silent",
        Mark::Pulse => "pulse",
    }
}

fn push_string(out: &mut String, value: &str) {
    out.push('"');
    for ch in value.chars() {
        match ch {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c < ' ' => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
}

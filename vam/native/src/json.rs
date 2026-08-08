use std::collections::BTreeMap;

use crate::runtime::{execute, push_execution_json, Object, Value};
use crate::{FrameReport, VamError, WireArg};

pub fn success_json(report: &FrameReport) -> String {
    let mut out = String::new();
    out.push_str("{\"ok\":true,\"profile\":\"vam0-ref-v1\",");
    out.push_str(&format!(
        "\"frame\":{{\"magic\":\"{}\",\"version\":{},\"size\":{},\"crc32\":\"{:08x}\"}},",
        report.magic, report.version, report.size, report.crc32
    ));
    push_program_report_fields(&mut out, report);
    out.push('}');
    out
}

pub(crate) fn semantic_report_json(report: &FrameReport) -> String {
    let mut out = String::new();
    out.push_str("{\"ok\":true,\"profile\":\"vam0-ref-v1\",");
    push_program_report_fields(&mut out, report);
    out.push('}');
    out
}

fn push_program_report_fields(out: &mut String, report: &FrameReport) {
    out.push_str(&format!(
        "\"instruction_count\":{},\"ops\":[",
        report.instructions.len()
    ));
    for (i, inst) in report.instructions.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        push_json_string(out, &inst.op);
    }
    out.push_str("],\"instructions\":[");
    for (pc, inst) in report.instructions.iter().enumerate() {
        if pc > 0 {
            out.push(',');
        }
        out.push_str(&format!("{{\"pc\":{},\"op\":", pc));
        push_json_string(out, &inst.op);
        out.push_str(&format!(
            ",\"line\":{},\"argc\":{},\"args\":[",
            inst.line,
            inst.args.len()
        ));
        for (i, arg) in inst.args.iter().enumerate() {
            if i > 0 {
                out.push(',');
            }
            match arg {
                WireArg::Int(v) => out.push_str(&format!("{{\"t\":\"int\",\"v\":{v}}}")),
                WireArg::Reg(v) => out.push_str(&format!("{{\"t\":\"reg\",\"v\":{v}}}")),
                WireArg::Str(s) => {
                    out.push_str("{\"t\":\"str\",\"v\":");
                    push_json_string(out, s);
                    out.push('}');
                }
            }
        }
        out.push_str("]}");
    }
    out.push_str("]");
    match execute(report) {
        Ok(execution) => push_execution_json(out, &execution),
        Err(err) => {
            out.push_str(",\"execution_error\":{\"kind\":");
            push_json_string(out, &err.kind);
            out.push_str(",\"message\":");
            push_json_string(out, &err.message);
            out.push('}');
        }
    }
}

pub fn error_json(err: &VamError) -> String {
    let mut out = String::from("{\"ok\":false,\"profile\":\"vam0-ref-v1\",\"error\":{\"kind\":");
    push_json_string(&mut out, err.kind);
    out.push_str(",\"message\":");
    push_json_string(&mut out, &err.message);
    out.push_str("}}");
    out
}

pub(crate) fn detail(o: &Object) -> String {
    match o.kind.as_str() {
        "Echo" => format!(
            "passed={} observer={}",
            py_bool(matches!(o.field("passed"), Some(Value::Bool(true)))),
            o.field("observer")
                .and_then(Value::as_str)
                .unwrap_or("None")
        ),
        "Certificate" => format!(
            "claim={} accepted={}",
            o.field("claim").and_then(Value::as_str).unwrap_or(""),
            py_bool(matches!(o.field("accepted"), Some(Value::Bool(true))))
        ),
        "Obstruction" => format!(
            "claim={}",
            o.field("claim").and_then(Value::as_str).unwrap_or("")
        ),
        _ => o.kind.clone(),
    }
}

fn py_bool(v: bool) -> &'static str {
    if v {
        "True"
    } else {
        "False"
    }
}

pub(crate) fn push_object_list(out: &mut String, xs: &[Object]) {
    out.push('[');
    for (i, x) in xs.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        push_object(out, x);
    }
    out.push(']');
}

pub(crate) fn push_object(out: &mut String, o: &Object) {
    out.push_str("{\"kind\":");
    push_json_string(out, &o.kind);
    out.push_str(",\"data\":");
    push_map(out, &o.data);
    out.push('}');
}

fn push_map(out: &mut String, m: &BTreeMap<String, Value>) {
    out.push('{');
    for (i, (k, v)) in m.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        push_json_string(out, k);
        out.push(':');
        push_value(out, v);
    }
    out.push('}');
}

pub(crate) fn push_value(out: &mut String, v: &Value) {
    match v {
        Value::Null => out.push_str("null"),
        Value::Bool(b) => out.push_str(if *b { "true" } else { "false" }),
        Value::Int(n) => out.push_str(&n.to_string()),
        Value::Str(s) => push_json_string(out, s),
        Value::Map(m) => push_map(out, m),
        Value::List(xs) => {
            out.push('[');
            for (i, x) in xs.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                push_value(out, x);
            }
            out.push(']');
        }
        Value::Obj(o) => push_object(out, o),
    }
}

pub(crate) fn compact_value_json(value: &Value) -> String {
    let mut out = String::new();
    push_value(&mut out, value);
    out
}

pub(crate) fn push_json_string(out: &mut String, s: &str) {
    out.push('"');
    for ch in s.chars() {
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

use std::collections::BTreeMap;

use crate::json::{detail, push_json_string, push_object, push_object_list};
use crate::payload::{
    boundary_shadow, debug_data, label_shadow, list_field, obj, obj_field, obstruction,
    trace_shadow,
};
use crate::{FrameReport, Instruction, VamError, WireArg};

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum Value {
    Null,
    Bool(bool),
    Int(i64),
    Str(String),
    Map(BTreeMap<String, Value>),
    List(Vec<Value>),
    Obj(Object),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct Object {
    pub(crate) kind: String,
    pub(crate) data: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct TraceRow {
    pc: usize,
    op: String,
    dst: String,
    kind: String,
    detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExecutionReport {
    pc: usize,
    registers: BTreeMap<String, Object>,
    trace: Vec<TraceRow>,
    certs: Vec<Object>,
    obstructions: Vec<Object>,
}

pub(crate) fn execute(report: &FrameReport) -> Result<ExecutionReport, VamError> {
    let mut rt = Runtime::default();
    for (pc, inst) in report.instructions.iter().enumerate() {
        rt.pc = pc;
        rt.step(inst)?;
    }
    rt.pc = report.instructions.len();
    Ok(ExecutionReport {
        pc: rt.pc,
        registers: rt.registers,
        trace: rt.trace,
        certs: rt.certs,
        obstructions: rt.obstructions,
    })
}

#[rustfmt::skip]
pub(crate) fn push_execution_json(out: &mut String, report: &ExecutionReport) {
    out.push_str(&format!(",\"pc\":{},\"registers\":{{", report.pc));
    for (i, (reg, obj)) in report.registers.iter().enumerate() { if i > 0 { out.push(','); } push_json_string(out, reg); out.push(':'); push_object(out, obj); }
    out.push_str("},\"trace\":[");
    for (i, row) in report.trace.iter().enumerate() { if i > 0 { out.push(','); } out.push_str(&format!("{{\"pc\":{},\"op\":", row.pc)); push_json_string(out, &row.op); out.push_str(",\"dst\":"); push_json_string(out, &row.dst); out.push_str(",\"kind\":"); push_json_string(out, &row.kind); out.push_str(",\"detail\":"); push_json_string(out, &row.detail); out.push('}'); }
    out.push_str("],\"certs\":"); push_object_list(out, &report.certs); out.push_str(",\"obstructions\":"); push_object_list(out, &report.obstructions);
}

#[derive(Default)]
struct Runtime {
    pc: usize,
    registers: BTreeMap<String, Object>,
    trace: Vec<TraceRow>,
    certs: Vec<Object>,
    obstructions: Vec<Object>,
}

impl Runtime {
    fn step(&mut self, inst: &Instruction) -> Result<(), VamError> {
        let Some(WireArg::Reg(dst_id)) = inst.args.first() else {
            return Err(VamError::new(
                "execution",
                format!(
                    "line {}: first operand must be destination register",
                    inst.line
                ),
            ));
        };
        let dst = reg_name(*dst_id);
        let obj = self.dispatch(&inst.op, &inst.args[1..])?;
        let detail = detail(&obj);
        self.registers.insert(dst.clone(), obj.clone());
        self.trace.push(TraceRow {
            pc: self.pc,
            op: inst.op.clone(),
            dst,
            kind: obj.kind.clone(),
            detail,
        });
        if obj.kind == "Obstruction" {
            self.obstructions.push(obj.clone());
        }
        if obj.kind == "Certificate" && matches!(obj.field("accepted"), Some(Value::Bool(true))) {
            self.certs.push(obj);
        }
        Ok(())
    }

    fn dispatch(&self, op: &str, args: &[WireArg]) -> Result<Object, VamError> {
        match (op, args.len()) {
            ("REZ", 1) => Ok(obj("Rez", [("label", lit_arg(&args[0]))])),
            ("NOD", 2) => {
                let rez = self.resolve(&args[0]);
                Ok(expect(&rez, "Rez", "nod-requires-rez").unwrap_or_else(|| {
                    obj(
                        "Nod",
                        [("rez", Value::Obj(rez)), ("label", lit_arg(&args[1]))],
                    )
                }))
            }
            ("TACT", 3) => {
                let left = self.resolve(&args[0]);
                let right = self.resolve(&args[1]);
                Ok(expect(&left, "Nod", "tact-left")
                    .or_else(|| expect(&right, "Nod", "tact-right"))
                    .unwrap_or_else(|| {
                        obj(
                            "Tact",
                            [
                                ("left", Value::Obj(left)),
                                ("right", Value::Obj(right)),
                                ("label", lit_arg(&args[2])),
                            ],
                        )
                    }))
            }
            ("BREATH", n) if n > 0 => {
                let tacts: Vec<Object> = args.iter().map(|a| self.resolve(a)).collect();
                if let Some(bad) = tacts
                    .iter()
                    .find(|t| t.kind != "Tact")
                    .and_then(|t| expect(t, "Tact", "breath-requires-tacts"))
                {
                    Ok(bad)
                } else {
                    Ok(obj(
                        "Breath",
                        [(
                            "tacts",
                            Value::List(tacts.into_iter().map(Value::Obj).collect()),
                        )],
                    ))
                }
            }
            ("MODE", 1) => {
                let breath = self.resolve(&args[0]);
                Ok(expect(&breath, "Breath", "mode-requires-breath")
                    .unwrap_or_else(|| obj("Mode", [("breath", Value::Obj(breath))])))
            }
            ("OBSERVER", 1) => Ok(obj("Observer", [("kind", lit_arg(&args[0]))])),
            ("OBSERVE", 2) => Ok(shadow(&self.resolve(&args[0]), &self.resolve(&args[1]))),
            ("ECHO", 3) => {
                let left = self.resolve(&args[0]);
                let right = self.resolve(&args[1]);
                let obs = self.resolve(&args[2]);
                let left_s = shadow(&left, &obs);
                let right_s = shadow(&right, &obs);
                let passed = left_s.kind == "Shadow"
                    && right_s.kind == "Shadow"
                    && left_s.field("value") == right_s.field("value");
                Ok(obj(
                    "Echo",
                    [
                        ("passed", Value::Bool(passed)),
                        ("left", Value::Obj(left_s)),
                        ("right", Value::Obj(right_s)),
                        (
                            "observer",
                            obs.field("kind").cloned().unwrap_or(Value::Null),
                        ),
                    ],
                ))
            }
            ("OBSTRUCT", 2) => Ok(obstruction(
                lit_arg(&args[0]).as_str().unwrap_or(""),
                Value::Obj(self.resolve(&args[1])).object_data_or_null(),
            )),
            ("COMPRESS", 2) => {
                let s = shadow(&self.resolve(&args[0]), &self.resolve(&args[1]));
                Ok(obj(
                    "Compressed",
                    [
                        ("shadow", Value::Obj(s.clone())),
                        (
                            "observer",
                            s.field("observer").cloned().unwrap_or(Value::Null),
                        ),
                        ("lossless", Value::Bool(true)),
                    ],
                ))
            }
            ("CERT", 3) => {
                let evidence = self.resolve(&args[1]);
                let accepted = evidence.kind == "Echo"
                    && matches!(evidence.field("passed"), Some(Value::Bool(true)));
                Ok(obj(
                    "Certificate",
                    [
                        ("claim", lit_arg(&args[0])),
                        ("evidence", Value::Obj(evidence)),
                        ("boundary", lit_arg(&args[2])),
                        ("accepted", Value::Bool(accepted)),
                    ],
                ))
            }
            _ => Err(VamError::new(
                "execution",
                format!(
                    "unsupported or malformed instruction: {op}/{}",
                    args.len() + 1
                ),
            )),
        }
    }

    fn resolve(&self, arg: &WireArg) -> Object {
        match arg {
            WireArg::Reg(id) => self
                .registers
                .get(&reg_name(*id))
                .cloned()
                .unwrap_or_else(|| obstruction("missing-register", Value::Str(reg_name(*id)))),
            _ => obj("Literal", [("value", lit_arg(arg))]),
        }
    }
}

fn reg_name(id: i64) -> String {
    format!("%r{id}")
}

fn lit_arg(arg: &WireArg) -> Value {
    match arg {
        WireArg::Int(v) => Value::Int(*v),
        WireArg::Reg(id) => Value::Str(reg_name(*id)),
        WireArg::Str(s) => Value::Str(s.clone()),
    }
}

fn expect(actual: &Object, expected: &str, claim: &str) -> Option<Object> {
    (actual.kind != expected).then(|| {
        obstruction(
            claim,
            Value::map([
                ("expected", Value::Str(expected.into())),
                ("actual", Value::Str(actual.kind.clone())),
            ]),
        )
    })
}

fn shadow(src: &Object, obs: &Object) -> Object {
    if obs.kind != "Observer" {
        return obstruction("observe-requires-observer", Value::Str(obs.kind.clone()));
    }
    let kind = obs.field("kind").and_then(Value::as_str).unwrap_or("");
    let value = match kind {
        "length" => Value::Int(length_shadow(src)),
        "kind" => Value::Str(src.kind.to_ascii_lowercase()),
        "label" => label_shadow(src),
        "trace" => Value::Str(trace_shadow(src)),
        "boundary" => boundary_shadow(src),
        _ => Value::Str(debug_data(src)),
    };
    obj(
        "Shadow",
        [
            ("observer", Value::Str(kind.into())),
            ("value", value),
            ("source_kind", Value::Str(src.kind.clone())),
        ],
    )
}

#[rustfmt::skip]
fn length_shadow(o: &Object) -> i64 { match o.kind.as_str() { "Breath" => list_field(o, "tacts").map(|v| v.len() as i64).unwrap_or(0), "Mode" => obj_field(o, "breath").map(length_shadow).unwrap_or(1), _ => 1 } }

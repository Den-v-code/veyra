//! Standalone native mirror of bounded quantified-theorem schema semantics.
//!
//! Compiled directly by parity tests; not wired into the legacy VM crate.
pub const PROFILE: &str = "veyra.vam.quantified-theorem.v1";
pub const OPCODE: &str = "DECLARE_FORALL";
pub const BOUNDARY: &str = "symbolic-schema-and-specialization-not-proof";
pub const MAX_BINDERS: usize = 128;
pub const MAX_TEXT_ROWS: usize = 256;
pub const MAX_TEXT_BYTES: usize = 4096;
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Binder {
    pub name: String,
    pub kind: String,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct QuantifiedInstruction {
    pub theorem_id: String,
    pub binders: Vec<Binder>,
    pub assumptions: Vec<String>,
    pub conclusions: Vec<String>,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Specialization {
    pub theorem_id: String,
    pub assignments: Vec<(String, String)>,
    pub assumptions: Vec<String>,
    pub conclusions: Vec<String>,
    pub status: &'static str,
    pub proof_status: &'static str,
    pub boundary: &'static str,
}
pub fn validate(instruction: &QuantifiedInstruction) -> Result<(), String> {
    if !is_identifier(&instruction.theorem_id) {
        return Err("invalid quantified theorem id".into());
    }
    if instruction.binders.is_empty()
        || instruction.binders.len() > MAX_BINDERS
        || instruction.conclusions.is_empty()
        || instruction.assumptions.len() + instruction.conclusions.len() > MAX_TEXT_ROWS
    {
        return Err("quantified theorem requires binders and conclusions".into());
    }
    let mut names: Vec<&str> = Vec::new();
    for binder in &instruction.binders {
        if !is_identifier(&binder.name) || !is_identifier(&binder.kind) {
            return Err("invalid quantified binder".into());
        }
        if names.contains(&binder.name.as_str()) {
            return Err("duplicate quantified binder".into());
        }
        names.push(&binder.name);
    }
    let texts = instruction
        .assumptions
        .iter()
        .chain(&instruction.conclusions);
    for text in texts {
        if text.len() > MAX_TEXT_BYTES {
            return Err("invalid quantified theorem text".into());
        }
        for placeholder in placeholders(text)? {
            if !names.contains(&placeholder.as_str()) {
                return Err(format!("free quantified variable: {placeholder}"));
            }
        }
    }
    Ok(())
}
pub fn canonical_text(instruction: &QuantifiedInstruction) -> Result<String, String> {
    validate(instruction)?;
    let assumptions = json_string_array(&instruction.assumptions);
    let binder_rows: Vec<String> = instruction
        .binders
        .iter()
        .map(|row| {
            format!(
                "{{\"kind\":{},\"name\":{}}}",
                json_string(&row.kind),
                json_string(&row.name)
            )
        })
        .collect();
    let conclusions = json_string_array(&instruction.conclusions);
    Ok(format!(
        "{{\"assumptions\":{assumptions},\"binders\":[{}],\"conclusions\":{conclusions},\"opcode\":{},\"profile\":{},\"theorem_id\":{}}}",
        binder_rows.join(","),
        json_string(OPCODE),
        json_string(PROFILE),
        json_string(&instruction.theorem_id),
    ))
}
pub fn specialize(
    instruction: &QuantifiedInstruction,
    assignments: &[(String, String)],
) -> Result<Specialization, String> {
    validate(instruction)?;
    if assignments.len() != instruction.binders.len() {
        return Err("specialization assignment mismatch".into());
    }
    let mut assigned_names: Vec<&str> = Vec::new();
    for (name, _) in assignments {
        if !is_identifier(name)
            || assigned_names.contains(&name.as_str())
            || !instruction
                .binders
                .iter()
                .any(|binder| binder.name == *name)
        {
            return Err("specialization assignment mismatch".into());
        }
        assigned_names.push(name);
    }
    let mut stable = Vec::new();
    for binder in &instruction.binders {
        let value = assignments
            .iter()
            .find(|(name, _)| name == &binder.name)
            .map(|(_, value)| value)
            .ok_or_else(|| "specialization assignment mismatch".to_string())?;
        validate_typed_atom(&binder.name, &binder.kind, value)?;
        stable.push((binder.name.clone(), value.clone()));
    }
    let assumptions = instruction
        .assumptions
        .iter()
        .map(|row| substitute(row, &stable))
        .collect::<Result<Vec<_>, _>>()?;
    let conclusions = instruction
        .conclusions
        .iter()
        .map(|row| substitute(row, &stable))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(Specialization {
        theorem_id: instruction.theorem_id.clone(),
        assignments: stable,
        assumptions,
        conclusions,
        status: "instantiated-open",
        proof_status: "open",
        boundary: BOUNDARY,
    })
}
fn substitute(template: &str, assignments: &[(String, String)]) -> Result<String, String> {
    let chars: Vec<char> = template.chars().collect();
    let mut result = String::new();
    let mut index = 0;
    while index < chars.len() {
        if chars[index] != '$' {
            push_bounded_char(&mut result, chars[index])?;
            index += 1;
            continue;
        }
        let start = index + 1;
        let mut end = start;
        while end < chars.len() && identifier_tail(chars[end]) {
            end += 1;
        }
        if start == end || !chars[start].is_ascii_alphabetic() {
            return Err("invalid placeholder".into());
        }
        let name: String = chars[start..end].iter().collect();
        let value = assignments
            .iter()
            .find(|(candidate, _)| candidate == &name)
            .map(|(_, value)| value)
            .ok_or_else(|| format!("missing assignment for {name}"))?;
        push_bounded(&mut result, value)?;
        index = end;
    }
    Ok(result)
}
fn placeholders(text: &str) -> Result<Vec<String>, String> {
    let chars: Vec<char> = text.chars().collect();
    let mut result = Vec::new();
    let mut index = 0;
    while index < chars.len() {
        if chars[index] != '$' {
            index += 1;
            continue;
        }
        let start = index + 1;
        let mut end = start;
        while end < chars.len() && identifier_tail(chars[end]) {
            end += 1;
        }
        if start == end || !chars[start].is_ascii_alphabetic() {
            return Err("invalid placeholder".into());
        }
        result.push(chars[start..end].iter().collect());
        index = end;
    }
    Ok(result)
}
fn is_identifier(value: &str) -> bool {
    if value.len() > MAX_TEXT_BYTES {
        return false;
    }
    let mut chars = value.chars();
    matches!(chars.next(), Some(first) if first.is_ascii_alphabetic()) && chars.all(identifier_tail)
}
fn validate_typed_atom(name: &str, expected_kind: &str, value: &str) -> Result<(), String> {
    if value.len() > MAX_TEXT_BYTES {
        return Err(format!("unsafe specialization value for {name}"));
    }
    let Some((kind, atom)) = value.split_once(':') else {
        return Err(format!("typed specialization mismatch for {name}"));
    };
    if kind != expected_kind || !is_identifier(atom) {
        return Err(format!("typed specialization mismatch for {name}"));
    }
    Ok(())
}
fn push_bounded(result: &mut String, value: &str) -> Result<(), String> {
    if result.len().saturating_add(value.len()) > MAX_TEXT_BYTES {
        return Err("specialized theorem text exceeds resource bound".into());
    }
    result.push_str(value);
    Ok(())
}
fn push_bounded_char(result: &mut String, value: char) -> Result<(), String> {
    if result.len().saturating_add(value.len_utf8()) > MAX_TEXT_BYTES {
        return Err("specialized theorem text exceeds resource bound".into());
    }
    result.push(value);
    Ok(())
}

fn identifier_tail(value: char) -> bool {
    value.is_ascii_alphanumeric() || value == '_' || value == '-'
}

#[rustfmt::skip]
fn json_string_array(rows: &[String]) -> String {
    format!("[{}]", rows.iter().map(|row| json_string(row)).collect::<Vec<_>>().join(","))
}

fn json_string(value: &str) -> String {
    let mut result = String::from("\"");
    for ch in value.chars() {
        match ch {
            '"' => result.push_str("\\\""),
            '\\' => result.push_str("\\\\"),
            '\n' => result.push_str("\\n"),
            '\r' => result.push_str("\\r"),
            '\t' => result.push_str("\\t"),
            '\u{08}' => result.push_str("\\b"),
            '\u{0c}' => result.push_str("\\f"),
            c if c < '\u{20}' => result.push_str(&format!("\\u{:04x}", c as u32)),
            c => result.push(c),
        }
    }
    result.push('"');
    result
}

#[cfg(test)]
#[rustfmt::skip]
mod tests {
    use super::*;
    fn sample() -> QuantifiedInstruction {
        QuantifiedInstruction {
            theorem_id: "echo-reflexive".into(),
            binders: vec![Binder { name: "x".into(), kind: "nod".into() }],
            assumptions: vec![],
            conclusions: vec!["ready(echo($x,$x,observer:kind))".into()],
        }
    }
    #[test]
    fn symbolic_declaration_and_specialization_remain_open() {
        let row = sample();
        assert!(validate(&row).is_ok());
        let instance = specialize(&row, &[("x".into(), "nod:a".into())]).unwrap();
        assert_eq!(instance.proof_status, "open");
        assert_eq!(instance.conclusions, vec!["ready(echo(nod:a,nod:a,observer:kind))"]);
    }
    #[test]
    fn free_variables_and_incomplete_assignments_fail_closed() {
        let mut row = sample();
        row.conclusions = vec!["ready($y)".into()];
        assert!(validate(&row).is_err());
        assert!(specialize(&sample(), &[]).is_err());
    }
    #[test]
    fn typed_hostile_and_oversized_specializations_fail_closed() {
        let row = sample();
        for value in ["mode:a", "nod:a)", "nod:$x", "nod:a:b", "nod:é"] {
            assert!(specialize(&row, &[("x".into(), value.into())]).is_err());
        }
        let oversized = format!("nod:{}", "a".repeat(4093));
        assert!(specialize(&row, &[("x".into(), oversized)]).is_err());
        let expanding = QuantifiedInstruction {
            theorem_id: "bounded".into(),
            binders: vec![Binder { name: "x".into(), kind: "nod".into() }],
            assumptions: vec![],
            conclusions: vec!["$x$x".into()],
        };
        let large = format!("nod:{}", "a".repeat(3000));
        assert!(specialize(&expanding, &[("x".into(), large)]).is_err());
    }
}

use crate::json::push_json_string;
use crate::{Instruction, WireArg};

const VAM0_MAGIC: &[u8; 4] = b"VAM0";
const VAM0_VERSION: u16 = 1;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EncodedVam0Frame {
    pub bytes: Vec<u8>,
    pub payload_len: usize,
    pub crc32: u32,
}

pub fn encode_vam0_frame(instructions: &[Instruction]) -> EncodedVam0Frame {
    let payload = program_payload(instructions);
    let crc32 = crc32_ieee(payload.as_bytes());
    let mut bytes = Vec::with_capacity(14 + payload.len());
    bytes.extend_from_slice(VAM0_MAGIC);
    bytes.extend_from_slice(&VAM0_VERSION.to_be_bytes());
    bytes.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    bytes.extend_from_slice(&crc32.to_be_bytes());
    bytes.extend_from_slice(payload.as_bytes());
    EncodedVam0Frame {
        bytes,
        payload_len: payload.len(),
        crc32,
    }
}

fn program_payload(instructions: &[Instruction]) -> String {
    let mut out = String::from("[");
    for (i, inst) in instructions.iter().enumerate() {
        if i > 0 {
            out.push(',');
        }
        out.push_str("{\"op\":");
        push_json_string(&mut out, &inst.op);
        out.push_str(",\"args\":[");
        for (j, arg) in inst.args.iter().enumerate() {
            if j > 0 {
                out.push(',');
            }
            push_wire_arg(&mut out, arg);
        }
        out.push_str("],\"line\":");
        out.push_str(&inst.line.to_string());
        out.push('}');
    }
    out.push(']');
    out
}

fn push_wire_arg(out: &mut String, arg: &WireArg) {
    match arg {
        WireArg::Int(v) => out.push_str(&format!("{{\"t\":\"int\",\"v\":{v}}}")),
        WireArg::Reg(v) => out.push_str(&format!("{{\"t\":\"reg\",\"v\":{v}}}")),
        WireArg::Str(v) => {
            out.push_str("{\"t\":\"str\",\"v\":");
            push_json_string(out, v);
            out.push('}');
        }
    }
}

fn crc32_ieee(bytes: &[u8]) -> u32 {
    let mut crc = 0xffff_ffffu32;
    for &b in bytes {
        crc ^= b as u32;
        for _ in 0..8 {
            crc = if crc & 1 != 0 {
                (crc >> 1) ^ 0xedb8_8320
            } else {
                crc >> 1
            };
        }
    }
    !crc
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{inspect_vam0, WireArg};

    #[test]
    fn encoded_vam0_frame_round_trips_through_native_decoder() {
        let instructions = vec![Instruction {
            op: "REZ".into(),
            args: vec![WireArg::Reg(1), WireArg::Str("phase".into())],
            line: 7,
        }];
        let frame = encode_vam0_frame(&instructions);
        let decoded = inspect_vam0(&frame.bytes).unwrap();

        assert_eq!(decoded.magic, "VAM0");
        assert_eq!(decoded.instructions, instructions);
        assert_eq!(decoded.size as usize, frame.payload_len);
        assert_eq!(decoded.crc32, frame.crc32);
    }
}

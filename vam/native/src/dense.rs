use crate::{FrameReport, Instruction, VamError, WireArg};

const MAGIC: &[u8; 4] = b"VAMD";
const VERSION: u16 = 1;
const HEADER_LEN: usize = 14;

pub fn inspect_vamdense(bytes: &[u8]) -> Result<FrameReport, VamError> {
    if bytes.len() < HEADER_LEN {
        return Err(VamError::new("short_frame", "short VAMD frame"));
    }
    if &bytes[..4] != MAGIC {
        return Err(VamError::new("magic", "bad VAMD magic"));
    }
    let version = u16::from_be_bytes([bytes[4], bytes[5]]);
    if version != VERSION {
        return Err(VamError::new(
            "version",
            format!("unsupported VAMD version: {version}"),
        ));
    }
    let payload_len = u32::from_be_bytes([bytes[6], bytes[7], bytes[8], bytes[9]]) as usize;
    let crc32 = u32::from_be_bytes([bytes[10], bytes[11], bytes[12], bytes[13]]);
    let payload = &bytes[HEADER_LEN..];
    if payload.len() != payload_len {
        return Err(VamError::new("length", "VAMD payload length mismatch"));
    }
    if crc32_ieee(payload) != crc32 {
        return Err(VamError::new("crc32", "VAMD checksum mismatch"));
    }
    Ok(FrameReport {
        magic: "VAMD",
        version,
        size: payload_len as u32,
        crc32,
        instructions: parse_payload(payload)?,
    })
}

fn parse_payload(payload: &[u8]) -> Result<Vec<Instruction>, VamError> {
    let mut r = Reader::new(payload);
    let count = r.u16()? as usize;
    let mut instructions = Vec::with_capacity(count);
    for _ in 0..count {
        instructions.push(Instruction {
            op: opcode_name(r.u8()?)?.to_string(),
            line: r.u32()? as i64,
            args: parse_args(&mut r)?,
        });
    }
    r.finish()?;
    Ok(instructions)
}

fn parse_args(r: &mut Reader<'_>) -> Result<Vec<WireArg>, VamError> {
    let count = r.u8()? as usize;
    let mut args = Vec::with_capacity(count);
    for _ in 0..count {
        args.push(match r.u8()? {
            1 => WireArg::Reg(r.u16()? as i64),
            2 => WireArg::Int(r.i64()?),
            3 => WireArg::Str(r.str()?),
            _ => return Err(r.bad("bad VAMD payload")),
        });
    }
    Ok(args)
}

fn opcode_name(code: u8) -> Result<&'static str, VamError> {
    Ok(match code {
        0x01 => "REZ",
        0x02 => "NOD",
        0x03 => "TACT",
        0x04 => "BREATH",
        0x05 => "MODE",
        0x06 => "OBSERVER",
        0x07 => "OBSERVE",
        0x08 => "ECHO",
        0x09 => "OBSTRUCT",
        0x0A => "COMPRESS",
        0x0B => "CERT",
        _ => {
            return Err(VamError::new(
                "opcode",
                format!("unknown VAMD opcode: {code:#04x}"),
            ))
        }
    })
}

struct Reader<'a> {
    bytes: &'a [u8],
    pos: usize,
}

impl<'a> Reader<'a> {
    fn new(bytes: &'a [u8]) -> Self {
        Self { bytes, pos: 0 }
    }
    fn finish(&self) -> Result<(), VamError> {
        if self.pos == self.bytes.len() {
            Ok(())
        } else {
            Err(self.bad("trailing VAMD payload data"))
        }
    }
    fn u8(&mut self) -> Result<u8, VamError> {
        self.take(1).map(|b| b[0])
    }
    fn u16(&mut self) -> Result<u16, VamError> {
        let b = self.take(2)?;
        Ok(u16::from_be_bytes([b[0], b[1]]))
    }
    fn u32(&mut self) -> Result<u32, VamError> {
        let b = self.take(4)?;
        Ok(u32::from_be_bytes([b[0], b[1], b[2], b[3]]))
    }
    fn i64(&mut self) -> Result<i64, VamError> {
        let b = self.take(8)?;
        Ok(i64::from_be_bytes([
            b[0], b[1], b[2], b[3], b[4], b[5], b[6], b[7],
        ]))
    }
    fn str(&mut self) -> Result<String, VamError> {
        let len = self.u16()? as usize;
        let bytes = self.take(len)?;
        std::str::from_utf8(bytes)
            .map(|s| s.to_string())
            .map_err(|_| self.bad("bad VAMD payload"))
    }
    fn take(&mut self, n: usize) -> Result<&'a [u8], VamError> {
        let end = self
            .pos
            .checked_add(n)
            .ok_or_else(|| self.bad("bad VAMD payload"))?;
        let bytes = self
            .bytes
            .get(self.pos..end)
            .ok_or_else(|| self.bad("bad VAMD payload"))?;
        self.pos = end;
        Ok(bytes)
    }
    fn bad(&self, msg: impl Into<String>) -> VamError {
        VamError::new("payload", msg)
    }
}

fn crc32_ieee(bytes: &[u8]) -> u32 {
    let mut crc = 0xffff_ffffu32;
    for &b in bytes {
        crc ^= b as u32;
        for _ in 0..8 {
            crc = if crc & 1 == 1 {
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
    use std::{env, fs};

    #[test]
    fn inspect_vamdense_from_env_blob() {
        let Ok(path) = env::var("VAMD_BLOB_PATH") else {
            return;
        };
        let bytes = fs::read(path).expect("blob");
        let report = inspect_vamdense(&bytes).expect("dense report");
        assert_eq!(report.version, 1);
        assert_eq!(report.instructions.len(), 3);
        assert_eq!(report.instructions[0].op, "REZ");
        assert_eq!(report.instructions[1].op, "TACT");
        assert_eq!(report.instructions[2].op, "CERT");
        assert_eq!(report.instructions[1].args[0], WireArg::Reg(7));
        assert_eq!(report.instructions[1].args[1], WireArg::Int(-5));
        assert_eq!(
            report.instructions[2].args[2],
            WireArg::Str("dense-boundary".into())
        );
    }
}

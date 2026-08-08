use std::collections::HashSet;

use crate::intrinsic_support::{crc32_ieee, response_kind, valid_path};
use crate::intrinsic_types::{IntrinsicFrameReport, IntrinsicNode, Mark, Obstruction, PathStep};
use crate::VamError;

const MAGIC: &[u8; 4] = b"VAMI";
const VERSION: u16 = 1;
const HEADER_LEN: usize = 14;
const MAX_PAYLOAD: usize = 1024 * 1024;
const MAX_NODES: usize = 4096;
const MAX_DEPTH: usize = 128;
const MAX_TACTS: usize = 2047;
const MAX_OBSTRUCTIONS: usize = 2048;
const MAX_PATH: usize = 128;

pub fn inspect_vami(bytes: &[u8]) -> Result<IntrinsicFrameReport, VamError> {
    if bytes.len() < HEADER_LEN {
        return Err(VamError::new("short_frame", "short VAMI frame"));
    }
    if &bytes[..4] != MAGIC {
        return Err(VamError::new("magic", "bad VAMI magic"));
    }
    let version = u16::from_be_bytes([bytes[4], bytes[5]]);
    if version != VERSION {
        return Err(VamError::new(
            "version",
            format!("unsupported VAMI version: {version}"),
        ));
    }
    let size = u32::from_be_bytes([bytes[6], bytes[7], bytes[8], bytes[9]]);
    if size as usize > MAX_PAYLOAD {
        return Err(VamError::new("resource", "VAMI payload exceeds 1 MiB"));
    }
    let crc32 = u32::from_be_bytes([bytes[10], bytes[11], bytes[12], bytes[13]]);
    let payload = &bytes[HEADER_LEN..];
    if payload.len() != size as usize {
        return Err(VamError::new("length", "VAMI payload length mismatch"));
    }
    if crc32_ieee(payload) != crc32 {
        return Err(VamError::new("crc32", "VAMI checksum mismatch"));
    }
    let mut reader = Reader::new(payload);
    let value = reader.node(0)?;
    reader.finish()?;
    Ok(IntrinsicFrameReport {
        version,
        size,
        crc32,
        nodes: reader.nodes,
        obstructions: reader.obstructions,
        value,
    })
}

struct Reader<'a> {
    bytes: &'a [u8],
    pos: usize,
    nodes: usize,
    obstructions: usize,
}

impl<'a> Reader<'a> {
    fn new(bytes: &'a [u8]) -> Self {
        Self {
            bytes,
            pos: 0,
            nodes: 0,
            obstructions: 0,
        }
    }

    fn node(&mut self, depth: usize) -> Result<IntrinsicNode, VamError> {
        self.enter(depth)?;
        match self.u8()? {
            1 => Ok(IntrinsicNode::Anchor),
            2 => Ok(IntrinsicNode::Tact),
            3 => self.recurrence(depth),
            4 => Ok(IntrinsicNode::Mark(self.mark()?)),
            5 => {
                let recurrence = self.node(depth + 1)?;
                if !matches!(recurrence, IntrinsicNode::Recurrence { .. }) {
                    return Err(self.bad("recurrence-value requires recurrence"));
                }
                Ok(IntrinsicNode::RecurrenceValue(Box::new(recurrence)))
            }
            6 => Ok(IntrinsicNode::MarkValue(self.mark()?)),
            7 => {
                let left = self.response(depth + 1)?;
                let right = self.response(depth + 1)?;
                Ok(IntrinsicNode::PairValue(Box::new(left), Box::new(right)))
            }
            8 => Ok(IntrinsicNode::Obstruction(self.obstruction(depth)?)),
            9 => Ok(IntrinsicNode::Ready(Box::new(self.response(depth + 1)?))),
            10 => Ok(IntrinsicNode::Blocked(self.obstruction_set(depth, false)?)),
            11 => Ok(IntrinsicNode::Echo(Box::new(self.response(depth + 1)?))),
            12 => self.mismatch(depth),
            13 => self.domain_blocked(depth),
            tag => Err(VamError::new("tag", format!("unknown VAMI tag: {tag}"))),
        }
    }

    fn response(&mut self, depth: usize) -> Result<IntrinsicNode, VamError> {
        let value = self.node(depth)?;
        if matches!(
            value,
            IntrinsicNode::RecurrenceValue(_)
                | IntrinsicNode::MarkValue(_)
                | IntrinsicNode::PairValue(_, _)
        ) {
            Ok(value)
        } else {
            Err(self.bad("response child has non-response tag"))
        }
    }

    fn recurrence(&mut self, depth: usize) -> Result<IntrinsicNode, VamError> {
        let tacts = self.u16()? as usize;
        let anchor = match self.u8()? {
            0 => false,
            1 => true,
            _ => return Err(self.bad("invalid recurrence anchor flag")),
        };
        if tacts > MAX_TACTS || (tacts == 0) != anchor {
            return Err(self.bad("invalid intrinsic recurrence"));
        }
        self.synthetic_children(tacts + usize::from(anchor), depth + 1)?;
        Ok(IntrinsicNode::Recurrence {
            tacts: tacts as u16,
            anchor,
        })
    }

    fn mismatch(&mut self, depth: usize) -> Result<IntrinsicNode, VamError> {
        let left = self.response(depth + 1)?;
        let right = self.response(depth + 1)?;
        if response_kind(&left) != response_kind(&right) {
            return Err(self.bad("mismatch response kinds differ"));
        }
        if left == right {
            return Err(self.bad("mismatch responses are equal"));
        }
        Ok(IntrinsicNode::Mismatch(Box::new(left), Box::new(right)))
    }

    fn domain_blocked(&mut self, depth: usize) -> Result<IntrinsicNode, VamError> {
        let left = self.obstruction_set(depth, true)?;
        let right = self.obstruction_set(depth, true)?;
        if left.is_empty() && right.is_empty() {
            return Err(self.bad("domain-blocked requires an obstruction"));
        }
        Ok(IntrinsicNode::DomainBlocked { left, right })
    }

    fn obstruction_set(&mut self, depth: usize, empty: bool) -> Result<Vec<Obstruction>, VamError> {
        let count = self.u16()? as usize;
        if count > MAX_OBSTRUCTIONS || (!empty && count == 0) {
            return Err(self.bad("invalid obstruction count"));
        }
        if self.obstructions + count > MAX_OBSTRUCTIONS {
            return Err(self.resource("too many VAMI obstructions"));
        }
        let mut values = Vec::with_capacity(count);
        let mut paths = HashSet::with_capacity(count);
        for _ in 0..count {
            self.enter(depth + 1)?;
            if self.u8()? != 8 {
                return Err(self.bad("obstruction set requires obstruction tags"));
            }
            let value = self.obstruction(depth + 1)?;
            if !paths.insert(value.path.clone()) {
                return Err(self.bad("duplicate obstruction path"));
            }
            values.push(value);
        }
        Ok(values)
    }

    fn obstruction(&mut self, _depth: usize) -> Result<Obstruction, VamError> {
        if self.u8()? != 0 {
            return Err(self.bad("unknown obstruction code"));
        }
        let count = self.u16()? as usize;
        if count == 0 || count > MAX_PATH {
            return Err(self.bad("invalid obstruction path length"));
        }
        let mut path = Vec::with_capacity(count);
        for _ in 0..count {
            path.push(match self.u8()? {
                0 => PathStep::ApplyTail,
                1 => PathStep::ApplyCrest,
                2 => PathStep::PairLeft,
                3 => PathStep::PairRight,
                _ => return Err(self.bad("unknown obstruction path step")),
            });
        }
        if !valid_path(&path) {
            return Err(self.bad("invalid obstruction path grammar"));
        }
        self.obstructions += 1;
        if self.obstructions > MAX_OBSTRUCTIONS {
            return Err(self.resource("too many VAMI obstructions"));
        }
        Ok(Obstruction { path })
    }

    fn enter(&mut self, depth: usize) -> Result<(), VamError> {
        if depth > MAX_DEPTH {
            return Err(self.resource("VAMI depth exceeds 128"));
        }
        self.nodes += 1;
        if self.nodes > MAX_NODES {
            return Err(self.resource("VAMI node count exceeds 4096"));
        }
        Ok(())
    }

    fn synthetic_children(&mut self, count: usize, depth: usize) -> Result<(), VamError> {
        if depth > MAX_DEPTH {
            return Err(self.resource("VAMI depth exceeds 128"));
        }
        self.nodes = self.nodes.saturating_add(count);
        if self.nodes > MAX_NODES {
            return Err(self.resource("VAMI node count exceeds 4096"));
        }
        Ok(())
    }

    fn mark(&mut self) -> Result<Mark, VamError> {
        match self.u8()? {
            0 => Ok(Mark::Silent),
            1 => Ok(Mark::Pulse),
            _ => Err(self.bad("unknown intrinsic mark")),
        }
    }

    fn finish(&self) -> Result<(), VamError> {
        if self.pos == self.bytes.len() {
            Ok(())
        } else {
            Err(self.bad("trailing VAMI payload data"))
        }
    }

    fn u8(&mut self) -> Result<u8, VamError> {
        self.take(1).map(|b| b[0])
    }

    fn u16(&mut self) -> Result<u16, VamError> {
        let b = self.take(2)?;
        Ok(u16::from_be_bytes([b[0], b[1]]))
    }

    fn take(&mut self, n: usize) -> Result<&'a [u8], VamError> {
        let end = self
            .pos
            .checked_add(n)
            .ok_or_else(|| self.bad("bad VAMI payload"))?;
        let value = self
            .bytes
            .get(self.pos..end)
            .ok_or_else(|| self.bad("bad VAMI payload"))?;
        self.pos = end;
        Ok(value)
    }

    fn bad(&self, message: impl Into<String>) -> VamError {
        VamError::new("payload", message)
    }

    fn resource(&self, message: impl Into<String>) -> VamError {
        VamError::new("resource", message)
    }
}

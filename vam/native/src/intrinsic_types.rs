#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Mark {
    Silent,
    Pulse,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum PathStep {
    ApplyTail,
    ApplyCrest,
    PairLeft,
    PairRight,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Obstruction {
    pub path: Vec<PathStep>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum IntrinsicNode {
    Anchor,
    Tact,
    Recurrence {
        tacts: u16,
        anchor: bool,
    },
    Mark(Mark),
    RecurrenceValue(Box<IntrinsicNode>),
    MarkValue(Mark),
    PairValue(Box<IntrinsicNode>, Box<IntrinsicNode>),
    Obstruction(Obstruction),
    Ready(Box<IntrinsicNode>),
    Blocked(Vec<Obstruction>),
    Echo(Box<IntrinsicNode>),
    Mismatch(Box<IntrinsicNode>, Box<IntrinsicNode>),
    DomainBlocked {
        left: Vec<Obstruction>,
        right: Vec<Obstruction>,
    },
}

impl IntrinsicNode {
    pub fn tag(&self) -> &'static str {
        match self {
            Self::Anchor => "anchor",
            Self::Tact => "tact",
            Self::Recurrence { .. } => "recurrence",
            Self::Mark(_) => "mark",
            Self::RecurrenceValue(_) => "recurrence-value",
            Self::MarkValue(_) => "mark-value",
            Self::PairValue(_, _) => "pair-value",
            Self::Obstruction(_) => "obstruction",
            Self::Ready(_) => "ready",
            Self::Blocked(_) => "blocked",
            Self::Echo(_) => "echo",
            Self::Mismatch(_, _) => "mismatch",
            Self::DomainBlocked { .. } => "domain-blocked",
        }
    }

    pub fn status(&self) -> &'static str {
        match self {
            Self::Blocked(_) | Self::DomainBlocked { .. } => "blocked",
            Self::Mismatch(_, _) => "mismatch",
            Self::Ready(_) | Self::Echo(_) => "ready",
            _ => "decoded",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct IntrinsicFrameReport {
    pub version: u16,
    pub size: u32,
    pub crc32: u32,
    pub nodes: usize,
    pub obstructions: usize,
    pub value: IntrinsicNode,
}

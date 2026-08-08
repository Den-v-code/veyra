use crate::intrinsic_types::{IntrinsicNode, PathStep};

pub(crate) fn valid_path(path: &[PathStep]) -> bool {
    let mut index = 0;
    while index < path.len() && matches!(path[index], PathStep::PairLeft | PathStep::PairRight) {
        index += 1;
    }
    if index < path.len() && path[index] == PathStep::ApplyCrest {
        index += 1;
    }
    let tail = index;
    while index < path.len() && path[index] == PathStep::ApplyTail {
        index += 1;
    }
    index == path.len() && index > tail
}

pub(crate) fn response_kind(value: &IntrinsicNode) -> String {
    match value {
        IntrinsicNode::RecurrenceValue(_) => "recurrence".into(),
        IntrinsicNode::MarkValue(_) => "mark".into(),
        IntrinsicNode::PairValue(left, right) => {
            format!("pair({},{})", response_kind(left), response_kind(right))
        }
        _ => "invalid".into(),
    }
}

pub(crate) fn crc32_ieee(bytes: &[u8]) -> u32 {
    let mut crc = 0xffff_ffffu32;
    for &byte in bytes {
        crc ^= byte as u32;
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

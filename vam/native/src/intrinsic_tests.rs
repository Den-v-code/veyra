use crate::intrinsic_support::crc32_ieee;
use crate::{inspect_vami, intrinsic_success_json};

fn frame(payload: &[u8]) -> Vec<u8> {
    let mut bytes = b"VAMI".to_vec();
    bytes.extend_from_slice(&1u16.to_be_bytes());
    bytes.extend_from_slice(&(payload.len() as u32).to_be_bytes());
    bytes.extend_from_slice(&crc32_ieee(payload).to_be_bytes());
    bytes.extend_from_slice(payload);
    bytes
}

#[test]
fn silence_recurrence_has_exact_json_and_counts() {
    let report = inspect_vami(&frame(&[3, 0, 0, 1])).unwrap();
    assert_eq!(report.nodes, 2);
    assert_eq!(report.obstructions, 0);
    let json = intrinsic_success_json(&report);
    assert!(json.contains("\"profile\":\"veyra.vami.intrinsic-r12.4.v1\""));
    assert!(json.contains("\"status\":\"decoded\",\"tag\":\"recurrence\""));
    assert!(json.contains("\"evidence_accepted\":false"));
    assert!(json.contains("\"promotion_ready\":false"));
    assert!(json.contains("\"taxonomy_changed\":false"));
}

#[test]
fn recurrence_is_compact_but_counts_synthetic_children() {
    let report = inspect_vami(&frame(&[3, 0x07, 0xff, 0])).unwrap();
    assert_eq!(report.nodes, 2048);
    assert_eq!(report.value.tag(), "recurrence");
    assert_eq!(
        inspect_vami(&frame(&[3, 0x08, 0x00, 0]))
            .unwrap_err()
            .message,
        "invalid intrinsic recurrence"
    );
    assert_eq!(
        inspect_vami(&frame(&[3, 0, 0, 1, 1])).unwrap_err().message,
        "trailing VAMI payload data"
    );
}

#[test]
fn ready_pair_executes_only_exact_response_children() {
    let payload = [9, 7, 6, 0, 5, 3, 0, 1, 0];
    let report = inspect_vami(&frame(&payload)).unwrap();
    assert_eq!(report.nodes, 6);
    assert_eq!(report.value.tag(), "ready");
    assert_eq!(report.value.status(), "ready");
}

#[test]
fn mismatch_rejects_equal_same_kind_values() {
    let error = inspect_vami(&frame(&[12, 6, 0, 6, 0])).unwrap_err();
    assert_eq!(error.kind, "payload");
    assert_eq!(error.message, "mismatch responses are equal");
}

#[test]
fn blocked_rejects_duplicate_and_bad_grammar_paths() {
    let duplicate = [10, 0, 2, 8, 0, 0, 1, 0, 8, 0, 0, 1, 0];
    assert_eq!(
        inspect_vami(&frame(&duplicate)).unwrap_err().message,
        "duplicate obstruction path"
    );
    let bad_grammar = [10, 0, 1, 8, 0, 0, 2, 0, 2];
    assert_eq!(
        inspect_vami(&frame(&bad_grammar)).unwrap_err().message,
        "invalid obstruction path grammar"
    );
}

#[test]
fn frame_boundary_rejects_crc_trailing_and_unknown_tag() {
    let mut bad_crc = frame(&[4, 0]);
    *bad_crc.last_mut().unwrap() = 1;
    assert_eq!(inspect_vami(&bad_crc).unwrap_err().kind, "crc32");
    assert_eq!(
        inspect_vami(&frame(&[4, 0, 1])).unwrap_err().message,
        "trailing VAMI payload data"
    );
    assert_eq!(inspect_vami(&frame(&[99])).unwrap_err().kind, "tag");
}

#[test]
fn response_depth_128_is_closed_and_129_rejects() {
    fn nested_pair(levels: usize) -> Vec<u8> {
        let mut payload = vec![7; levels];
        payload.extend_from_slice(&[6, 0]);
        for _ in 0..levels {
            payload.extend_from_slice(&[6, 1]);
        }
        payload
    }
    assert_eq!(inspect_vami(&frame(&nested_pair(128))).unwrap().nodes, 257);
    let error = inspect_vami(&frame(&nested_pair(129))).unwrap_err();
    assert_eq!(error.kind, "resource");
    assert_eq!(error.message, "VAMI depth exceeds 128");
}

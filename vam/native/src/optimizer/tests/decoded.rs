use super::{inst, report, report_with_magic};
use crate::optimizer::{optimize_observer_alias, optimizer_slice_json};
use crate::WireArg;

#[test]
fn observer_alias_removes_duplicate_observer_and_rewrites_uses() {
    let input = report(vec![
        inst(
            "OBSERVER",
            vec![WireArg::Reg(1), WireArg::Str("kind".into())],
        ),
        inst(
            "OBSERVER",
            vec![WireArg::Reg(2), WireArg::Str("kind".into())],
        ),
        inst(
            "ECHO",
            vec![
                WireArg::Reg(3),
                WireArg::Reg(1),
                WireArg::Reg(1),
                WireArg::Reg(2),
            ],
        ),
    ]);
    let opt = optimize_observer_alias(&input).unwrap();
    assert_eq!(opt.optimized.instructions.len(), 2);
    assert_eq!(opt.rows[0].detail, "%r2->%r1 kind=kind");
    assert_eq!(opt.optimized.instructions[1].args[3], WireArg::Reg(1));
}

#[test]
fn vamd_optimizer_uses_decoded_semantics_without_frame_claim() {
    let input = report_with_magic(
        "VAMD",
        vec![
            inst(
                "OBSERVER",
                vec![WireArg::Reg(1), WireArg::Str("kind".into())],
            ),
            inst(
                "OBSERVER",
                vec![WireArg::Reg(2), WireArg::Str("kind".into())],
            ),
            inst("REZ", vec![WireArg::Reg(3), WireArg::Str("phase".into())]),
            inst(
                "ECHO",
                vec![
                    WireArg::Reg(4),
                    WireArg::Reg(3),
                    WireArg::Reg(3),
                    WireArg::Reg(2),
                ],
            ),
        ],
    );
    let opt = optimize_observer_alias(&input).unwrap();
    assert_eq!(opt.original.magic, "VAMD");
    assert_eq!(
        opt.optimized.instructions.len(),
        input.instructions.len() - 1
    );
    assert!(opt.rows.iter().any(|row| row.pass_name == "observer-alias"
        && row.accepted
        && row.detail == "%r2->%r1 kind=kind"));
    assert_eq!(
        opt.optimized.instructions.last().unwrap().args[3],
        WireArg::Reg(1)
    );

    let json = optimizer_slice_json(&input, "observer-alias-v1").unwrap();
    assert!(json.contains("\"input_magic\":\"VAMD\""));
    assert!(json.contains("\"optimizer_boundary\":\"decoded-ir-report-only\""));
    assert!(json.contains(
        "\"optimized_report\":{\"ok\":true,\"profile\":\"vam0-ref-v1\",\"instruction_count\""
    ));
    assert!(!json.contains("\"optimized_frame\""));
    assert!(
        !json.contains("\"optimized_report\":{\"ok\":true,\"profile\":\"vam0-ref-v1\",\"frame\"")
    );
}

#[test]
fn unsupported_optimizer_slice_error_is_preserved_for_vamd() {
    let input = report_with_magic("VAMD", vec![]);
    let err = optimizer_slice_json(&input, "not-a-slice").unwrap_err();
    assert_eq!(err.kind, "unsupported-profile");
    assert_eq!(
        err.message,
        "unsupported native optimizer slice: not-a-slice"
    );
}

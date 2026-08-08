use super::{base_mode_with, inst, report};
use crate::optimizer::optimize_observer_alias;
use crate::WireArg;

#[test]
fn compress_alias_removes_duplicate_safe_compress_and_rewrites_uses() {
    let input = report(base_mode_with(vec![
        inst(
            "OBSERVER",
            vec![WireArg::Reg(7), WireArg::Str("kind".into())],
        ),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(8), WireArg::Reg(6), WireArg::Reg(7)],
        ),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(9), WireArg::Reg(6), WireArg::Reg(7)],
        ),
        inst(
            "ECHO",
            vec![
                WireArg::Reg(10),
                WireArg::Reg(8),
                WireArg::Reg(9),
                WireArg::Reg(7),
            ],
        ),
    ]));
    let opt = optimize_observer_alias(&input).unwrap();
    assert!(opt.rows.iter().any(|row| row.pass_name == "compress-alias"
        && row.accepted
        && row.detail == "%r9->%r8 source=%r6 observer=%r7"));
    assert_eq!(
        opt.optimized.instructions.len(),
        input.instructions.len() - 1
    );
    assert_eq!(
        opt.optimized.instructions.last().unwrap().args[2],
        WireArg::Reg(8)
    );
}

#[test]
fn compress_alias_rejects_duplicate_when_shadow_contains_obstruction() {
    let input = report(vec![
        inst("REZ", vec![WireArg::Reg(1), WireArg::Str("phase".into())]),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(2), WireArg::Reg(1), WireArg::Reg(1)],
        ),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(3), WireArg::Reg(1), WireArg::Reg(1)],
        ),
        inst(
            "ECHO",
            vec![
                WireArg::Reg(4),
                WireArg::Reg(2),
                WireArg::Reg(3),
                WireArg::Reg(1),
            ],
        ),
    ]);
    let opt = optimize_observer_alias(&input).unwrap();
    assert_eq!(opt.optimized.instructions, input.instructions);
    assert!(opt.rows.iter().any(|row| row.pass_name == "compress-alias"
        && !row.accepted
        && row.detail.contains("obstruction")));
}

#[test]
fn compress_idempotent_removes_same_observer_visible_candidate() {
    let input = report(vec![
        inst("REZ", vec![WireArg::Reg(1), WireArg::Str("phase".into())]),
        inst(
            "OBSERVER",
            vec![WireArg::Reg(2), WireArg::Str("kind".into())],
        ),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(3), WireArg::Reg(1), WireArg::Reg(2)],
        ),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(4), WireArg::Reg(3), WireArg::Reg(2)],
        ),
        inst(
            "ECHO",
            vec![
                WireArg::Reg(5),
                WireArg::Reg(3),
                WireArg::Reg(4),
                WireArg::Reg(2),
            ],
        ),
    ]);
    let opt = optimize_observer_alias(&input).unwrap();
    assert!(opt
        .rows
        .iter()
        .any(|row| row.pass_name == "compress-idempotent"
            && row.accepted
            && row.detail.contains("same-observer-visible")));
    assert_eq!(
        opt.optimized.instructions.len(),
        input.instructions.len() - 1
    );
    assert_eq!(
        opt.optimized.instructions.last().unwrap().args[2],
        WireArg::Reg(3)
    );
}

#[test]
fn compress_idempotent_rejects_nested_obstruction() {
    let input = report(vec![
        inst("REZ", vec![WireArg::Reg(1), WireArg::Str("phase".into())]),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(2), WireArg::Reg(1), WireArg::Reg(1)],
        ),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(3), WireArg::Reg(2), WireArg::Reg(1)],
        ),
        inst(
            "ECHO",
            vec![
                WireArg::Reg(4),
                WireArg::Reg(2),
                WireArg::Reg(3),
                WireArg::Reg(1),
            ],
        ),
    ]);
    let opt = optimize_observer_alias(&input).unwrap();
    assert_eq!(opt.optimized.instructions, input.instructions);
    assert!(opt
        .rows
        .iter()
        .any(|row| row.pass_name == "compress-idempotent"
            && !row.accepted
            && row.detail.contains("nested obstruction")));
}

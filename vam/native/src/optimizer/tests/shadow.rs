use super::{inst, report};
use crate::optimizer::optimize_observer_alias;
use crate::WireArg;

#[test]
fn dead_shadow_removes_unused_safe_shadow_but_keeps_obstruction_shadow() {
    let safe = report(vec![
        inst(
            "OBSERVER",
            vec![WireArg::Reg(1), WireArg::Str("kind".into())],
        ),
        inst("REZ", vec![WireArg::Reg(2), WireArg::Str("phase".into())]),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(3), WireArg::Reg(2), WireArg::Reg(1)],
        ),
    ]);
    let safe_opt = optimize_observer_alias(&safe).unwrap();
    assert_eq!(safe_opt.optimized.instructions.len(), 2);
    assert!(safe_opt
        .rows
        .iter()
        .any(|row| row.pass_name == "dead-shadow"
            && row.accepted
            && row.detail == "drop unused COMPRESS %r3"));

    let obstructed = report(vec![
        inst("REZ", vec![WireArg::Reg(1), WireArg::Str("phase".into())]),
        inst(
            "COMPRESS",
            vec![WireArg::Reg(2), WireArg::Reg(1), WireArg::Reg(1)],
        ),
    ]);
    let obstructed_opt = optimize_observer_alias(&obstructed).unwrap();
    assert_eq!(
        obstructed_opt.optimized.instructions,
        obstructed.instructions
    );
    assert!(obstructed_opt
        .rows
        .iter()
        .any(|row| row.pass_name == "dead-shadow"
            && !row.accepted
            && row.detail.contains("obstruction")));
}

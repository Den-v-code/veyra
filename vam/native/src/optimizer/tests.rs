use crate::{FrameReport, Instruction, WireArg};

mod compress;
mod decoded;
mod shadow;

fn report(instructions: Vec<Instruction>) -> FrameReport {
    report_with_magic("VAM0", instructions)
}

fn report_with_magic(magic: &'static str, instructions: Vec<Instruction>) -> FrameReport {
    FrameReport {
        magic,
        version: 1,
        size: 0,
        crc32: 0,
        instructions,
    }
}

fn base_mode_with(mut tail: Vec<Instruction>) -> Vec<Instruction> {
    let mut program = vec![
        inst("REZ", vec![WireArg::Reg(1), WireArg::Str("phase".into())]),
        inst(
            "NOD",
            vec![WireArg::Reg(2), WireArg::Reg(1), WireArg::Str("0".into())],
        ),
        inst(
            "NOD",
            vec![WireArg::Reg(3), WireArg::Reg(1), WireArg::Str("1".into())],
        ),
        inst(
            "TACT",
            vec![
                WireArg::Reg(4),
                WireArg::Reg(2),
                WireArg::Reg(3),
                WireArg::Str("step".into()),
            ],
        ),
        inst("BREATH", vec![WireArg::Reg(5), WireArg::Reg(4)]),
        inst("MODE", vec![WireArg::Reg(6), WireArg::Reg(5)]),
    ];
    program.append(&mut tail);
    program
}

fn inst(op: &str, args: Vec<WireArg>) -> Instruction {
    Instruction {
        op: op.into(),
        args,
        line: 1,
    }
}

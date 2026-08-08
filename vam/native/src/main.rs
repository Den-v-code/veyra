use std::{env, fs, process};

use vam_native::{
    encode_vam0_frame, error_json, inspect_vam0, inspect_vamdense, optimize_slice,
    optimizer_report_json, optimizer_slice_json, success_json, FrameReport, OptimizedFrameEmission,
    VamError,
};

fn main() {
    let args: Vec<String> = env::args().collect();
    let result = run(&args);
    match result {
        Ok(json) => println!("{json}"),
        Err(err) => {
            println!("{}", error_json(&err));
            process::exit(1);
        }
    }
}

fn run(args: &[String]) -> Result<String, VamError> {
    if args.len() == 2 && args[1] == "--help" {
        return Ok(help_json());
    }
    let mut profile = "vam0-ref-v1";
    let mut optimizer_slice: Option<&str> = None;
    let mut emit_optimized_vam0: Option<&str> = None;
    let mut path: Option<&str> = None;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--profile" => {
                i += 1;
                if i >= args.len() {
                    return Err(VamError {
                        kind: "usage",
                        message: "missing --profile value".into(),
                    });
                }
                profile = &args[i];
            }
            "--optimize" => {
                i += 1;
                if i >= args.len() {
                    return Err(VamError {
                        kind: "usage",
                        message: "missing --optimize value".into(),
                    });
                }
                optimizer_slice = Some(&args[i]);
            }
            "--emit-optimized-vam0" => {
                i += 1;
                if i >= args.len() {
                    return Err(VamError {
                        kind: "usage",
                        message: "missing --emit-optimized-vam0 value".into(),
                    });
                }
                emit_optimized_vam0 = Some(&args[i]);
            }
            value if value.starts_with('-') => {
                return Err(VamError {
                    kind: "usage",
                    message: format!("unknown option: {value}"),
                });
            }
            value => path = Some(value),
        }
        i += 1;
    }
    if profile != "vam0-ref-v1" {
        return Err(VamError {
            kind: "profile",
            message: format!("unsupported profile: {profile}"),
        });
    }
    let Some(path) = path else {
        return Err(VamError {
            kind: "usage",
            message:
                "usage: vam0-inspect [--profile vam0-ref-v1] [--optimize observer-alias-v1] [--emit-optimized-vam0 out.vam0] <file.vam0|file.vamd>"
                    .into(),
        });
    };
    let data = fs::read(path).map_err(|e| VamError {
        kind: "io",
        message: e.to_string(),
    })?;
    let report = inspect_frame(&data)?;
    match (optimizer_slice, emit_optimized_vam0) {
        (Some(slice), Some(out_path)) => {
            optimizer_slice_json_with_vam0_emit(&report, slice, out_path)
        }
        (Some(slice), None) => optimizer_slice_json(&report, slice),
        (None, Some(_)) => Err(VamError {
            kind: "usage",
            message: "--emit-optimized-vam0 requires --optimize".into(),
        }),
        (None, None) => Ok(success_json(&report)),
    }
}

fn optimizer_slice_json_with_vam0_emit(
    report: &FrameReport,
    slice: &str,
    out_path: &str,
) -> Result<String, VamError> {
    if slice != "observer-alias-v1" {
        return Err(VamError {
            kind: "unsupported-profile",
            message: "optimized VAM0 frame emission requires observer-alias-v1".into(),
        });
    }
    if report.magic != "VAM0" {
        return Err(VamError {
            kind: "unsupported-profile",
            message: "optimized VAM0 frame emission accepts VAM0 input only".into(),
        });
    }
    let opt = optimize_slice(report, slice)?;
    let frame = encode_vam0_frame(&opt.optimized.instructions);
    fs::write(out_path, &frame.bytes).map_err(|e| VamError {
        kind: "io",
        message: e.to_string(),
    })?;
    let emitted = OptimizedFrameEmission {
        magic: "VAM0",
        version: 1,
        boundary: "optimized-ir-to-vam0-frame",
        path: out_path,
        bytes: frame.bytes.len(),
        payload_len: frame.payload_len,
        instruction_count: opt.optimized.instructions.len(),
        crc32: frame.crc32,
    };
    Ok(optimizer_report_json(&opt, Some(&emitted)))
}

fn inspect_frame(data: &[u8]) -> Result<FrameReport, VamError> {
    if data.len() < 4 {
        return inspect_vam0(data);
    }
    match &data[..4] {
        b"VAM0" => inspect_vam0(data),
        b"VAMD" => inspect_vamdense(data),
        _ => Err(VamError {
            kind: "magic",
            message: "unsupported VAM frame magic".into(),
        }),
    }
}

fn help_json() -> String {
    "{\"ok\":true,\"usage\":\"vam0-inspect [--profile vam0-ref-v1] [--optimize observer-alias-v1] [--emit-optimized-vam0 out.vam0] <file.vam0|file.vamd>\"}"
        .to_string()
}

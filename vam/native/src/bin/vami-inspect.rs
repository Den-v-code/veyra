use std::{env, fs::File, io::Read, process};

use vam_native::{inspect_vami, intrinsic_error_json, intrinsic_success_json, VamError};

const PROFILE: &str = "veyra.vami.intrinsic-r12.4.v1";
const MAX_FRAME: u64 = 14 + 1024 * 1024;

fn main() {
    match run(&env::args().collect::<Vec<_>>()) {
        Ok(json) => println!("{json}"),
        Err(error) => {
            println!("{}", intrinsic_error_json(&error));
            process::exit(1);
        }
    }
}

fn run(args: &[String]) -> Result<String, VamError> {
    if args.len() == 2 && args[1] == "--help" {
        return Ok(format!(
            "{{\"ok\":true,\"profile\":\"{PROFILE}\",\"usage\":\"vami-inspect [--profile {PROFILE}] <file.vami>\"}}"
        ));
    }
    let mut profile = PROFILE;
    let mut path = None;
    let mut index = 1;
    while index < args.len() {
        match args[index].as_str() {
            "--profile" => {
                index += 1;
                if index >= args.len() {
                    return Err(usage("missing --profile value"));
                }
                profile = &args[index];
            }
            value if value.starts_with('-') => {
                return Err(usage(format!("unknown option: {value}")));
            }
            value if path.is_none() => path = Some(value),
            _ => return Err(usage("multiple input files")),
        }
        index += 1;
    }
    if profile != PROFILE {
        return Err(VamError {
            kind: "profile",
            message: format!("unsupported profile: {profile}"),
        });
    }
    let path = path.ok_or_else(|| usage("missing VAMI input file"))?;
    let file = File::open(path).map_err(|error| VamError {
        kind: "io",
        message: error.to_string(),
    })?;
    let mut bytes = Vec::with_capacity(MAX_FRAME as usize + 1);
    file.take(MAX_FRAME + 1)
        .read_to_end(&mut bytes)
        .map_err(|error| VamError {
            kind: "io",
            message: error.to_string(),
        })?;
    if bytes.len() as u64 > MAX_FRAME {
        return Err(VamError {
            kind: "resource",
            message: "VAMI file exceeds bounded frame size".into(),
        });
    }
    inspect_vami(&bytes).map(|report| intrinsic_success_json(&report))
}

fn usage(message: impl Into<String>) -> VamError {
    VamError {
        kind: "usage",
        message: message.into(),
    }
}

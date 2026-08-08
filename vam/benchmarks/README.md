# VAM semantic parity harness

`semantic_parity.py` is an optional diagnostic harness for VAM backend parity.
It compares the Python oracle with the native `vam0-inspect` CLI across the
same golden fixture programs encoded as `VAM0` and/or `VAMD` frames.

This is **not** a performance claim and not a speedup benchmark. The elapsed
values printed by the script are only operational timing for the harness run.
Do not use this output to claim that one backend is faster than another.

## What it checks

For each selected fixture and frame format, the script compares these semantic
fields:

- `ok`
- `profile`
- `instruction_count`
- `pc`
- `trace`
- `registers`
- `certs`
- `obstructions`

The Python side decodes the generated frame, executes the decoded program, and
builds a canonical report. The native side writes the same frame to a temporary
file and calls `vam0-inspect`.

## Usage

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 vam/benchmarks/semantic_parity.py
```

Useful smoke run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 vam/benchmarks/semantic_parity.py --limit 2
```

Run only dense `VAMD` parity:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 vam/benchmarks/semantic_parity.py --format vamd
```

Use a prebuilt native binary explicitly:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 vam/benchmarks/semantic_parity.py \
  --native-bin vam/native/target/debug/vam0-inspect
```

Use Cargo instead of a prebuilt binary:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 vam/benchmarks/semantic_parity.py --cargo
```

`--cargo` may update Cargo build artifacts. The default mode prefers the
existing `vam/native/target/debug/vam0-inspect` binary when present and falls
back to `cargo run` only when no binary exists.

## Status

- Optional; not required by the complete verification suite unless the suite runner later decides
  to promote it.
- Safe by default: encoded frames are written under a temporary directory.
- No external dependencies beyond Python stdlib, project imports, and the native
  CLI/Cargo toolchain.
- Designed as a no-overclaim parity ledger, not a native-speed benchmark.


## Battle timing harness

`battle_benchmark.py` is a local timing diagnostic for larger synthetic VAM programs. It measures current surfaces, not superiority:

- Python reference `execute()`;
- Python `optimize()`;
- `VAM0` / `VAMD` encode and decode;
- native `vam0-inspect` process-level inspection for both frame formats.

Default run:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. \
  python3 vam/benchmarks/battle_benchmark.py \
  --blocks 16,64,128,256,512 --repeats 3 \
  --json-out data/benchmarks/vam_battle_latest.json
```

Boundary string: `local-timing-diagnostic-not-speedup-claim`. Treat native CLI rows as process-level timings; they include process startup and JSON reporting overhead.

Current local artifact `data/benchmarks/vam_battle_latest.json` includes 512-block rows after the Python optimizer switched definition-object capture from repeated prefix execution to one-pass snapshots. This is a local regression diagnostic only, not a speedup or native-performance claim.

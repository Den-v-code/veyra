# VAM v1.7 — Optimized VAM0 frame emission boundary

**Status:** implemented bounded checkpoint.
**Scope:** native CLI emission of an optimized `VAM0` frame after the existing bounded optimizer slice.

## Purpose

VAM v1.7 turns the report-only native optimizer result into a concrete `VAM0` frame artifact for the narrow case where the input is already `VAM0` and the requested optimizer slice is exactly `observer-alias-v1`.

The intended pipeline is:

```text
VAM0 frame -> Rust decoder -> bounded native optimizer -> optimized IR -> VAM0 frame
```

This is a backend artifact boundary, not a speed milestone and not a proof of optimizer correctness.

## CLI contract

The bounded emission command is:

```bash
vam0-inspect --optimize observer-alias-v1 --emit-optimized-vam0 out.vam0 in.vam0
```

Required behavior:

- `--emit-optimized-vam0` requires `--optimize`;
- emission requires exact slice `observer-alias-v1`;
- input frame magic must be `VAM0`;
- emitted bytes are a normal `VAM0` frame encoding the optimized instruction IR;
- the JSON report keeps the semantic `optimized_report` without embedding raw bytes.

## Emitted metadata

When emission succeeds, the top-level JSON includes `emitted_frame` with bounded metadata:

```json
{
  "magic": "VAM0",
  "version": 1,
  "boundary": "optimized-ir-to-vam0-frame",
  "path": "out.vam0",
  "bytes": 123,
  "payload_len": 109,
  "instruction_count": 4,
  "crc32": "deadbeef",
  "source": "native-optimized-instructions"
}
```

The report deliberately does not include `optimized_frame` or `optimized_bytes` fields. Tests decode the written frame and compare the resulting instruction IR plus semantic report against the Python oracle.

## VAMD boundary

VAMD optimizer input remains accepted for semantic report-only parity, but v1.7 does not emit optimized VAMD frames.

For this checkpoint:

- `--emit-optimized-vam0 ... in.vamd` rejects with `unsupported-profile`;
- no VAMD output file is written;
- VAMD-to-VAM0 conversion is not claimed;
- optimized VAMD binary layout, CRC behavior, and dense re-encoding remain future work.

## Evidence boundary

The implemented tests check:

- native VAM0 emission succeeds and writes a decodable VAM0 frame;
- the emitted frame decodes to the Python optimizer's optimized instruction IR;
- native inspection of the emitted frame matches the optimized semantic report;
- VAMD emission rejects without writing an artifact;
- emission without optimizer and emission with legacy slice alias reject.

This is bounded regression evidence only. It is not proof-grade optimizer correctness, not a native performance backend, not a compiler verification result, and not VAMD frame emission.

## Next pressure

The next honest backend pressure is a witness/metamorphic parity ledger that records optimizer evidence without pretending to be a proof assistant. Only after that should broader emitted-frame families or performance backends be considered.

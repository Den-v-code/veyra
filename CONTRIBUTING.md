# Contributing to Veyra

Thank you for helping improve Veyra. Contributions to code, proofs,
documentation, counterexamples, and reproducibility are welcome.

## Before starting

1. Read `README.md` and `docs/102_foundational_gap_audit.md`.
2. Search existing issues and pull requests before proposing overlapping work.
3. Open a design issue before a large semantic, proof, or public API change.
4. Keep every claim within the exact observer, doctrine, ledger, and finite or
   all-depth scope that supports it.

Security-sensitive reports must follow `SECURITY.md`, not a public issue.

## Development setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Run the onboarding checks:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -m pytest -q tests/test_axiom_kernel.py tests/test_approx_resonance.py
python -m ruff check src tests
```

Some proof and native checks additionally require the pinned Lean version,
Rust, or SageMath. See `README.md` and `proofs/lean/README.md`.

## Contribution standards

### Claims and proofs

- Label additions as definitions, bounded certificates, checked proof
  artifacts, relative results, candidates, or open questions.
- Do not infer a general theorem from finite test coverage.
- State assumptions, dependencies, failure modes, and non-claims next to the
  result.
- Add adversarial cases or counterexamples when a boundary can be tested.
- Update `THEOREMS.md` and `NOTATION.md` whenever a public statement or symbol
  changes.
- Keep proof-source and digest bindings exact where an existing contract
  requires them.

### Code

- Prefer small, deterministic functions with explicit error paths.
- Preserve resource limits and fail-closed validation.
- Add tests for normal, boundary, malformed, and hostile inputs.
- Do not commit caches, generated binaries, credentials, or local paths.
- Keep active source and documentation files within the project's 300-line
  hygiene limit; split modules when needed.

### Documentation

- Write for readers without access to unpublished context.
- Use repository-relative paths.
- Separate established results from proposals and future work.
- Update `CHANGELOG.md` for user-visible behavior or public mathematical
  status changes.

## Testing

Run the narrowest relevant checks while developing. Before requesting review,
run at least:

```bash
python -m ruff check <changed-python-paths>
python -m pytest -q <relevant-test-paths>
git diff --check
```

If all optional prerequisites are installed and the change affects shared
semantics, run:

```bash
make verify
```

State exactly which checks ran, their results, and which checks did not run.

## Pull requests

A pull request should include:

- a concise problem statement;
- the chosen solution and alternatives considered;
- mathematical scope, assumptions, and non-claims;
- tests and proof checks performed;
- documentation and registry changes;
- compatibility or migration notes when relevant.

Keep unrelated refactors separate. Review may request a smaller proof surface,
additional counterexamples, or narrower wording before acceptance.

By contributing, you agree that your contribution is licensed under the MIT
License in `LICENSE` and that you will follow `CODE_OF_CONDUCT.md`.

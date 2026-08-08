# Notebooks

Notebook artifacts are generated views over tested Veyra modules.

## Layout

| Path | Role |
|---|---|
| `generated/` | Rebuilt by `make notebooks` from executable theorem-card data. |

## Rules

1. Treat notebooks as presentation artifacts; code truth lives in `src/` and tests.
2. Regenerate after changing theorem cards or Sage facade exports.
3. Keep generated markdown previews with notebooks for diff-friendly review.
4. Notebook claims must point back to tests, docs, or registry entries.

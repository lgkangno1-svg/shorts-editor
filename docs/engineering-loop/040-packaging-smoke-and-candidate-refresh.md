# 040 — Packaging smoke test and candidate refresh

## Audit

- Stable baseline: `main` at `2b0dd0a` (PR #24 causal-shadow QC fixture).
- CI previously installed the project editable and ran pytest, but never built or imported the distributable wheel. A packaging regression could therefore pass CI and fail for an end user.
- Runtime code is unchanged in this loop.

## Change

CI now builds sdist/wheel with `python -m build`, force-installs the generated wheel without dependencies, and imports `shorts_editor` on both Python 3.10 and 3.12. This adds a packaging/release smoke gate without production runtime cost.

## Commercial-model refresh (2026-09-18)

- Netflix VOID remains Apache-2.0 and relevant for interaction-aware object/effect deletion, but the official quick start still targets 40GB+ VRAM; keep as benchmark-only until representative hardware/quality evidence exists.
- `caiovicentino1/VOID-Netflix-HLWQ-Q5` advertises Apache-2.0 and 24GB operation, but is a third-party quantized derivative. Do not production-integrate before provenance, reproducibility and quality comparison against official VOID are verified.
- MiniMax-Remover weights are CC-BY-NC-4.0: production excluded.
- ACut LaMa ONNX is Apache-2.0 but still-image/fixed-512 inference; it is not evidence of a temporal-quality upgrade over the current video path.

## Acceptance

Keep this CI-only change only if pull-request CI passes on both supported Python versions. Do not claim local or model benchmarks: none were run in this loop. Merge only after green PR CI, then verify a post-merge `main` run.

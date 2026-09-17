# Loop 035 — commercial video-removal candidate audit

Date: 2026-09-17

## Stable baseline

- Baseline: `main` at `96db995894fca479fe50c6e5b23ef5152b80d221`.
- No production code changed in this loop.
- Local test execution was attempted but the automation container could not resolve `github.com`; no local test result is claimed.

## Fresh candidate review

### SVOR — keep as benchmark candidate

- Upstream: `xiaomi-research/svor`.
- License: Apache-2.0 at repository level.
- Focus: stable video object removal under imperfect masks; explicitly relevant to mask robustness and temporal reconstruction.
- Decision: commercially compatible enough for an isolated benchmark candidate, but **not production-approved yet**. Before integration, verify all checkpoint/transitive-component licenses and benchmark quality, VRAM, latency, and failure behavior against the current stable pipeline on owned fixtures.

### Netflix VOID — keep as high-resource benchmark candidate

- Upstream: `Netflix/void-model` / Hugging Face VOID weights.
- License: Apache-2.0.
- Focus: video object + interaction deletion using CogVideoX-based inpainting.
- Decision: retain as an optional high-resource comparison target only; do not add a production dependency without measured benefit and resource-budget validation.

### DiffuEraser — exclude from production for now

- Repository code is Apache-2.0, but the published implementation uses ProPainter as a prior and explicitly requires compliance with ProPainter licensing.
- Decision: production exclusion remains fail-closed until a fully commercial-safe dependency path is demonstrated.

### EffectErase / MiniMax-Remover — exclude

- Published model/data terms include CC BY-NC 4.0 / non-commercial restrictions.
- Decision: not eligible for the commercial production path.

## Global audit note

The current tree is intentionally small and modular (`benchmark`, `chunking`, `local_vsr`, `masks`, `ocr_adapters`, `precision_masks`, `qc`, `routing`, `subtitles`, `tracks`, `windows`). Recent changes have concentrated on numeric boundary validation. No new code defect was accepted without an executable regression test in this run.

## Gate for next implementation

Only promote a new remover/tracker/masker when all are true:
1. code + weights + transitive runtime dependencies are commercially usable;
2. deterministic fixture benchmark beats or complements the stable baseline on temporal consistency/removal residual/protected-region damage;
3. runtime/VRAM cost is documented;
4. failure is fail-closed and fallback behavior is tested;
5. CI is green before merge and post-merge CI is verified.

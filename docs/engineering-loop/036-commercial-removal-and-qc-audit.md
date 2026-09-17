# 036 — Commercial removal and QC audit

Date: 2026-09-17
Baseline: `main` at `98a0c35d21e1b0035b873dc4abf5b8ee307b35c3`

## Repository audit

- Reviewed the current module/test/package tree after the mask-geometry promotion.
- No production code change is justified in this loop. The recent numeric-boundary fixes are already on `main`; changing additional validation without a demonstrated failing fixture would add churn rather than measurable quality.
- `qc.py` already accepts `numbers.Real`, rejects booleans/non-finite/out-of-range values, and fails closed on protected-region damage and residuals.
- No test or benchmark was run in this audit-only loop; therefore no test-pass or performance claim is made.

## Commercial candidate review

- Netflix VOID remains Apache-2.0 for code/model and is relevant for interaction-aware removal plus optional flow-warped temporal refinement. Official model guidance requires 40GB+ VRAM, so it remains a high-quality benchmark/escalation candidate rather than a default local engine.
- HigherHu/SVOR remains relevant for imperfect masks, abrupt motion, shadows/reflections and flicker robustness. Do not integrate until the complete checkpoint/dependency license chain and a reproducible fixture benchmark are verified.
- OpenCV/LaMa Apache-2.0 ONNX remains a useful low-cost still/window inpainting candidate, but frame-independent use must not be promoted as temporal reconstruction without flicker benchmarking.
- MiniMax-Remover weights remain CC-BY-NC-4.0 and EffectErase remains CC BY-NC 4.0; both stay excluded from production.
- DiffuEraser is not accepted as production-safe merely because its repository is Apache-2.0: it inherits/uses ProPainter and requires the downstream third-party license chain to be cleared first.

## Decision

Stable production code is unchanged. Next useful engineering work is evidence-driven: benchmark a commercially cleared candidate against the paired-video fixtures and existing QC metrics, including residual, boundary, protected-region damage and temporal flicker, before adding dependencies or routing changes.

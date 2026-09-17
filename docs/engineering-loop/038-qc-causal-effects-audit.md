# 038 — QC causal-effects and removal candidate audit

Date: 2026-09-18
Baseline: `main` at `fe51bb63466d4a639701d833793ca84310fd0ae8`

## Repository / CI review

- PR #22 head `84c3b3921493105e5f57e2f9812c9ab00bbc49c6` completed `cleanup-core-ci` run #109 successfully before its merge.
- The squash-merged main commit currently has no pull-request workflow run; no post-merge CI result is claimed.
- Re-reviewed `benchmark.py` and `tests/test_benchmark.py`. The paired benchmark already compares candidate output to clean references outside an expanded target mask, so shadows/reflections/other target-induced effects outside the mask can surface as protected-region damage rather than being silently ignored.
- Existing gates cover visible residual, boundary spill, protected-region damage, temporal instability, malformed video/mask shapes, non-finite masks, non-binary masks, and weak fixtures.
- No production defect with a demonstrated regression fixture was found in this run. Runtime code is unchanged.
- No local tests or benchmarks were executed in this run; no local pass/performance claim is made.

## Fresh commercial research

- `xiaomi-research/svor` remains Apache-2.0 at repository level. Its MUSE window-union mask strategy, denoising-aware segmentation, and training with degraded masks directly target abrupt motion, defective masks, shadows/reflections, and flicker. Keep as a benchmark candidate pending checkpoint/transitive-license and resource verification.
- `Netflix/void-model` remains Apache-2.0 and Hugging Face publishes Apache-2.0 VOID weights. Its interaction-aware removal remains a useful high-quality comparison target, not a default backend without measured resource/quality benefit.
- `YigitEkin/BeyondMasks` now provides an ECCV 2026 paired benchmark plus CORE evaluation aimed specifically at target-induced shadows, reflections, illumination, translucency and dynamic traces. Its evaluation concepts are relevant to extending project QC, but no external benchmark dependency is added without license/data/runtime review and a reproducible local evaluation plan.
- `QuantumWars/propainter-delogo` documents useful engineering patterns (shot-aware windows, crop-only processing, mask dilation/feathering, flat-black passthrough), but it depends on separately licensed ProPainter. Treat those patterns as design references only; do not import its ProPainter production path without commercial clearance.
- DiffuEraser remains excluded from the commercial production path because its published implementation uses ProPainter and explicitly requires compliance with that separate license.

## Decision

Stable runtime code stays unchanged. The next justified implementation should be fixture-backed QC/benchmark work: add a secondary-effect fixture (shadow/reflection outside the target mask) and prove the existing protected-region gate catches failed causal cleanup before changing scoring or integrating a model. Any new backend must also record VRAM, wall time, checkpoint license, transitive licenses, residual, boundary damage, protected-region preservation and temporal flicker versus the stable baseline.

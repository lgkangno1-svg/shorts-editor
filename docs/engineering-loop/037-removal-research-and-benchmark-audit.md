# 037 — Removal research and benchmark audit

Date: 2026-09-17
Baseline: `main` at `399f52305bc13a7c9942f269e6b4f0ef6dd64c56`

## Repository audit

- Reviewed recent main history through PR #21 and the paired-video benchmark implementation.
- No production change is justified in this loop: current benchmark already gates residual removal, boundary artifacts, protected-region damage and temporal flicker, and recent numeric-boundary fixes cover the main NumPy/OpenCV interoperability seams.
- Searched the indexed tree for TODO/FIXME/NotImplemented/pass markers and found no actionable dead-code marker.
- Packaging remains intentionally minimal: runtime has no mandatory dependencies; NumPy benchmark and RapidOCR remain extras.
- No local benchmark/test execution was performed in this loop. PR CI is the only test evidence to record if it runs.

## Fresh commercial candidate review

- `xiaomi-research/svor` remains Apache-2.0 at repository level and now explicitly points to the PROVE removal benchmark. Its MUSE strategy for imperfect/moving masks and flicker resistance is directly relevant, but checkpoint and transitive dependency licensing plus resource cost still require fixture-backed validation before production integration.
- `Netflix/void-model` remains Apache-2.0 and a high-quality interaction-aware comparison target, but its large CogVideoX-based resource footprint makes it an escalation/benchmark candidate rather than the default local backend.
- `knightyxp/VideoCoF` is Apache-2.0 at repository level and supports object removal/long-video editing. It is not production-approved here because its Wan/VideoX-Fun-derived runtime/checkpoint chain and GPU cost have not been fully cleared or benchmarked against this project.
- Adobe Object-WIPER is technically relevant because its proposed metric explicitly combines temporal foreground consistency, foreground/background coherence and removal dissimilarity. Adobe's publication page says source code/models will be publicly available; without a verified released implementation/license chain, it is research inspiration only, not a dependency candidate.
- EffectErase remains CC BY-NC 4.0 and MiniMax-Remover published weights remain non-commercial; both stay excluded from production.

## Decision

Stable runtime code is unchanged. The next justified implementation should be benchmark infrastructure or an isolated adapter only when a commercially cleared candidate can be run on owned paired fixtures. Prefer measuring removal residual, boundary damage, protected-region preservation, temporal flicker, VRAM and wall time against the current baseline before routing any production traffic to a new backend.

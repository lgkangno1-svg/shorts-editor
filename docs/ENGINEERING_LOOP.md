# Engineering Loop Log

## Loop 008 — 2026-09-15

### Repository audit
- Development branch contained only `README.md` and the Vmake-parity PRD; actual removal-engine source was absent.
- Stable branch was left unchanged.

### External technique review
- SAM2 remained a commercially usable tracking/segmentation candidate (Apache-2.0).
- ProPainter-based implementations were excluded from production because upstream licensing is non-commercial.

### Promotion decision
**NO CODE PROMOTION.** No executable implementation was available.

## Loop 009 — 2026-09-16

### Repository audit
- Rechecked `feature/vmake-parity-prd`; implementation source was still absent.
- No benchmark or regression test was claimed or run.
- Synthetic clean/overlaid twin clips were selected as the future objective benchmark pattern.

### Promotion decision
**DOCUMENTATION ONLY.** Stable code remained untouched.

## Loop 010 — 2026-09-16

### Implemented on successor branch
- Created `feature/vmake-parity-core` from the PRD branch rather than modifying stable `main`.
- Added an installable Python core with deterministic cost-aware routing: easy jobs -> local fast, medium jobs -> local temporal, hard/uncertain-mask jobs -> Smart Pro.
- Added fail-closed QC primitives for residuals, temporal flicker, mask boundaries and protected-region damage.
- Added validation tests for routing, invalid inputs and QC safety gates.
- Added GitHub Actions CI for Python 3.10 and 3.12.

### Commercial-license review
- SAM2 remains eligible for future mask propagation: upstream code/checkpoints are Apache-2.0.
- ProPainter remains excluded from production: upstream explicitly declares non-commercial-only use.
- DiffuEraser is not production-eligible as published when using its ProPainter prior; its Apache-2.0 repository does not remove the upstream ProPainter restriction. It may only be reconsidered with a commercially clean replacement prior and full dependency audit.

### Evidence / limitations
- This loop establishes testable architecture, not removal-quality parity yet.
- Local execution was attempted but the execution environment could not resolve github.com, so **no local pytest/benchmark result is claimed**.
- CI was added so pushed commits can provide independent execution evidence; CI status must pass before promotion.
- No model weights or non-commercial code were added.

### Promotion decision
**DO NOT MERGE TO STABLE YET.** Keep on `feature/vmake-parity-core` until CI passes and real video fixtures/quality benchmarks exist.

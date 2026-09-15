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

### promotion decision
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
- DiffuEraser is not production-eligible as published when using its ProPainter prior; its Apache-2.0 repository does not remove the upstream ProPainter restriction.

### Promotion decision
**DO NOT MERGE TO STABLE YET.** Keep on `feature/vmake-parity-core` until CI passes and real video fixtures/quality benchmarks exist.

## Loop 011 — 2026-09-16
- Added bounded QC escalation: Local Fast -> Local Temporal -> Smart Pro; terminal failure requires manual review.
- Tests added; no passing CI/local run claimed for this head.

## Loop 012 — 2026-09-16
- Added deterministic scene-aware chunk planning so temporal inference does not cross shot boundaries.
- Tests added; stable remained unchanged.

## Loop 013 — 2026-09-16
- Previous scene-aware head was verified passing GitHub Actions on Python 3.10/3.12.
- Added padded crop geometry to reduce compute for small removal regions; new head CI was not yet claimed.

## Loop 014 — 2026-09-16
- Fixed routing bug where duration was ignored: Local Fast is now limited to short/simple jobs; long easy clips use Local Temporal.
- Regression test added; no new-head pass claim.

## Loop 015 — 2026-09-16
- Added overlap-safe temporal context windows while emitting every frame exactly once and respecting scene cuts.
- New tests committed; no pass claim for the new head.

## Loop 016 — 2026-09-16
- Added tracking fail-safe signals using confidence and center displacement; switched motion detection from top-left to box center.
- SAM2/VOID/SVOR remain commercial candidates; ProPainter/DiffuEraser default pipeline remains excluded.
- New tests committed; stable unchanged.

## Loop 017 — 2026-09-16

### Repository audit and implementation
- Found tracking-risk logic treated displacement between sparse keyframes as if it occurred in one frame. A valid target moving gradually over ten frames could therefore be falsely classified as tracker drift and trigger unnecessary re-detection/escalation.
- Added `max_center_velocity()` and changed risk gating to normalized displacement per frame while retaining raw `max_center_jump()` for diagnostics.
- Added regression coverage proving a 0.4 normalized displacement over ten frames is treated as 0.04/frame rather than an abrupt 0.4-frame jump.

### External review
- Hugging Face connector model search failed during this loop, so no model was adopted from unverified metadata.
- Existing commercial-policy gate remains unchanged: SAM2/VOID/SVOR are candidates pending benchmarks; non-commercial ProPainter-derived production paths remain excluded.

### Evidence / limitations
- Code and regression test are committed. No passing local/CI execution is claimed for this new head yet.
- Stable `main` remains unchanged pending CI and objective paired-video quality benchmarks.

### promotion decision
**KEEP ON DEVELOPMENT BRANCH.** Next highest-value gate remains executable paired clean/overlay video benchmarking plus objective quality scoring.

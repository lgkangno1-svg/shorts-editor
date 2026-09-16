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
- Fixed sparse-keyframe tracking risk by measuring normalized center displacement per frame rather than raw sample-to-sample displacement.
- Regression coverage added; no new-head CI pass claimed.

## Loop 018 — 2026-09-16

### Repository audit and implementation
- Found an API-semantics defect left by Loop 017: `has_tracking_risk(max_center_jump=...)` was still named as a raw-jump threshold even though the implementation compared per-frame velocity. This could cause future callers to configure a threshold in the wrong units and weaken the destructive-edit fail-safe.
- Introduced explicit `max_center_velocity` as the preferred threshold and retained `max_center_jump` only as a compatibility alias. Supplying both is rejected rather than guessed.
- Added regression coverage for the new keyword, legacy compatibility, sparse-keyframe behavior, and ambiguous dual-threshold calls.

### External review
- SAM2 remains Apache-2.0 and suitable for future video mask propagation.
- Netflix VOID remains Apache-2.0 and a high-quality hard-case candidate, but its 40GB+ class GPU requirement keeps it out of the default local path.
- CLEAR and LTX2.3-ICEdit-Insight surfaced as Apache-2.0 subtitle/watermark restoration candidates; they are research candidates only until upstream provenance, runtime cost, and paired-video quality are benchmarked.
- MiniMax-Remover weights are CC-BY-NC-4.0 and therefore excluded from production despite Apache-2.0 source code.

### Evidence / limitations
- Source and tests were committed on `feature/vmake-parity-core`. No local or CI pass is claimed for this new head.
- Stable `main` remains unchanged; objective paired clean/overlay video benchmarks are still required before promotion.

### promotion decision
**KEEP ON DEVELOPMENT BRANCH.**

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

### Repository audit and implementation
- Audited the complete successor branch; it remains small with no duplicate/dead modules identified yet.
- Added bounded QC escalation: failed Local Fast jobs move to Local Temporal, failed Local Temporal jobs move to Smart Pro, and failed Smart Pro jobs stop for manual review instead of looping or silently shipping a bad render.
- Added four tests covering escalation order, failed fast escalation, terminal Smart Pro failure, and no retry after a passing QC result.

### External review
- Netflix VOID remains the cleanest hard-case candidate found: official GitHub/model are Apache-2.0, with Pass 2 intended to improve temporal consistency, but official guidance still targets 40GB+ VRAM.
- LaMa Apache-2.0 variants remain useful candidates for a cheap still-frame/local-fast baseline, but must be benchmarked for temporal flicker before adoption.
- MiniMax-Remover weights are non-commercial and remain excluded from production.

### Evidence / limitations
- Tests were added but no passing CI/local run is claimed in this loop.
- Stable `main` remains unchanged until executable CI and video-quality evidence exist.

### Promotion decision
**KEEP ON DEVELOPMENT BRANCH.** Next highest-value slice is the actual job pipeline plus synthetic clean/overlay video fixtures and measurable QC.

## Loop 012 — 2026-09-16

### Repository audit and implementation
- Re-audited the full successor branch; no dead/duplicate implementation modules were found.
- Added a deterministic scene-aware chunk planner so temporal engines never process across known shot boundaries and every inference window stays under its frame budget.
- Added tests for bounded chunking, scene-cut isolation and invalid-cut rejection.

### External review
- Reconfirmed Netflix VOID as Apache-2.0 and suitable only for routed hard cases due to its official 40GB+ VRAM guidance and up-to-197-frame design.
- Reconfirmed MiniMax-Remover weights are CC-BY-NC-4.0 and excluded from commercial production.
- ProPainter-dependent projects remain architecture references only, not production dependencies.

### Evidence / limitations
- No passing local or CI run is claimed in this loop; tests were committed but execution evidence is still absent.
- Stable `main` remains unchanged.

### Promotion decision
**KEEP ON DEVELOPMENT BRANCH.** Next slice: connect chunk planning to a real video job executor and add synthetic video fixtures/quality measurements.

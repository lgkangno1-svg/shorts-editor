# Engineering Loop Log

## Loop 008 — 2026-09-15

### Repository audit
- Development branch contained only `README.md` and the Vmake-parity PRD; actual removal-engine source was absent.
- Stable branch was left unchanged.

### External technique review
- SAM2 remained a commercially usable tracking/segmentation candidate (Apache-2.0).
- ProPainter-based implementations were excluded from production because upstream licensing is non-commercial.

### promotion decision
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

## Loop 019 — 2026-09-16
- Fixed a fail-open QC defect: NaN metric/threshold values previously bypassed range comparisons and could produce a passing decision. QC now rejects all non-finite inputs; regression tests cover NaN and infinities.
- External review reconfirmed Apache-2.0 VOID/SVOR as candidates and ProPainter-dependent paths as unsuitable for the commercial default. BeyondMasks/CORE is a promising 2026 paired object-removal benchmark/evaluator to assess before adoption.
- Changes are committed only on `feature/vmake-parity-core`; no local/CI pass is claimed for this head and `main` remains unchanged.

## Loop 020 — 2026-09-16
- Global validation audit found the same non-finite fail-open class in pre-inference routing: NaN normalized signals could survive validation and collapse the difficulty clamp toward an easy route; NaN duration also bypassed the positive-duration check.
- Routing now rejects NaN and infinities for every normalized signal and duration before engine selection; regression tests cover both signal and duration inputs.
- Research refresh: Netflix VOID and Xiaomi SVOR remain Apache-2.0 commercial candidates; MiniMax-Remover weights remain excluded (CC-BY-NC-4.0). EffectErase and D2DF are promising 2026 candidates but require dependency/license-chain and paired-video benchmarking before production adoption.
- No local or CI pass is claimed for this head. `main` remains unchanged pending objective video benchmarks and green CI.

## Loop 021 — 2026-09-16
- Global fail-closed audit found non-finite validation gaps in tracking: NaN bounding-box coordinates/sizes and NaN confidence could pass Python range checks; non-finite risk thresholds could also weaken the destructive-edit guard.
- Bounding boxes, track confidence, and tracking-risk thresholds now reject NaN/infinities. Regression coverage was added for each input class.
- Research refresh: VOID and SVOR remain Apache-2.0 candidates. D2DF is Apache-2.0 but its draft-guided mode acknowledges ProPainter, so dependency-path isolation is required; EffectErase uses SAM2.1 masks and remains research-only until its full dependency/weight license chain is verified. MiniMax-Remover weights remain excluded as CC-BY-NC-4.0.
- No local or CI pass is claimed for this head. `main` remains unchanged pending green CI and paired-video benchmarks.

## Loop 022 — 2026-09-16
- Global validation audit found temporal window counts accepted booleans and fractional values; Python could then fail later inside `range()` or silently treat `True` as one frame. `max_frames` and `overlap_frames` now require real integer frame counts and reject booleans.
- Regression tests cover fractional/boolean window parameters. No local or CI pass is claimed for this new head; stable `main` remains unchanged.
- Research refresh reconfirmed Apache-2.0 VOID and SVOR as commercial candidates. Recent ProPainter wrappers expose useful windowed/shot-aware/low-VRAM engineering patterns, but their ProPainter dependency remains excluded from the production model path because upstream licensing is separate/non-commercial.

## Loop 023 — 2026-09-16
- Global frame-index audit found the same type-safety gap in scene-aware chunking: fractional frame counts/cuts could fail late in arithmetic/range operations, while booleans were silently accepted as integer frame indices.
- `FrameChunk` boundaries and `plan_chunks` frame counts, limits, and scene-cut indices now reject booleans and non-integers up front; regression coverage was added for each class.
- Research refresh: Netflix VOID and Xiaomi SVOR remain Apache-2.0 commercial candidates. VOID's interaction-aware quadmask/two-pass refinement remains a Smart-Pro candidate rather than a local default because the official model card recommends 40GB+ VRAM. MiniMax-Remover remains excluded because its weights are CC-BY-NC-4.0. DiffuEraser remains unsuitable for the commercial default while its published pipeline depends on ProPainter licensing.
- No local or CI pass is claimed for this new head. `main` remains unchanged pending green CI and objective paired-video benchmarks.

## Loop 024 — 2026-09-16
- Global QC/escalation audit found `QCDecision` itself trusted caller-supplied values. A malformed manually constructed decision could carry NaN/out-of-range scores, non-boolean pass flags, or an empty reason into escalation even though `evaluate_qc` is fail-closed.
- `QCDecision` now validates boolean pass state, finite [0,1] score, and non-empty reason; regression tests cover malformed decision inputs.
- Research refresh reconfirmed Apache-2.0 SAM2/SAMURAI for mask tracking and VOID/SVOR for advanced removal. VOID remains Smart-Pro class due to its documented 40GB+ GPU requirement. MiniMax-Remover weights remain excluded as CC-BY-NC-4.0; DiffuEraser's published ProPainter-dependent path remains excluded from the commercial default.
- No local or CI pass is claimed for this new head. `main` remains unchanged pending green CI and objective paired-video benchmarks.

## Loop 025 — 2026-09-16
- QC metric and threshold type-safety was tightened so boolean values cannot masquerade as numeric 0/1 quality signals; regression coverage was added.
- This head (`eb596c5`) was subsequently verified by GitHub Actions run 35081562129: `cleanup-core-ci` completed successfully on the branch.

## Loop 026 — 2026-09-16
- Global audit found no additional low-risk source change with evidence strong enough to justify modifying the currently green core. `main` remains only the standalone repository bootstrap, so there is still no executable stable quality baseline against which real video quality can honestly be compared.
- External refresh reconfirmed official Netflix VOID and its Hugging Face weights as Apache-2.0; VOID remains Smart-Pro/research class because of its high GPU requirement. Official SAM2 code/checkpoints remain Apache-2.0 and suitable for mask propagation. MiniMax-Remover remains excluded from production because the surfaced weights are non-commercial. DiffuEraser is not promoted because its published implementation uses ProPainter as a prior and explicitly requires compliance with that upstream license.
- A useful implementation pattern from recent ProPainter wrappers is windowed, shot-aware, crop-only processing; the architecture already has scene-aware chunks, padded crops, and temporal windows, so no model dependency was imported merely to duplicate those ideas.
- No new benchmark was run in this loop. Existing CI evidence is limited to the current pre-documentation head; objective paired clean/overlay video fixtures remain the promotion blocker.

### promotion decision
**AUDIT/DOCUMENTATION ONLY. KEEP STABLE CODE UNCHANGED.**

## Loop 027 — 2026-09-16
- Escalation audit found boundary inputs were less strict than routing/QC: arbitrary strings or mapping-like QC payloads could fail late or expose inconsistent error behavior. `next_engine`/`decide_escalation` now fail closed unless given the declared `Engine` and `QCDecision` types; regression tests cover malformed inputs.
- Research refresh reconfirmed Netflix VOID and Xiaomi SVOR as Apache-2.0 advanced-removal candidates. A recent watermark-removal implementation reinforces crop-only, shot-aware, windowed processing as a practical low-VRAM pattern already represented in this core; its ProPainter dependency is not imported into the commercial production path.
- Changes are isolated to `feature/vmake-parity-core`. No local test run was available in this environment, and no GitHub Actions run was present for head `6cc5e88` when checked, so no passing-test claim is made. `main` remains unchanged.

### promotion decision
**KEEP ON DEVELOPMENT BRANCH PENDING CI AND PAIRED-VIDEO BENCHMARKS.**

## Loop 028 — 2026-09-17
- Re-audited current `main` at `61297b8`: the executable cleanup core and the integral chunk-input normalization are now present on stable. The chunk planner validates all frame indices through one `numbers.Integral` gate, so no duplicate low-risk type patch was justified.
- Packaging remains intentionally minimal (`setuptools`, zero runtime dependencies; NumPy/RapidOCR are optional), which reduces production dependency risk. No dead dependency was added or removed in this pass.
- Research refresh: official Netflix VOID remains Apache-2.0 and is suitable only as a high-resource Smart-Pro candidate; official SAM2 code/checkpoints remain Apache-2.0 for mask propagation. A new MIT bidirectional-SAM2/Wan-VACE workflow provides useful long-video engineering ideas (81-frame chunking, bidirectional propagation, mask growth/feathering), but its full model-weight license chain was not verified, so it was not imported. SAM2Matting was explicitly rejected for production because it is CC BY-NC-SA 4.0. DiffuEraser remains excluded from the commercial default because its published pipeline uses ProPainter and requires compliance with that upstream license.
- No code change or benchmark was run in this pass. GitHub reported no pull-request workflow run for current main head `61297b8` via the available commit-run query, so this loop makes no new CI-pass claim. Objective paired clean/overlay video benchmarks remain the main quality-promotion blocker.

### promotion decision
**AUDIT/DOCUMENTATION ONLY. STABLE CODE UNCHANGED.**

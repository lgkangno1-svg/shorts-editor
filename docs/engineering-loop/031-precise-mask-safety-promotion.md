# Loop 031 — precise mask safety promotion

Date: 2026-09-16

## Audit finding
- Real-video work on the Vmake-parity branch showed that treating a full subtitle-line rectangle as the destructive removal mask can damage moving foreground detail.
- The development fix introduced normalized fine mask polygons and changed coarse consensus rectangles to guidance-only by default.
- Global spot-checks found no new hard-coded local paths, TODO/FIXME/HACK markers, or new production model dependency in this change.

## Change promoted
- Added `PreciseMaskPolygon`, confidence filtering, same-frame duplicate suppression, pixel clipping and frame-bounded VSR manual corrections.
- Coarse consensus tracks now require explicit `coarse_track_mask=True` before becoming destructive VSR regions.
- Precise masks remain additive while VSR OCR stays enabled, reducing the risk that a missed glyph disables fallback detection.
- Temporal mask union controls are exposed but remain opt-in until real-video benchmarking proves a net benefit.

## Verification evidence
- Original development head `11265e4f0dff5d6669befba6fe1c28ef775af05f`: GitHub Actions run `35106878518` passed on Python 3.10 and 3.12.
- Rebased successor PR #2 head `f3feec4fb872e3e22873969832e096748f4e311c`: pull-request run `35107352402` passed on Python 3.10 and 3.12.
- Squash merge `6166cdd55d0dd621cf8bb9651403b84ccce21487`: post-merge `main` run `35107430480` passed on Python 3.10 and 3.12.
- No new full external VSR/STTN/LaMa paired-video benchmark was run in this loop; no Vmake-quality-parity claim is made.

## Commercial/offline review
- No cloud/paid API or new model dependency was introduced.
- SAM 2 remains Apache-2.0; Cutie and XMem remain MIT candidates for future mask propagation after runtime/quality benchmarks.
- ProPainter and E2FGVI remain excluded from the commercial production path because their upstream usage terms are non-commercial.

## Decision
**PROMOTED TO `main`.** The change improves destructive-mask safety with three green CI checkpoints and no added runtime/model cost. Objective paired-video quality benchmarking remains the next promotion-quality milestone.

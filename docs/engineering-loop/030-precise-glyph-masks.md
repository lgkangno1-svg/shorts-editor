# Engineering Loop 030 — precise glyph masks from real-video failure

Date: 2026-09-16
Branch: `feature/vmake-parity-core`

## Trigger
Two user-supplied 720x1280/30fps Korean-caption clips were inspected and sampled. The broad subtitle-line removal experiment visibly damaged moving foreground content (hands, banana, textured surfaces) because the coarse consensus rectangle was treated as the destructive mask.

## Implemented
- Added `PreciseMaskPolygon`, a model-agnostic normalized polygon primitive for glyph/stroke masks.
- Added fail-closed validation, duplicate suppression by same-frame IoU, confidence filtering, pixel clipping, and short-lived VSR `manual_mask_corrections` conversion.
- Changed the VSR adapter so coarse consensus tracks are **not destructive by default**. Legacy coarse keyframe masks now require explicit `coarse_track_mask=True`.
- Precise polygons are additive while VSR OCR remains enabled, so local OCR can catch missed glyphs instead of the adapter disabling detection.
- Exposed VSR scene-safe temporal mask-union controls through `VSRRunnerConfig` (`temporal_mask_union`, `temporal_mask_window`). They remain opt-in until real-video benchmarking proves that temporal union reduces misses without extra foreground damage.
- Kept the pipeline fully local/API-free; no new model dependency was added.

## Evidence
- Real fixture metadata verified locally: video-06 = 720x1280, 30 fps, 568 frames / 18.93 s; video-01 = 720x1280, 30 fps, 807 frames / 26.90 s.
- Prior 1-second local proof on video-06 completed; broad-mask visual damage was confirmed and the approach rejected.
- Focused sandbox tests for the new mask primitive and VSR bridge: **17 passed**. This is not the full repository test suite.
- Full end-to-end VSR/STTN/LaMa inference is still not available in this execution environment because the reviewed external VSR runtime/model bundle is not installed here.

## Commercial/offline policy
- No paid/cloud API was introduced.
- The VSR bridge remains external and offline; commercially compatible OCR/refinement backends can feed `PreciseMaskPolygon`.
- Non-commercial ProPainter/E2FGVI/MiniMax-remover paths remain excluded from production.

## Promotion decision
**KEEP ON DEVELOPMENT BRANCH.** The real-video defect is fixed at the adapter boundary, but stable promotion still requires full VSR runs on both supplied clips plus residual-text/flicker/outside-mask-damage measurements.

# Engineering Loop 029 — real-video subtitle fixtures

Date: 2026-09-16
Branch: `feature/vmake-parity-core`

## Fixtures exercised
- `threads-gaebalza-DdVt4P0GaMh-video-06.mp4`: 720x1280, 30 fps, about 18.9 s.
- `threads-gaebalza-DdVt4P0GaMh-video-01.mp4`: 720x1280, 30 fps, about 26.9 s.
- Both contain Korean burned-in captions around the middle/lower-middle of the portrait frame over moving, detailed foregrounds.

## What was actually run
- Sample/contact-sheet inspection on both supplied videos.
- OpenCV/Tesseract local proof-of-concept experiments on representative frames.
- A 1-second, 30-frame local removal proof of concept from video-06 completed and produced a valid MP4.
- A broad subtitle-line rectangle reconstruction experiment was rejected: it visibly smeared foreground content such as hands/banana/background texture.
- Character/glyph-sized masks preserved substantially more source content and removed most sampled caption pixels, but some missed glyphs/residuals remain.
- A second 1-second video-01 attempt did not complete within the available execution window; no success claim is made for it.
- Full VSR/STTN/LaMa model inference was not run in this environment because the reviewed VSR runtime/model bundle is not installed here.

## Defect found in the current adapter
`build_vsr_config_overlay()` converted the consensus subtitle track (a coarse subtitle-line envelope) into VSR `subtitle_region_keyframes` and enabled `sttn_skip_detection`. Upstream VSR treats those keyframes as the actual removal mask, not merely an OCR search ROI. On the supplied clips, that geometry is too broad and can destroy legitimate foreground pixels.

## Change
- Coarse consensus tracks are guidance-only by default and no longer become destructive masks.
- Legacy/manual coarse-mask behavior remains available only with explicit `coarse_track_mask=True`.
- Added conversion of fine OCR/glyph detections into short-lived additive `manual_mask_corrections` polygons.
- Duplicate overlapping detections are suppressed; corrections are bounded in time and pixels.
- VSR OCR remains enabled while precise corrections are added, allowing local VSR detection to catch misses.
- Exposed VSR's scene-safe temporal mask-union controls through the adapter.

## Commercial/offline policy
- No paid API was introduced.
- VSR remains an external reviewed MIT-licensed local runtime.
- RapidOCR/PaddleOCR/Tesseract-class commercially compatible local detection remains eligible.
- ProPainter/MiniMax non-commercial paths remain excluded from production.

## Promotion decision
Keep on the development branch. The real fixtures exposed a meaningful quality defect and justified this patch, but full end-to-end VSR quality still needs to be benchmarked on the supplied videos before stable promotion.

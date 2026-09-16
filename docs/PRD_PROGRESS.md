# Video Cleanup PRD Progress

Updated: 2026-09-16
Stable branch: `main`
Development branches: `feature/vmake-parity-core`, `feature/vmake-parity-precise-masks`, `feature/rapidocr-frame-adapter`, `feature/paired-video-benchmark`

## P0 removal core

| Capability | Status | Current implementation/evidence |
| --- | --- | --- |
| Engine-neutral routing | Implemented / stable | Local Fast / Local Temporal / Smart Pro routing with fail-closed validation |
| Subtitle OCR consensus | Implemented / stable | Multi-frame block fusion + temporal association |
| Subtitle mask stabilization | Implemented / stable | short-gap interpolation + temporal union envelope |
| Precise glyph/stroke masks | Implemented / stable | normalized frame polygons, confidence gate, duplicate suppression and frame-bounded VSR corrections |
| Coarse-mask safety | Implemented / stable | consensus subtitle rectangles are guidance-only by default; destructive coarse masks require explicit opt-in |
| Local removal execution | Integrated adapter / stable | VSR external local runner; LaMa/STTN/AUTO mapping; no paid API |
| Moving region export | Compatibility-only | coarse VSR keyframe rectangles remain available only through explicit `coarse_track_mask=True` |
| Scene-aware temporal windows | Implemented / stable | chunking/window modules avoid crossing scene cuts |
| QC/escalation primitives | Implemented / stable | residual/flicker/boundary/protected-damage gates and bounded escalation |
| Residual OCR verification | Enabled in VSR adapter | VSR `verify_removal` + quality report requested by default |
| Real OCR frame adapter | Implemented / stable | RapidOCR 3.x line output feeds tracking while `return_word_box=True` word polygons feed precise masks; NumPy-backed output is covered by tests |
| OCR runtime dependency | Optional / local | `.[ocr]` installs `rapidocr>=3.9.2,<4`; Korean is the default engine language; no paid/cloud API |
| Paired-video benchmark core | Implemented / stable | `evaluate_paired_video()` measures residual, flicker, boundary spill and protected-region damage against clean reference frames and feeds the existing fail-closed QC gate |
| Commercial video mask propagation | Candidate stage | SAM 2 (Apache-2.0), Cutie/XMem (MIT) require runtime/integration benchmarks |
| Full real-video parity benchmark | Pending fixture/runtime evidence | measurement code is stable; full external VSR/STTN/LaMa runs still need executable local runtime plus suitable reference fixtures |
| Stable promotion | Promoted | precise-mask safety PR #2, RapidOCR adapter PR #3 and paired benchmark PR #4 all passed Python 3.10/3.12 PR CI before merge |

## Commercial dependency policy

Production/default paths may use commercially compatible local components such as MIT/Apache-2.0 VSR, RapidOCR, PaddleOCR, SAM 2, Cutie, or XMem after integration validation. Non-commercial upstream code/weights such as ProPainter and E2FGVI remain excluded from production dependencies. VOID/SVOR remain research candidates until runtime and paired-video quality justify their cost.

## Current quality statement

`main` is the stable executable baseline. Subtitle OCR has a concrete local RapidOCR path, broad consensus boxes are non-destructive by default, and objective paired-reference scoring is now implemented. Vmake-quality parity is **not yet claimed**. The next evidence milestone is running the benchmark on real removal outputs and then enabling temporal propagation only when measured residual/flicker/background-damage scores improve.

# Video Cleanup PRD Progress

Updated: 2026-09-16
Stable branch: `main`
Development branches: `feature/vmake-parity-core`, `feature/vmake-parity-precise-masks`, `feature/rapidocr-frame-adapter`

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
| Commercial video mask propagation | Candidate stage | SAM 2 (Apache-2.0), Cutie/XMem (MIT) require runtime/integration benchmarks |
| Paired-video objective benchmark | Required for parity claims | full external VSR/STTN/LaMa paired benchmark has not yet been completed |
| Stable promotion | Promoted | precise-mask safety merged through PR #2 and RapidOCR adapter through PR #3; both PR CI matrices passed Python 3.10/3.12 |

## Commercial dependency policy

Production/default paths may use commercially compatible local components such as MIT/Apache-2.0 VSR, RapidOCR, PaddleOCR, SAM 2, Cutie, or XMem after integration validation. Non-commercial upstream code/weights such as ProPainter and E2FGVI remain excluded from production dependencies. VOID/SVOR remain research candidates until runtime and paired-video quality justify their cost.

## Current quality statement

`main` is the stable executable baseline. Subtitle OCR now has a concrete local RapidOCR path and broad consensus boxes no longer become destructive masks unless explicitly requested. Vmake-quality parity is **not yet claimed**. The next evidence milestone is a reproducible real-video benchmark with residual-text, flicker, boundary and protected-background-damage measurements, followed by temporal propagation only where those metrics improve.

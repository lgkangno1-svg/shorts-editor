# Video Cleanup PRD Progress

Updated: 2026-09-16
Development branch: `feature/vmake-parity-core`

## P0 removal core

| Capability | Status | Current implementation/evidence |
| --- | --- | --- |
| Engine-neutral routing | Implemented | Local Fast / Local Temporal / Smart Pro routing with fail-closed validation |
| Subtitle OCR consensus | Implemented in core | Multi-frame block fusion + temporal association; OCR backend remains pluggable |
| Subtitle mask stabilization | Implemented in core | short-gap interpolation + temporal union envelope |
| Precise glyph/stroke mask interchange | Implemented | normalized polygons, duplicate suppression, confidence gate, frame-bounded VSR corrections |
| Coarse-mask safety | Implemented | consensus line tracks are guidance-only by default; destructive coarse masks require explicit opt-in |
| Local removal execution | Integrated adapter | VSR external local runner; LaMa/STTN/AUTO mapping; no paid API |
| Moving region export | Compatibility-only | core tracks -> VSR keyframe rectangles only with explicit coarse-mask opt-in |
| Scene-aware temporal windows | Implemented | chunking/window modules avoid crossing scene cuts |
| QC/escalation primitives | Implemented | residual/flicker/boundary/protected-damage gates and bounded escalation |
| Residual OCR verification | Enabled in VSR adapter | VSR `verify_removal` + quality report requested by default |
| Real OCR frame adapter | Next | RapidOCR first, PaddleOCR optional fallback; should emit fine glyph/stroke polygons where available |
| Real-video fixture inspection | Partial | both supplied clips inspected; broad rectangle approach rejected; one 1-second local proof completed |
| Full real-video VSR benchmark | Blocking promotion | reviewed external VSR runtime/models are not installed in the current execution environment |
| Stable promotion | Blocked | `main` has no executable cleanup baseline; full real-video benchmark + green CI required |

## Commercial dependency policy

Production/default paths may use commercially compatible local components such as MIT/Apache-2.0 VSR, RapidOCR, PaddleOCR, SAM2 and Apache-compatible local restoration models after runtime/quality validation. Non-commercial upstream code/weights such as ProPainter/E2FGVI/MiniMax-remover paths are not production dependencies. VOID/SVOR remain research candidates until runtime and real-video quality justify their cost.

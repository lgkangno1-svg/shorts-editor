# Video Cleanup PRD Progress

Updated: 2026-09-16
Development branch: `feature/vmake-parity-core`

## P0 removal core

| Capability | Status | Current implementation/evidence |
| --- | --- | --- |
| Engine-neutral routing | Implemented | Local Fast / Local Temporal / Smart Pro routing with fail-closed validation |
| Subtitle OCR consensus | Implemented in core | Multi-frame block fusion + temporal association; OCR backend remains pluggable |
| Subtitle mask stabilization | Implemented in core | short-gap interpolation + temporal union envelope |
| Local removal execution | Integrated adapter | VSR external local runner; LaMa/STTN/AUTO mapping; no paid API |
| Moving region export | Implemented | core tracks -> VSR keyframe rectangles |
| Scene-aware temporal windows | Implemented | chunking/window modules avoid crossing scene cuts |
| QC/escalation primitives | Implemented | residual/flicker/boundary/protected-damage gates and bounded escalation |
| Residual OCR verification | Enabled in VSR adapter | VSR `verify_removal` + quality report requested by default |
| Real OCR frame adapter | Next | RapidOCR first, PaddleOCR optional fallback |
| Paired-video objective benchmark | Blocking promotion | not yet implemented/run in this repo |
| Stable promotion | Blocked | `main` has no executable cleanup baseline; real-video benchmark required |

## Commercial dependency policy

Production/default paths may use commercially compatible local components such as MIT/Apache-2.0 VSR, RapidOCR and PaddleOCR. Non-commercial upstream code/weights such as ProPainter/E2FGVI-class restricted paths are not production dependencies. VOID/SVOR remain research candidates until runtime and paired-video quality justify their cost.

# Video Cleanup PRD Progress

Updated: 2026-09-16
Stable branch: `main`
Development branch: `feature/vmake-parity-core`

## P0 removal core

| Capability | Status | Current implementation/evidence |
| --- | --- | --- |
| Engine-neutral routing | Implemented / stable | Local Fast / Local Temporal / Smart Pro routing with fail-closed validation |
| Subtitle OCR consensus | Implemented / stable | Multi-frame block fusion + temporal association; OCR backend remains pluggable |
| Subtitle mask stabilization | Implemented / stable | short-gap interpolation + temporal union envelope |
| Local removal execution | Integrated adapter / stable | VSR external local runner; LaMa/STTN/AUTO mapping; no paid API |
| Moving region export | Implemented / stable | core tracks -> VSR keyframe rectangles |
| Scene-aware temporal windows | Implemented / stable | chunking/window modules avoid crossing scene cuts |
| QC/escalation primitives | Implemented / stable | residual/flicker/boundary/protected-damage gates and bounded escalation |
| Residual OCR verification | Enabled in VSR adapter | VSR `verify_removal` + quality report requested by default |
| Real OCR frame adapter | Next | RapidOCR first, PaddleOCR optional fallback |
| Text-shaped / glyph-level mask refinement | Priority next | real-video fixture review shows full subtitle boxes can over-remove background |
| Commercial video mask propagation | Candidate stage | SAM 2 (Apache-2.0), Cutie/XMem (MIT) require runtime/integration benchmarks |
| Paired-video objective benchmark | Required for parity claims | not yet implemented/run in this repo |
| Stable promotion | Promoted | core promoted to `main` after Python 3.10/3.12 GitHub Actions success; CI now covers `main` pushes |

## Commercial dependency policy

Production/default paths may use commercially compatible local components such as MIT/Apache-2.0 VSR, RapidOCR, PaddleOCR, SAM 2, Cutie, or XMem after integration validation. Non-commercial upstream code/weights such as ProPainter and E2FGVI are excluded from production dependencies. VOID/SVOR remain research candidates until runtime and paired-video quality justify their cost.

## Current quality statement

`main` is now the stable executable baseline, but Vmake-quality parity is **not yet claimed**. The next evidence milestone is objective paired clean/overlay video benchmarking plus tighter subtitle/text masks that minimize protected-background damage.

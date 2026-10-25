# Video Cleanup PRD Progress

Updated: 2026-10-26
Stable branch: `main`
Development branches: `feature/vmake-parity-core`, `feature/vmake-parity-precise-masks`, `feature/rapidocr-frame-adapter`, `feature/paired-video-benchmark`, `feature/real-fixture-top-captions`, `feature/opaque-caption-plates-20260923`

## P0 removal core

| Capability | Status | Current implementation/evidence |
| --- | --- | --- |
| Engine-neutral routing | Implemented / stable | Local Fast / Local Temporal / Smart Pro routing with fail-closed validation |
| Subtitle OCR consensus | Implemented / stable | Multi-frame block fusion + temporal association |
| Top-caption coverage | Implemented / stable | four-fixture audit exposed top-edge caption exclusion; PR #5 lowered the default vertical gate while keeping temporal/confidence safety gates; PR and post-merge CI passed Python 3.10/3.12 |
| Subtitle mask stabilization | Implemented / stable | short-gap interpolation + temporal union envelope |
| Precise glyph/stroke masks | Implemented / stable | normalized frame polygons, confidence gate, duplicate suppression and frame-bounded VSR corrections |
| Coarse-mask safety | Implemented / stable | consensus subtitle rectangles are guidance-only by default; destructive coarse masks require explicit opt-in |
| Local removal execution | Bridge contract implemented / backend approval pending | LaMa/STTN/AUTO mapping remains, but destructive execution now requires an explicit commercial-use approval plus the `shorts-editor-vsr-bridge/v1` JSON capability handshake. Raw third-party GUI entrypoints are rejected fail-closed. |
| Moving region export | Compatibility-only | coarse VSR keyframe rectangles remain available only through explicit `coarse_track_mask=True` |
| Scene-aware temporal windows | Implemented / stable | chunking/window modules avoid crossing scene cuts |
| QC/escalation primitives | Implemented / stable | residual/flicker/boundary/protected-damage gates and bounded escalation |
| Residual OCR verification | Enabled in VSR adapter | VSR `verify_removal` + quality report requested by default |
| Real OCR frame adapter | Implemented / stable | RapidOCR 3.x line output feeds tracking while `return_word_box=True` word polygons feed precise masks; NumPy-backed output is covered by tests |
| OCR runtime dependency | Optional / local / smoke-tested | `.[ocr]` installs `rapidocr>=3.9.2,<4` plus the required ONNX Runtime inference backend; CI executes the public adapter on a real blank frame; Korean is the default engine language; no paid/cloud API |
| Paired-video benchmark core | Implemented / stable | `evaluate_paired_video()` measures residual, flicker, boundary spill and protected-region damage against clean reference frames and feeds the existing fail-closed QC gate |
| Real fixture decode audit | Verified current fixture set | The 4 user-supplied validation clips were re-probed from source on 2026-10-26: all are HEVC/H.265, 1080x1920, 30 fps, totaling 4,702 frames. The previous H.264/AV1 fixture note was stale and has been corrected. |
| Portable media preflight/decode | Implemented / locally smoke-tested | `probe_media()` normalizes ffprobe metadata and `decode_frame_rgb()` uses FFmpeg RGB24 output instead of depending on OpenCV codec support. A generated 1080x1920 HEVC clip was probed and decoded end-to-end on the authorized Linux validation host. |
| Opaque caption plates | Implemented / pending real-fixture promotion | dark backplate masks now require four-sided dark margins, brighter outer boundaries, wide/shallow geometry, repeated temporal support, and `TargetKind.SUBTITLE`; natural dark scenes and product/scene text fail closed. Synthetic regression coverage is included; the private fourth fixture still needs an executable local rerun before Vmake-parity claims |
| Commercial video mask propagation | Candidate stage | SAM 2 (Apache-2.0), Cutie/XMem (MIT) require runtime/integration benchmarks |
| Full real-video parity benchmark | Pending fixture/runtime evidence | measurement code is stable; full external VSR/STTN/LaMa runs still need executable local runtime plus suitable clean-reference fixtures |
| Stable promotion | Promoted baseline | precise-mask safety, RapidOCR adapter, paired benchmark, top-caption coverage and opaque-caption safeguards are on `main`; PR #29 additionally proved the packaged OCR extra can execute a real ONNX Runtime-backed adapter call in CI. |

## Commercial dependency policy

Production/default paths may use local components only after their commercial terms and transitive dependencies are explicitly verified. RapidOCR, PaddleOCR, SAM 2, Cutie, and XMem remain candidates subject to integration validation. The `ppzflpp/VideoSubtitleRemover` snapshot audited at `af4f257` is **not production-approved**: its documented entrypoint is a PyQt GUI, it requires an NVIDIA GPU (minimum 1060 per its README), and the checked-out repository contains no root license file establishing commercial terms. Non-commercial upstream code/weights such as ProPainter and E2FGVI remain excluded from production dependencies. GRT is Apache-2.0 but targets stereo disocclusion rather than general removal; VOID/SVOR remain research candidates until runtime, license, and paired-video quality evidence justify integration.

## Current quality statement

`main` is the stable executable baseline. Subtitle OCR has a concrete local RapidOCR path, top-edge captions are no longer excluded by default, broad consensus boxes are non-destructive by default, objective paired-reference scoring is implemented, and codec-sensitive inputs now have an FFprobe/FFmpeg media path. The opaque-caption path remains conservative and does not widen generic OCR masks by default. Vmake-quality parity is **not yet claimed**. The remaining quality gap is full VSR reconstruction on the private real clips followed by clean-reference/protected-region scoring of the rendered outputs.

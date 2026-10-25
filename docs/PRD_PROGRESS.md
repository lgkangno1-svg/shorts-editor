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
| Local removal execution | Built-in local-fast CPU fallback implemented / temporal backend pending | An Apache-2.0 OpenCV CPU bridge now implements `shorts-editor-vsr-bridge/v1` for the `lama`/Local Fast route using precise polygons only. It rejects coarse subtitle boxes and any frame whose destructive mask exceeds 10% area. STTN/AUTO still require a separately reviewed backend. |
| Moving region export | Compatibility-only | coarse VSR keyframe rectangles remain available only through explicit `coarse_track_mask=True` |
| Scene-aware temporal windows | Implemented / stable | chunking/window modules avoid crossing scene cuts |
| QC/escalation primitives | Implemented / stable | residual/flicker/boundary/protected-damage gates and bounded escalation |
| Residual OCR verification | Request plumbing implemented / post-render OCR gate pending | Runner overlays request `verify_removal` and quality reporting by default. The built-in OpenCV bridge reports that request but does not claim OCR re-verification; post-render OCR gating still needs orchestration. |
| Real OCR frame adapter | Implemented / stable | RapidOCR 3.x line output feeds tracking while `return_word_box=True` word polygons feed precise masks; NumPy-backed output is covered by tests |
| OCR runtime dependency | Optional / local / smoke-tested | `.[ocr]` installs `rapidocr>=3.9.2,<4` plus the required ONNX Runtime inference backend; CI executes the public adapter on a real blank frame; Korean is the default engine language; no paid/cloud API |
| Paired-video benchmark core | Implemented / stable | `evaluate_paired_video()` measures residual, flicker, boundary spill and protected-region damage against clean reference frames and feeds the existing fail-closed QC gate |
| Real fixture decode audit | Verified current fixture set | The 4 user-supplied validation clips were re-probed from source on 2026-10-26: all are HEVC/H.265, 1080x1920, 30 fps, totaling 4,702 frames. The previous H.264/AV1 fixture note was stale and has been corrected. |
| Portable media preflight/decode | Implemented / locally smoke-tested | `probe_media()` normalizes ffprobe metadata and `decode_frame_rgb()` uses FFmpeg RGB24 output instead of depending on OpenCV codec support. A generated 1080x1920 HEVC clip was probed and decoded end-to-end on the authorized Linux validation host. |
| Opaque caption plates | Implemented / pending real-fixture promotion | dark backplate masks now require four-sided dark margins, brighter outer boundaries, wide/shallow geometry, repeated temporal support, and `TargetKind.SUBTITLE`; natural dark scenes and product/scene text fail closed. Synthetic regression coverage is included; the private fourth fixture still needs an executable local rerun before Vmake-parity claims |
| Commercial video mask propagation | Candidate stage | SAM 2 (Apache-2.0), Cutie/XMem (MIT) require runtime/integration benchmarks |
| Full real-video parity benchmark | Synthetic render path proven / private-clip parity pending | The built-in CPU bridge rendered H.264 and HEVC synthetic clips end-to-end with audio preservation and clean-reference checks. Private real-clip OCR→mask→render→QC orchestration and temporal reconstruction remain pending. |
| Stable promotion | Promoted baseline | precise-mask safety, RapidOCR adapter, paired benchmark, top-caption coverage and opaque-caption safeguards are on `main`; PR #29 additionally proved the packaged OCR extra can execute a real ONNX Runtime-backed adapter call in CI. |

## Commercial dependency policy

Production/default paths may use local components only after their commercial terms and transitive dependencies are explicitly verified. The built-in Local Fast fallback uses `opencv-python-headless` 4.14, whose installed wheel metadata identifies Apache 2.0; it is isolated behind the optional `.[opencv]` extra. RapidOCR, PaddleOCR, SAM 2, Cutie, and XMem remain candidates subject to integration validation. The `ppzflpp/VideoSubtitleRemover` snapshot audited at `af4f257` is **not production-approved**: its documented entrypoint is a PyQt GUI, it requires an NVIDIA GPU (minimum 1060 per its README), and the checked-out repository contains no root license file establishing commercial terms. Non-commercial upstream code/weights such as ProPainter and E2FGVI remain excluded from production dependencies. GRT is Apache-2.0 but targets stereo disocclusion rather than general removal; VOID/SVOR remain research candidates until runtime, license, and paired-video quality evidence justify integration.

## Current quality statement

`main` is the stable executable baseline. Subtitle OCR has a concrete local RapidOCR path, broad consensus boxes remain non-destructive by default, codec-sensitive inputs use FFprobe/FFmpeg, and a commercially explicit CPU Local Fast renderer can now consume precise masks end-to-end. The renderer has been exercised on synthetic H.264 and HEVC clips with audio and clean-reference checks. Vmake-quality parity is **not yet claimed**: the remaining gates are private real-clip OCR→mask→render orchestration, post-render OCR/QC, and a reviewed temporal backend for harder/long clips.

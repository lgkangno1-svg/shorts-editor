# 042 — built-in OpenCV CPU removal bridge

Date: 2026-10-26
Baseline: `main` after PR #31 (`11679bd`)

## Goal

Provide a commercially explicit, executable Local Fast fallback without depending on an unreviewed third-party video-removal GUI or GPU runtime.

The fallback is deliberately conservative. It consumes only precise pixel polygons that have already passed the OCR/mask pipeline. It does not turn broad subtitle consensus boxes into destructive masks and it does not claim temporal reconstruction parity.

## Dependency and licensing evidence

The validation host installed `opencv-python-headless 4.14.0`. Its installed wheel metadata reports:

- License: `Apache 2.0`
- Home: `https://github.com/opencv/opencv-python`

The dependency is isolated behind the optional `.[opencv]` extra.

## Bridge contract

`shorts_editor.opencv_bridge` implements the reviewed `shorts-editor-vsr-bridge/v1` handshake.

Capabilities:

- CPU only;
- Local Fast / `lama` compatibility route only;
- JSON output and JSON config overlays;
- precise masks only;
- maximum destructive mask area: 10% of a frame;
- coarse `subtitle_region_keyframes` are rejected.

`create_builtin_opencv_runner_config()` records explicit commercial approval and the Apache-2.0 backend license string before `run_vsr_local()` can execute it.

## Render implementation

The bridge:

1. probes the input with FFprobe;
2. decodes the video stream through FFmpeg as BGR24, avoiding OpenCV codec dependence;
3. rasterizes only reviewed precise polygons;
4. applies a small 1-pixel mask dilation and OpenCV TELEA inpainting;
5. rejects a frame if its destructive mask exceeds the 10% safety limit;
6. encodes H.264 with the requested CRF;
7. copies the original audio stream when present;
8. re-probes the output and fails if dimensions, FPS, frame count, or video duration diverge.

The initial encoder used `-shortest`; real smoke validation exposed a 15→14 frame truncation. That option was removed and explicit frame-count/duration validation was added.

## Runtime evidence on authorized host

### H.264 synthetic overlay

- 360x640, 30 fps, 30 frames, AAC audio;
- all 30 frames were decoded and masked;
- maximum mask area ratio: 0.034067;
- clean-reference mean absolute error inside the target region:
  - before removal: 144.150
  - after removal: 2.104
- protected-region mean absolute error: 0.000;
- output retained AAC audio.

### HEVC synthetic overlay

- 360x640, 30 fps, 15 frames, AAC audio;
- input codec: HEVC;
- output codec: H.264;
- all 15 frames were decoded and masked;
- maximum mask area ratio: 0.034067;
- clean-reference mean absolute error inside the target region:
  - before removal: 143.803
  - after removal: 2.844
- protected-region mean absolute error: 0.000;
- output retained AAC audio.

The public `run_vsr_local()` path was also exercised with 15 per-frame precise masks. Final verification reported input=15 frames/0.500s and output=15 frames/0.500s with AAC audio.

## Scope limit

This is a safe executable fallback, not a claim of Vmake-quality parity.

Remaining gates:

- drive real private clips through OCR → precise-mask selection → render;
- perform post-render OCR/residual/flicker/protected-region QC;
- validate a commercially reviewed temporal backend for long or reconstruction-heavy clips;
- compare real rendered samples visually and quantitatively before making a production quality claim.

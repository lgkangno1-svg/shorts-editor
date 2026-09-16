# Engineering Loop 028 — API-free local subtitle stack

Date: 2026-09-16
Branch: `feature/vmake-parity-core`

## Source review

The user-supplied `SubtitleEraser_ONE_v2_Windows` archive was inspected before changing the current core. Useful patterns retained conceptually:

- local VideoSubtitleRemover (VSR) execution rather than a paid cloud restoration API,
- FFmpeg/ffprobe validation and output verification,
- multi-frame subtitle-band detection as a cheap fallback,
- local AI restoration preferred over blur/delogo.

The old optional Gemini/FCC-style detection path is intentionally **not** carried forward because the current requirement is API-free operation.

## Implemented

1. Added OCR-engine-neutral subtitle consensus (`subtitles.py`). RapidOCR, PaddleOCR or another local OCR engine can feed normalized observations without coupling the core to one detector.
2. Word/line detections are fused into caption blocks, then associated over time. Selection uses support, confidence, position, width, stability and text-change evidence rather than a fixed bottom strip.
3. Short OCR dropouts are interpolated, then a local temporal union/envelope stabilizes mask edges and reduces clipped glyphs/mask flicker.
4. Added a local VSR runner (`local_vsr.py`) that maps the existing cost-aware tiers to local-only VSR modes: `LOCAL_FAST -> lama`, `LOCAL_TEMPORAL -> sttn`, `SMART_PRO -> auto`.
5. Trusted subtitle tracks are exported as VSR moving-region keyframes and skip duplicate detection; VSR quality reporting and residual-removal verification stay enabled.
6. The subprocess is invoked with `shell=False`; common model-hub offline environment flags are set so this adapter contains no remote API path.
7. Hardened `BoundingBox`, `TrackSample`, `RemovalTrack` and tracking-risk thresholds against booleans/wrong runtime types that Python could otherwise silently treat as numbers.

## Commercial-license gate

- `SysAdminDoc/VideoSubtitleRemover`: MIT — eligible as an external local backend.
- RapidOCR: Apache-2.0 — eligible.
- PaddleOCR: Apache-2.0 — eligible.
- Netflix VOID: Apache-2.0 — eligible as a high-VRAM research/Smart-Pro candidate, not the default consumer path.
- Upstream ProPainter, E2FGVI and non-commercial remover weights remain excluded from the production dependency path.

## Evidence

A focused sandbox unit/synthetic run covering subtitle consensus, mask stabilization, VSR command/config bridging, local subprocess execution and validation completed **35 passed in 0.79s**.

This is **not** a full repository CI run and **not** a real-video quality benchmark. `main` still contains no executable stable cleanup baseline, so no honest stable-vs-new PSNR/SSIM/VMAF comparison is available yet.

## Next quality gate

- add a real RapidOCR frame adapter,
- build paired clean + burned-in-subtitle video fixtures,
- measure residual OCR, masked-region reconstruction error, temporal flicker and outside-mask damage,
- run VSR end-to-end on those fixtures,
- only then tune routing thresholds or promote toward stable.

## Promotion decision

**KEEP ON DEVELOPMENT BRANCH.** The architecture is safer and more complete, but real-video paired benchmarks remain mandatory before stable promotion.

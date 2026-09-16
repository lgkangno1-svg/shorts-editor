# Engineering Loop 031 — RapidOCR frame adapter

Date: 2026-09-16
Branch: `feature/rapidocr-frame-adapter`

## Goal
Replace the pluggable-only OCR boundary with a concrete, local RapidOCR 3.x adapter while preserving the precise-mask safety introduced in loop 030.

## Design
- RapidOCR line `boxes/txts/scores` become engine-neutral `OCRDetection` values for subtitle consensus/tracking.
- `return_word_box=True` word polygons become `PreciseMaskPolygon` values for destructive removal.
- Broad line boxes do **not** become destructive masks unless `allow_line_masks=True` is explicitly requested.
- Low-confidence word masks are filtered before removal geometry is emitted.
- Malformed optional word polygons are skipped; parallel line-array contract mismatches fail closed.
- NumPy scalar coordinates/scores are accepted because RapidOCR returns NumPy-backed geometry.
- Runtime dependency is optional (`.[ocr]`) and no paid/cloud API is introduced.

## Version / license basis
- Adapter targets RapidOCR 3.x, with optional dependency `rapidocr>=3.9.2,<4`.
- RapidOCR 3.9.2 is Apache-2.0 and supports Python 3.10/3.12.

## Promotion gate
Promote only after pull-request CI passes the full repository suite on Python 3.10 and 3.12. This loop validates the adapter boundary; it does not claim a full VSR real-video quality benchmark.

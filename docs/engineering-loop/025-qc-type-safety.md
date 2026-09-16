# Loop 025 — QC metric/threshold type safety — 2026-09-16

## Audit / change
- Global fail-closed review found `QCMetrics` called `math.isfinite()` directly, so booleans were silently accepted as 0/1 metrics and strings/None failed with incidental Python errors rather than the API's validation contract.
- `evaluate_qc()` had the same boolean/nonnumeric threshold gap.
- Added explicit numeric/non-boolean validation for all QC metrics and thresholds, plus regression coverage.

## Verification
- A targeted local validation harness covering malformed booleans/strings/None, non-finite/out-of-range values, and a valid control case passed 17 cases.
- Full repository pytest could not be run in this automation environment because direct GitHub clone/network resolution is unavailable. No full-suite or CI pass is claimed for this head.

## Research refresh
- Netflix VOID remains Apache-2.0 and suitable as a high-cost Smart-Pro research candidate; official model documentation still describes a 40GB+ VRAM class setup and optional flow-warped second pass for temporal consistency.
- Apache-2.0 LaMa ONNX/safetensors mirrors remain attractive for a cheap frame-local fallback, but require video-level temporal QC before adoption.
- MiniMax-Remover weights remain excluded from production because the published weights are CC-BY-NC-4.0 even though source code is Apache-2.0.
- DiffuEraser's repository is Apache-2.0 but its published pipeline uses ProPainter as a prior, so that dependency path remains excluded unless replaced and re-benchmarked.

## Promotion decision
**KEEP ON `feature/vmake-parity-core`.** `main` remains unchanged until full CI and paired clean/overlay video benchmarks are green.

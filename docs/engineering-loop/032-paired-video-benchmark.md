# Engineering Loop 032 — paired video quality benchmark

Date: 2026-09-16
Branch: `feature/paired-video-benchmark`
Promotion: merged to `main` through PR #4

## Goal
Turn the existing QC primitives into a reproducible paired-video benchmark so removal changes are promoted by measured quality rather than visual impression alone.

## Inputs
- overlay frames: original frames containing the subtitle/text target
- candidate frames: removal output under evaluation
- clean frames: paired clean reference frames
- removal mask: expected target pixels per frame

## Metrics
- residual: candidate error inside the removal mask relative to the original overlay signal
- flicker: temporal-difference error versus the clean reference inside/around target frames
- boundary: candidate error in a narrow ring surrounding the target mask
- protected damage: candidate error outside a safety-expanded target region

The four normalized metrics feed the existing fail-closed `evaluate_qc()` decision gate.

## Safety / validity checks
- video tensors must have identical `[frames, height, width, channels]` shapes
- removal mask must match the video geometry and contain target pixels
- fixtures with insufficient overlay signal inside the mask are rejected rather than producing misleading quality scores
- NumPy is an optional local benchmark dependency; no cloud API is required

## Evidence
- PR #4 full repository CI passed on Python 3.10 and 3.12.
- Synthetic coverage includes perfect cleanup, visible residual, protected-region damage, boundary spill, temporal flicker, mismatched shapes, empty masks and missing overlay signal.

## Result
**PROMOTED.** Objective paired-reference scoring is stable on `main`. The remaining blocker for Vmake-parity claims is evidence from full real-video removal runs with suitable references/runtime, not the absence of a scoring core.

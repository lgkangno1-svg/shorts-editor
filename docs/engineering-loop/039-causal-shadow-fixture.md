# 039 — causal shadow QC fixture

Date: 2026-09-18
Baseline: `main` at `6f0181f7d11e67f9b6ce756adbc6be047ca55032`

## Repository / CI review

- PR #23 head `30948397bc5c76629ea98a8f5caa18348c7cb428` completed `cleanup-core-ci` run #111 successfully and was squash-merged before this change.
- Re-audited the paired benchmark and converted the prior causal-effects audit recommendation into an executable regression fixture rather than changing runtime scoring.
- Added a synthetic target-induced shadow outside the removal mask/protected margin. The candidate removes the masked target but leaves the shadow; the expected result is zero target residual but a failed protected-region-damage gate.
- This specifically proves the existing paired-reference QC can reject incomplete causal cleanup without importing a new metric/model dependency.
- No local tests or benchmarks were executed in this connector run. The new test must pass CI before merge.

## Fresh commercial research

- Netflix VOID remains Apache-2.0 at repository/model-card level and explicitly targets interaction-aware deletion; retain as a high-resource comparison candidate.
- D2DF (2026) publishes an Apache-2.0 repository/model card and proposes one-step draft refinement, but its documented draft-guided path acknowledges ProPainter and CogVideoX components. Do not production-integrate until checkpoint and transitive-license/resource validation is complete.
- `propainter-delogo` continues to demonstrate useful shot-aware/crop-only/feathered-composite engineering patterns, but its runtime depends on separately licensed ProPainter; patterns only, no production dependency.
- Newly surfaced `ghostmark-video` is source-available with product/service use requiring written permission, so it is excluded from the production dependency path despite useful tiled-watermark detection ideas.

## Decision

Keep runtime code unchanged. The only change in this loop is regression coverage proving the existing protected-region QC catches a target-induced secondary effect left behind outside the object mask. Merge only after this branch's CI succeeds.
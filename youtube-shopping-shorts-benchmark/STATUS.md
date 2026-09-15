# Project status

Last checked: 2026-09-09 KST

## Benchmark sample
- Verified Korean shopping/product Shorts at 5M+ views: **102**
- Existing structured rows: **102 / 102**
- Sample-count target: reached

## IMPORTANT: strict completion condition

**STRICT DIRECT-VISUAL REVIEW MILESTONE COMPLETE — 102 / 102.**

Every one of the 102 included Shorts has now been directly visually reviewed at scene/frame level. Metadata-only, transcript-only, title-proxy, extracted-only, or inferred audiovisual fields did **not** count toward this milestone.

### Strict direct-review counters
- Total benchmark videos: **102**
- Strictly reviewed through the current direct visual protocol: **102 / 102**
- Remaining strict visual reviews: **0**

Strictly counted reviews are committed review JSON files with `direct_visual_review: true` backed by actual inspected contact-sheet/frame evidence.

## Latest durable MiniPC extraction state
Latest frame-extraction workflow run inspected: **34364704107** (`d03d7d7ceb35c2c3d51768f71de24656a8141929`, refreshed free Piped/public-US proxy rescue)
- Durable evidence DONE markers in artifact: **102 / 102**
- Current failed/retry markers: **0**
- DONE marker without local evidence: **0**
- Artifact: `shopping-shorts-frame-analysis-minipc-34364704107`
- Artifact ID: **10109367625**

This free-route run recovered the three previously blocked evidence sets (`001`, `007`, `047`). No paid API, paid vidIQ/Codex acquisition, account cookies, or credentialed/private proxy was required.

## Final direct visual-review batch
The final three samples were reviewed from the actual MiniPC artifact using their first-frame image, hook 5-fps contact sheet, whole-video 1-fps contact sheets, scene-change contact sheets, manifest, and audio spectrogram:

- `001_5DwcGCiBs70` — a **Top-5 food/product listicle** with five visibly distinct foods/drinks. First-frame liquid-pour macro, dense first-five-second cutting, persistent `1/5` through `5/5` rank markers, preparation/tasting proof. **Excluded from single-product training.**
- `007_gfHPsBrXqZQ` — a **Top-5 household/emergency-item listicle** with visibly distinct swab/tool, patch/sticker, wound-closure strip, patch/bandage, and liquid-applicator segments. Persistent `1/5` through `5/5` markers. **Excluded from single-product training.**
- `047_pUpu06TgayE` — a **Top-3 travel-emergency-item listicle** with compact towel/cleaning item, condition/temperature patch, and disinfecting swab/applicator. Persistent `1/3` through `3/3` markers. **Excluded from single-product training.**

Direct audio listening was not claimed for these three. BGM identity, exact edit-SFX identity, Foley audibility, and VO identity remain `unknown` unless supported elsewhere. Extracted LUFS/LRA/RMS/silence/pulse/transient metrics and visible action cues are retained only as supporting measurements/candidates.

## Single-product training evidence
The final three reviews add **no** single-product training samples because all three are confirmed multi-product listicles.

The normalization gap for `086_EB-2ov6_gOw` remains closed. Its committed strict review directly confirms one rotating/stirring cooker system from multi-unit mechanism hook through home-use reveal, automatic cooking, result/material proof and cleanup. The multiple hook units are identical instances of the same product, not a listicle.

`direct_review_adjudications.csv` explicitly contains `086` as `reviewed, include_single_product, confirmed`. The normalized strict confirmed training index therefore remains at **12** adjudicated single-product samples, all backed by strict direct-visual review and all with confirmed timing evidence.

`seed_event_timings.csv` remains **12 timing rows, all in confirmed evidence buckets**:
- `direct_visual`: **11**
- `direct_audiovisual`: **1**
- `confirmed_transcript_timing`: **0**
- `estimated`: **0**

Current descriptive timing medians across the 12 confirmed single-product timing rows remain exploratory rather than frozen template targets:
- hook end: **4.83 s**
- product reveal: **3.0135 s**
- first demo: **5.45 s**
- first proof: **9.25 s**
- secondary proof: **16.5 s** (`n=10`)
- payoff/wrap: **21.24 s**

The deterministic edit compiler reads these values from `data/seed_timing_stats.json` when emitting its benchmark snapshot. The empirical snapshot remains metadata only: policy role shares are still independent and are not silently re-derived from the small single-product corpus.

## Extraction diagnosis / blocker resolution
The prior acquisition blockers were:

`001_5DwcGCiBs70`, `007_gfHPsBrXqZQ`, `047_pUpu06TgayE`.

They are **resolved for evidence acquisition** in run `34364704107`. The refreshed free Piped/public-US proxy rescue produced valid MiniPC evidence directories and DONE markers for all three. Their actual contact sheets were then directly inspected and strict review records committed, so they now legitimately increment the direct-review counter.

## Strict review storage / aggregation
- Schema: `strict-frame-analysis/SCHEMA.md`
- Per-video reviews: `strict-frame-analysis/reviews/<sample_id>_<video_id>.json`
- Aggregate builder: `scripts/build_strict_review_index.py`
- Aggregate output: `data/strict_frame_review_index.csv`
- Coverage report: `analysis/STRICT_FRAME_REVIEW_COVERAGE.md`

The per-video review JSONs are the strict source of truth for the 102/102 milestone. The aggregate CSV/report should be regenerated after the final three JSON commits so their derived coverage statistics also reflect 102 rows.

## Paid-tool constraint
Paid vidIQ/Codex were not used for the final bulk evidence acquisition/review. The MiniPC/free-route requirement was satisfied.

## Completion state
**COMPLETE FOR THE STRICT DIRECT FRAME-ANALYSIS MILESTONE — 102 / 102 direct visual reviews.**

All 102 benchmark Shorts now have strict direct visual/frame-level review records. Broader downstream engine/template work is a separate project phase and should not be confused with this completed review milestone.

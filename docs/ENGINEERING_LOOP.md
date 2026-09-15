# Engineering Loop Log

## Loop 008 — 2026-09-15

### Repository audit
- Development branch currently contains only `README.md` and the Vmake-parity PRD; the actual Build 007/removal engine source is not present in this repository yet.
- Because implementation source is absent, no production code cleanup, regression test, benchmark, or safe feature change can truthfully be performed in this loop.
- Stable branch was therefore left unchanged.

### External technique review
- Netflix VOID remains the preferred production-grade hard-case candidate: official code/model is Apache-2.0 and supports Pass 1 + Pass 2 temporal refinement.
- Official VOID guidance requires 40GB+ VRAM and up to 197-frame windows; this reinforces keeping it as a routed hard-case engine rather than the default path.
- SAM2 remains a commercially usable tracking/segmentation candidate (Apache-2.0) for object/person/moving-overlay propagation.
- ProPainter-based watermark-removal projects were reviewed only as architecture references and are excluded from the planned production engine because ProPainter's upstream license is non-commercial.
- Hugging Face connector lookup failed transiently in this loop; no model was adopted from an unverified result.

### Next safe gate
1. Import/migrate the actual current Windows Build 007 source into this repository or a dedicated successor repository.
2. Establish reproducible smoke tests and sample fixtures before refactoring.
3. Fix Windows launcher/packaging first.
4. Introduce a common `RemovalTrack` abstraction for subtitle/text and watermark/logo targets.
5. Add fixed watermark MVP before moving-watermark propagation.

### Promotion decision
**NO CODE PROMOTION.** There is no implementation source in the repository to validate. Documentation/audit only.

## Loop 009 — 2026-09-16

### Repository audit
- Rechecked `feature/vmake-parity-prd`: it still contains only `README.md` and `docs/`; implementation source is still absent.
- No benchmark or regression test was claimed or run because there is no executable project code in this repository.

### Technique review
- SAM2 video propagation remains a strong production candidate for moving watermark/logo/object masks; its model/code are Apache-2.0.
- Reviewed recent watermark-removal projects for architecture ideas: shot-aware chunking, processing only a padded crop around a small watermark, mask dilation/feathering, audio passthrough, and measurable synthetic clean/watermarked twin fixtures are useful patterns.
- ProPainter-dependent implementations remain reference-only because upstream commercial licensing is unsuitable for our production path.
- A useful testing pattern was identified: generate paired clean + watermarked synthetic clips and score residue/tracking error rather than relying only on visual inspection. This should become the first benchmark harness once source is present.

### Promotion decision
**DOCUMENTATION ONLY.** Stable code remains untouched until the real removal-engine source is present.
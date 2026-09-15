# Engineering Loop Log

## Loop 008 — 2026-09-15

### Repository audit
- Development branch currently contains only `README.md` and the Vmake-parity PRD; the actual Build 007/removal engine source is not present in this repository yet.
- Because implementation source is absent, no production code cleanup, regression test, benchmark, or safe feature change can truthfully be performed in this loop.
- Stable branch was therefore left unchanged.

### External technique review
- Netflix VOID remains the preferred production-grade hard-case candidate: official code/model is Apache-2.0 and supports Pass 1 + Pass 2 temporal refinement.
- Official VOID guidance requires 40GB+ VRAM and up to 197-frame windows; this reinforces keeping it as a routed hard-case engine rather than the default path.
- Community VOID wrappers reveal useful integration constraints to validate later: frame counts aligned to 4k+1, dimensions aligned to model requirements, explicit quadmask semantics, and Pass 2 only when temporal consistency needs refinement. These are implementation leads, not yet adopted as production truth until verified against official code.
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
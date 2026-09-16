# Loop 034 — propagation candidate audit

Date: 2026-09-17

## Audit

- Stable baseline before this loop: `30af9783709f889a697c737b11ae0e30eab3b49f`.
- Global review kept the current subtitle/RapidOCR/paired-QC paths unchanged; no production dependency was added without runtime evidence.
- A direct subtitle validation path still uses Python `int/float` type checks while the RapidOCR adapter already normalizes NumPy scalars. This is a small reliability cleanup candidate, but it was not promoted in this loop because a complete tested patch was not available through the current execution path.

## Current propagation research

- Meta SAM 2.1 remains Apache-2.0; official Hugging Face `facebook/sam2.1-hiera-small` exposes video segmentation and is about 46M parameters / 184 MB. It is the preferred first propagation benchmark candidate.
- Cutie remains MIT and reports materially better difficult-object VOS accuracy than XMem at similar runtime in its paper; it remains a second benchmark candidate.
- SAM2Matting was reviewed and excluded from production because its repository is CC BY-NC-SA 4.0 / non-commercial.
- No ProPainter/E2FGVI production dependency was introduced.

## Decision

Do not integrate a propagation model yet. The uploaded fixtures exposed opaque caption plates and AV1 decode handling as immediate real-world gaps; propagation should be promoted only after local runtime and paired/QC evidence show lower residual/flicker without protected-region damage.

## Evidence policy

No SAM2/Cutie runtime inference or full VSR reconstruction was run in this loop, so no quality improvement is claimed.

# PRD — AI Video Cleanup Platform

> Working title: **RemakeClean / Video Cleanup ONE**  
> Status: Draft v1.0  
> Date: 2026-09-15  
> Benchmark target: **Vmake Labs removal workflow parity and eventual quality/cost advantage**  
> Primary principle: **Do not ship a result merely because rendering succeeded. Ship only results that pass automatic quality gates.**

---

## 0. Executive Summary

This product evolves the current subtitle-removal prototype into a general-purpose **AI video cleanup platform**.

The target is not a single `subtitle remover` feature. The target is a product class comparable to Vmake Labs removal tools:

- Subtitle / text removal
- Watermark / logo removal
- Moving watermark tracking
- Object removal
- Person / passerby removal
- Manual brush / box / eraser
- Protect zones
- Batch processing
- Automatic difficulty routing
- Local processing when quality is sufficient
- Cloud/self-hosted generative video inpainting for hard cases
- Post-render automatic QC and retry/escalation
- Windows application first for rapid QA
- Web application + Chrome extension for commercialization
- Subscription + credit-based billing

The product must compete on three dimensions simultaneously:

1. **Quality** — fewer residual letters, smears, ghosts, seams, flicker, and subject damage.
2. **Cost** — local processing whenever possible; expensive AI only for clips that actually need it.
3. **Reliability** — codecs, long videos, batch jobs, interrupted jobs, and difficult masks must fail safely.

The long-term advantage is specialization: rather than being a broad AI studio from day one, the product will first become exceptionally strong at **removal and reconstruction**.

---

# 1. Product Vision

## 1.1 Vision

Create a removal-focused video editing system that can automatically decide:

> **what should be removed, where it moves, what is behind it, which reconstruction engine is appropriate, and whether the result is actually good enough.**

The user should not need to understand OCR, optical flow, segmentation, inpainting models, temporal windows, GPU providers, or mask formats.

The user experience should feel like:

1. Add video.
2. Choose what to remove or let Auto detect it.
3. Preview detected regions.
4. Click Remove.
5. Receive a clean video.

Internally, the system may run multiple detectors, trackers, reconstruction engines, and QC passes.

---

## 1.2 Product Positioning

Primary positioning:

> **AI video cleanup optimized for subtitles, watermarks, logos, people and unwanted objects — with automatic quality verification.**

Do not position the product as a copyright or attribution bypass tool.

The product should state that users must have the rights or authorization necessary to edit uploaded content.

---

# 2. Competitive Benchmark: Vmake

## 2.1 Current observed Vmake capabilities

Public Vmake product pages currently advertise:

- Automatic watermark removal
- Static and moving watermark handling
- Smart tracking
- Fixed, animated, and scrolling subtitle removal
- Logo removal
- Object removal
- Person / passerby removal
- Removal zone and protect zone controls
- Smart Pro for harder cases
- Better handling of large text, busy backgrounds, moving or semi-transparent text
- Batch upload of up to 30 videos
- HD export
- Processing often described as roughly 30 seconds to 1 minute depending on clip complexity
- Browser workflow and Chrome `Remake Extension`

The Chrome extension is a thin client that sends visual content into the Vmake workspace rather than performing large AI inference inside the browser.

This validates the intended architecture for our commercial product:

`Chrome Extension -> Workspace/API -> GPU workers -> Result`

## 2.2 Current observed Vmake plan constraints

Vmake pricing currently exposes removal tools through subscription tiers, with higher daily file limits in higher plans.

This suggests their economics are unlikely to rely exclusively on an expensive third-party API for every frame of every job.

Our cost architecture therefore must favor:

1. local/cheap processing,
2. self-hosted GPU processing,
3. expensive external API fallback only when justified.

## 2.3 What we copy vs. what we do not copy

We copy the **product category lessons**, not branding, proprietary UI, models, or implementation.

We should learn from:

- Simple upload-first workflow
- Automatic detection
- Smart tracking
- Protect areas
- Multiple quality tiers
- Batch workflow
- Extension as companion client
- SaaS subscription model

We should differentiate with:

- Explicit automated QC
- Cost-aware engine routing
- Better removal-specialized diagnostics
- Transparent quality fallback
- Local processing modes
- User-selectable privacy modes
- Easier correction when Auto detection is wrong

---

# 3. Users

## 3.1 Primary users

### Creator / Shorts editor
Needs to:
- remove baked-in subtitles,
- remove platform marks from authorized source material,
- create localized versions,
- clean reused footage,
- remove distracting objects,
- process many short clips quickly.

### E-commerce / advertising editor
Needs to:
- remove old text overlays,
- remove obsolete logos,
- clean product backgrounds,
- remove people or objects from ad creatives,
- generate multiple language versions from the same clean master.

### Agency / batch operator
Needs to:
- queue many videos,
- review failed jobs,
- avoid manual frame-by-frame masking,
- predict processing cost,
- preserve consistent export quality.

### Power user
Needs to:
- manually correct detection,
- draw masks,
- define protect areas,
- force a higher-quality engine,
- inspect difficult frames.

---

# 4. Jobs To Be Done

1. **When a video contains burned-in subtitles,** remove the subtitles while reconstructing the hidden background naturally.
2. **When a watermark or logo moves,** track it through the clip and remove it without forcing the user to redraw every frame.
3. **When Auto selects the wrong target,** let the user correct the target quickly with box/brush/protect tools.
4. **When a local method cannot reconstruct the scene cleanly,** escalate automatically to a stronger AI engine.
5. **When a result contains visible artifacts,** detect that automatically and retry/escalate instead of quietly returning a poor file.
6. **When many clips need the same operation,** process them as a queue with resumable jobs.
7. **When the user works from the browser,** let the Chrome extension send the media into the workspace without embedding secret model keys in the extension.

---

# 5. Scope

## 5.1 P0 — Removal Core

Must support:

- Video import
- Video metadata probe
- AV1 / H.264 / H.265 / VP9 decoding through FFmpeg fallback where needed
- Preserve audio
- Subtitle/text detection
- Manual region selection
- Frame range selection
- Fast local removal
- Local HQ temporal reconstruction
- QC gate
- Smart / Smart Pro provider interface
- Output export

## 5.2 P1 — Watermark & Logo

Must support:

- Fixed watermark detection
- Repeated corner logo detection
- Semi-transparent watermark mask refinement
- Moving watermark tracking
- Manual watermark seed box
- Track propagation
- Track correction
- Logo/text distinction where practical
- Multi-region removal

## 5.3 P2 — Generic Object / Person Removal

Must support:

- Click/box object selection
- Video segmentation
- Object track propagation
- Person/passersby removal
- Protect area
- Multiple objects per clip

## 5.4 P3 — Production Workflow

Must support:

- Batch jobs
- Pause/resume
- Crash recovery
- Job history
- Preview result
- Before/after scrub
- Failure reason
- Retry with stronger engine
- Export profiles

## 5.5 P4 — SaaS

Must support:

- Account
- Workspace
- Signed upload/download
- Object storage
- Worker queue
- Usage ledger
- Credits
- Subscription entitlement
- Stripe Checkout
- Stripe Customer Portal
- Webhooks
- Admin cost dashboard

## 5.6 P5 — Chrome Extension

Must support:

- Manifest V3
- Send selected video/media into workspace
- Send current page media URL when legally/technically available
- Open workspace job
- Show job status
- Open/download result

The extension must remain thin. It must not contain provider secret keys or execute remotely-hosted model code.

---

# 6. Non-Goals For Initial Releases

Do not delay the removal product in order to build:

- Full Premiere/CapCut-style timeline editor
- Text-to-video generation
- Voice generation
- General-purpose image generation
- Full multi-track compositing
- Full color-grading suite
- Social media publishing suite

These can be integrated later, but they are not prerequisites for removal parity.

---

# 7. User Experience

## 7.1 Default Auto workflow

1. User selects video.
2. App probes codec, FPS, resolution, duration, audio.
3. App samples frames.
4. Auto analyzer proposes removable tracks:
   - Subtitle/Text
   - Watermark/Logo
   - Person
   - Object
5. User sees highlighted tracks.
6. User accepts/removes/adds tracks.
7. User clicks `Remove`.
8. Router selects engine.
9. Render runs.
10. Automatic QC evaluates result.
11. If QC fails, router retries/escalates.
12. User sees preview and export button.

## 7.2 Manual workflow

Tools:

- Select box
- Brush
- Eraser
- Track
- Add frame range
- Protect zone
- Remove zone
- Expand mask
- Shrink mask
- Feather
- Previous/next problematic frame

## 7.3 Quality modes shown to users

Do not expose model names as the primary UX.

User-facing modes:

### Auto
Recommended. Let router choose.

### Fast
Lowest cost, local when possible.

### High Quality
Prefer temporal/local AI and stronger reconstruction.

### Maximum Quality
Use strongest permitted engine and additional temporal pass.

Internal names such as VOID, TBE, LaMa, provider names and GPU SKUs belong in diagnostics/admin UI.

---

# 8. Detection Architecture

## 8.1 Subtitle/Text detector

Pipeline candidates:

- RapidOCR / DBNet-style detector
- Lightweight text/non-text classifier
- Edge/color cues as fallback
- Temporal clustering

Requirements:

- Korean
- English
- Chinese/Japanese text geometry
- Numbers
- Outlined text
- Drop shadows
- Semi-transparent text
- Animated captions
- Scrolling captions
- Multi-line subtitles

Detection must return:

- frame/time range,
- bounding box,
- polygon when available,
- confidence,
- track id,
- text-like class,
- optional OCR text.

OCR text is useful for track consistency but removal must not depend on perfect transcription.

## 8.2 Watermark/logo detector

Signals:

- Repeated spatial appearance
- Corner persistence
- Alpha/translucency pattern
- Template similarity
- Segmentation confidence
- Motion track consistency

Detection classes:

- fixed logo,
- moving logo,
- semi-transparent watermark,
- tiled/repeated watermark,
- unknown overlay.

## 8.3 Person/object detector

Candidate architecture:

- Object detector
- Video segmentation
- Tracker

Model selection must be verified for commercial licensing before production inclusion.

---

# 9. Tracking Architecture

Tracking is a first-class subsystem, not an implementation detail.

## 9.1 Track model

Each removable entity should become a `RemovalTrack`:

```text
RemovalTrack
- id
- type
- start_time
- end_time
- confidence
- keyframes[]
- masks[] / mask references
- protected_overlap
- motion_score
- opacity_score
- complexity_score
```

## 9.2 Tracking methods

Use a cascade:

1. static persistence matching,
2. box/polygon association,
3. optical flow,
4. tracker/model propagation,
5. segmentation propagation for hard cases.

Do not run the most expensive tracker if static matching is sufficient.

---

# 10. Mask System

The mask system is critical to quality.

Support:

- Binary masks
- Soft/alpha masks
- Polygon masks
- Temporal mask tracks
- Protected masks
- Remove masks

For VOID-compatible jobs, generate quad masks using semantic levels compatible with its input expectations:

- remove region,
- overlap/transition,
- affected region,
- background.

Mask generation must specifically cover:

- glyph core,
- outline,
- shadow,
- glow,
- anti-aliased edge,
- translucent pixels.

A tight mask that leaves shadows is a failure.
A broad mask that destroys background unnecessarily is also a failure.

---

# 11. Reconstruction Engines

## 11.1 Tier 0 — Copy/no-op

Used only for frames with no active mask.

## 11.2 Tier 1 — Fast Local

Candidates:

- OpenCV Telea/Navier-Stokes
- Neighbor interpolation
- Simple edge-aware fill

Use when:

- small target,
- low texture complexity,
- stable background,
- artifact risk is low.

## 11.3 Tier 2 — Local HQ Temporal

Primary technique:

- Temporal Background Exposure style reconstruction
- Neighbor frame search
- Mask-aware motion estimation
- ROI-limited optical flow
- Robust temporal aggregation
- Seam feathering

This tier attempts to reconstruct **real background pixels from nearby frames** instead of hallucinating them.

## 11.4 Tier 3 — Local neural image inpainting

Optional candidates subject to commercial-license validation:

- LaMa/ONNX class of local inpainters

Best for:

- small/medium masked areas,
- scenes where temporal background is insufficient,
- cases where full video diffusion is unnecessary.

## 11.5 Tier 4 — Self-hosted video inpainting

Primary planned high-quality engine:

- Netflix VOID or equivalent commercially usable video inpainting model

Use:

- complex backgrounds,
- large overlays,
- moving camera,
- semi-transparent overlays,
- major temporal reconstruction.

Self-hosting is preferred once utilization justifies GPU infrastructure.

## 11.6 Tier 5 — Maximum-quality second pass

Use:

- temporal refinement,
- second-pass reconstruction,
- hard-scene retry,
- chunk-overlap reconciliation.

## 11.7 External API fallback

fal.ai or another external provider can remain as:

- development accelerator,
- overflow capacity,
- provider redundancy,
- emergency fallback.

It should not be the only long-term production engine if unit economics are materially worse than self-hosting.

---

# 12. Engine Router

The router decides the cheapest engine likely to pass quality requirements.

Input features:

- mask area ratio,
- target type,
- motion magnitude,
- camera motion,
- texture complexity,
- edge density,
- opacity/translucency,
- temporal background availability,
- track stability,
- protected-area proximity,
- face/person overlap,
- clip duration,
- resolution,
- expected dollar cost.

Example routing policy:

```text
if target is small and background stable:
    Fast Local
elif temporal exposure is strong:
    Local HQ Temporal
elif mask is moderate and scene simple:
    Local Neural
elif scene complexity high:
    Self-hosted Video Inpainting
if first high-quality result fails temporal QC:
    Maximum-quality second pass
```

The router must log the reason for each choice.

---

# 13. Automatic Quality Control

A job is not successful merely because the output file exists.

## 13.1 Residual overlay score

Detect:

- residual characters,
- shadow remnants,
- logo fragments,
- repeated edges.

## 13.2 Background damage score

Detect:

- smears,
- broad blur,
- texture collapse,
- stretched regions,
- repeated patches.

## 13.3 Boundary score

Detect:

- hard seams,
- halos,
- color discontinuity,
- edge rings.

## 13.4 Temporal consistency score

Detect:

- flicker,
- ghosting,
- texture popping,
- unstable color,
- moving seams.

## 13.5 Outside-mask preservation

Pixels outside the intended edit area should remain as close as possible to the original unless explicitly required for reconstruction blending.

## 13.6 Subject preservation

Special attention near:

- faces,
- hands,
- products,
- foreground objects,
- protected zones.

## 13.7 Media integrity

Requirements:

- decode success,
- audio preserved,
- A/V sync,
- duration accuracy,
- valid timestamps,
- correct rotation,
- no unexpected resolution change.

---

# 14. Retry / Escalation Logic

Example:

```text
render Tier 1
    -> QC pass -> return
    -> QC fail -> Tier 2

render Tier 2
    -> QC pass -> return
    -> QC fail -> Tier 4

render Tier 4
    -> QC pass -> return
    -> temporal QC fail -> Tier 5

Tier 5 fail
    -> mark Needs Review
    -> surface problematic frames to user
```

Never hide fallback behavior.

Internal job diagnostics must show:

- attempted engines,
- elapsed time,
- cost,
- QC scores,
- failure reason.

---

# 15. Batch Processing

Target parity: at least **30 concurrent queued input files** in the UI.

This does not imply 30 simultaneous GPU executions.

Requirements:

- Queue
- Concurrency limits
- Per-job state
- Pause
- Cancel
- Retry
- Resume after crash
- Persist job manifest
- Per-job cost estimate
- Mixed success/failure handling

States:

```text
QUEUED
ANALYZING
WAITING_FOR_CONFIRMATION
PROCESSING_LOCAL
PROCESSING_CLOUD
QC
RETRYING
COMPLETED
FAILED
NEEDS_REVIEW
CANCELLED
```

---

# 16. Windows App

Windows is the rapid-development validation client.

Requirements:

- One reliable `.exe` launcher
- No fragile Korean-encoded BAT dependency
- Bundled or automatically located FFmpeg
- Clear first-run dependency diagnostics
- Drag & drop
- Hardware capability detection
- Local temp management
- Crash log
- Job resume manifest

The GUI must expose:

- video preview,
- timeline,
- region/mask editor,
- target tracks,
- before/after preview,
- quality mode,
- queue.

---

# 17. Web App Architecture

Recommended topology:

```text
Web Client
   |
API / Auth
   |
Job Orchestrator
   |---------------------|
Local/Cheap Workers      GPU Smart Workers
   |                     |
QC Worker <--------------|
   |
Object Storage
   |
Result/CDN
```

Suggested components:

- Frontend: React / Next.js
- API: TypeScript or Python service
- DB: PostgreSQL
- Auth: Supabase/Auth provider or equivalent
- Storage: S3-compatible / Cloudflare R2
- Queue: Redis/managed queue/cloud queue
- Workers: containerized FFmpeg/OpenCV/model runtime
- GPU: RunPod/serverless/dedicated pool initially
- Billing: Stripe

The core engine API must remain provider-agnostic.

---

# 18. Chrome Extension

Chrome extension is a companion surface, not the inference engine.

Requirements:

- Manifest V3
- Minimal permissions
- Right-click/send media where supported
- Open selected media in cleanup workspace
- Login/session handoff
- Job-status display
- Result link

Do not embed:

- Stripe secret key
- fal key
- RunPod key
- storage secrets
- model provider secrets

Server-side proxy all privileged operations.

---

# 19. Billing & Unit Economics

## 19.1 Pricing principle

Do not price solely by `file count` internally.

Internal cost meter should track:

- processed video seconds,
- resolution multiplier,
- engine tier,
- GPU seconds,
- retries,
- storage,
- egress.

## 19.2 User-facing model

Candidate model:

- Free trial seconds/minutes
- Creator subscription
- Pro subscription
- Additional AI credits
- Batch/agency plan later

Simple local jobs should consume little or no premium AI credit.
Hard generative inpainting should consume more.

## 19.3 Cost target

Long-term objective:

- Route a majority of easy cleanup jobs through local/cheap processing.
- Self-host high-quality video inpainting when GPU utilization makes it cheaper than per-call APIs.
- Maintain at least one external API fallback.

---

# 20. Privacy & Security

Requirements:

- TLS uploads
- Signed storage URLs
- Short-lived credentials
- Explicit deletion policy
- Configurable retention
- Server-side provider secrets
- No secrets in extension
- No secrets committed to GitHub
- Sanitize filenames
- Validate media/container input
- Sandbox worker execution

Optional paid differentiator:

- `Local-only` privacy mode for jobs supported entirely by local engines.

---

# 21. Rights / Acceptable Use Product Requirement

The product should be marketed for legitimate editing workflows such as:

- cleaning owned footage,
- removing obsolete overlays from source footage,
- localization,
- authorized brand asset updates,
- removing distracting objects,
- restoring footage.

Terms and UI should require users to have necessary rights or permission to edit content.

Do not advertise the product as a way to evade attribution, ownership controls, DRM, or copyright restrictions.

---

# 22. Commercial Licensing Rules

No model or dependency becomes a production default until its license is checked for commercial use.

Current policy:

- Prefer Apache-2.0 / MIT / BSD style components.
- Keep a `THIRD_PARTY_LICENSES.md` inventory.
- Store model license metadata with each engine adapter.
- Block production activation of unknown/non-commercial licenses.

Examples already identified:

- Netflix VOID: candidate for commercial use; Apache-2.0 repository/model path to be verified at integration time.
- RapidOCR: preferred OCR candidate due permissive licensing; exact packaged models/dependencies to be inventoried.
- ProPainter: do not use as a default commercial production engine without separate permission because its upstream project is non-commercially licensed.
- E2FGVI: do not use as a default commercial production engine without separate permission.

---

# 23. Engineering Loop

Every development loop must follow this sequence:

```text
1. Freeze baseline
2. Pick representative + hard real clips
3. Render baseline
4. Measure automatic quality metrics
5. Visually inspect key frames
6. Classify failures
7. Make the smallest justified change
8. Re-render the same clips
9. A/B compare
10. Run full regression suite
11. Promote only if better
12. Otherwise rollback
13. Record LOOP_LOG
```

Rules:

- A test not actually executed cannot be recorded as PASS.
- A render without errors is not equivalent to a good result.
- Synthetic clips alone are insufficient for stable promotion.
- Real-world codecs must be included.
- Any feature that worsens the stable benchmark is rejected or guarded behind routing.

---

# 24. Benchmark Corpus

Minimum benchmark classes:

## Subtitle
- Korean white text + black shadow
- Multi-line Korean captions
- English subtitles
- Chinese/Japanese glyph-heavy subtitles
- Animated subtitles
- Scrolling subtitles
- Semi-transparent captions
- Captions over faces
- Captions over products

## Watermark/logo
- Static corner logo
- Moving TikTok-style watermark
- Semi-transparent logo
- Repeated/tiled watermark
- Center watermark
- Animated brand bug
- Watermark over detailed background

## Object/person
- Person crossing static background
- Person crossing moving camera
- Small foreground object
- Large object occluding scene
- Object crossing a protected face/product

## Background difficulty
- Flat wall
- Gradient/sky
- Water
- Grass
- Hair
- Foliage
- Textured fabric
- Computer screens
- Product labels
- Rapid camera pan

## Media formats
- H.264
- H.265
- AV1
- VP9
- 24/25/30/60 fps
- 720p/1080p/vertical 9:16
- Audio and no-audio clips
- Korean/special-character filenames

---

# 25. Core Metrics

## Detection
- Recall
- Precision
- Track stability
- False-positive area

## Mask
- Ground-truth mask overlap on synthetic/annotated data
- Shadow/outline coverage
- Excess-mask ratio

## Reconstruction
- Residual text/logo score
- Seam score
- Texture preservation
- Temporal flicker score
- Outside-mask difference

## Reliability
- Decode success rate
- Export success rate
- Crash rate
- Retry success rate
- Resume success rate

## Performance
- Seconds processed / wall-clock second
- GPU seconds / video second
- Peak RAM
- Peak VRAM

## Economics
- Cost / processed minute
- Cost / successful job
- Retry cost
- Storage/egress cost

---

# 26. Stable Promotion Gates

A candidate becomes `stable` only when:

- Mandatory regression tests: 100% pass
- No new media-integrity regression
- No significant quality degradation on current stable corpus
- At least one target failure class measurably improves
- No hidden provider fallback is falsely reported as local success
- Cost increase is justified by quality gain
- Performance remains within tier target
- Real-video visual inspection completed
- LOOP_LOG written

---

# 27. Vmake Parity Scorecard

Track product parity explicitly.

| Capability | Target | Current baseline |
|---|---:|---:|
| Manual subtitle region removal | 100% | Partial/working |
| Auto subtitle detection | 100% | Prototype |
| Animated subtitle tracking | 100% | Incomplete |
| Static watermark removal | 100% | Planned |
| Moving watermark tracking | 100% | Planned |
| Semi-transparent watermark | 100% | Planned |
| Logo removal | 100% | Planned |
| Protect zone | 100% | Planned |
| Brush/eraser editor | 100% | Planned |
| Generic object removal | 100% | Planned |
| Person/passersby removal | 100% | Planned |
| Automatic engine routing | 100% | Prototype |
| Automatic QC | > Vmake target | Prototype |
| Batch 30 | 100% | Planned |
| Crash resume | 100% | Planned |
| Web workspace | 100% | Planned |
| Chrome extension companion | 100% | Planned |
| Subscription/credits | 100% | Planned |
| Self-hosted high-quality engine | > Vmake cost target | Planned |

`Vmake parity` is reached only when core removal categories, tracking, manual correction, batch workflow, web delivery and commercial operations are all production-ready.

`Vmake surpassed` requires demonstrably better benchmark quality or materially better cost/latency on our benchmark corpus.

---

# 28. Delivery Phases

## Phase A — Stabilize subtitle core

- Fix Windows launcher/package
- Harden AV1/codec fallback
- Finish subtitle track detection
- Improve masks for outline/shadow
- Local HQ optimization
- Smart provider execution
- Automated QC

Exit criterion:

A representative subtitle corpus can be processed without manual frame-by-frame editing, and hard cases reliably escalate rather than returning poor local results.

## Phase B — Watermark/logo parity

- Fixed watermark detector
- Moving watermark tracker
- Semi-transparent mask support
- Multi-track removal
- Protect zones
- Manual correction tools

Exit criterion:

Static, moving and semi-transparent watermark benchmark classes are all supported.

## Phase C — Object/person removal

- Segmentation
- Track propagation
- Person/passersby mode
- Object mode
- Protect subject

## Phase D — Production workflow

- Queue
- Batch 30
- Resume
- Job history
- Before/after review
- Export profiles

## Phase E — Web/SaaS

- API
- Auth
- Storage
- GPU workers
- Usage ledger
- Stripe
- Admin cost telemetry

## Phase F — Chrome companion

- MV3 extension
- Send to workspace
- Track status
- Open result

---

# 29. Immediate Next Engineering Loops

## Loop 008

Goal: packaging reliability + removal-core correctness.

- Remove fragile CMD/BAT encoding dependency
- Build a reliable Windows launcher path
- Add package self-check
- Validate FFmpeg discovery
- Run on current AV1 real sample

## Loop 009

Goal: `RemovalTrack` abstraction.

- Unify subtitle/watermark target representation
- Add track persistence
- Add temporal region editor
- Add track JSON serialization

## Loop 010

Goal: fixed watermark MVP.

- Detect repeated/persistent overlay region
- Manual seed box
- Static logo track
- Local HQ reconstruction
- QC

## Loop 011

Goal: moving watermark.

- Optical-flow/track propagation
- Jumping watermark handling
- Lost-track reacquisition
- Correctable keyframes

## Loop 012

Goal: alpha/semi-transparent watermark.

- opacity estimation
- mask refinement
- shadow/glow support
- residual artifact metric

## Loop 013+

- Video segmentation for objects/people
- Self-hosted VOID benchmark
- GPU cost benchmark
- Batch/resume
- Web worker extraction

---

# 30. Definition of Product Completion

This project is **not complete** when one sample looks good.

V1 commercial readiness requires:

1. Subtitle/text removal is production-stable.
2. Fixed and moving watermark removal is production-stable.
3. Manual correction tools are usable.
4. Hard jobs escalate automatically.
5. QC rejects visibly bad results at a useful rate.
6. Batch jobs recover from interruption.
7. Windows package installs/runs reliably.
8. Backend secrets are not shipped to clients.
9. Unit economics are measured from real GPU workloads.
10. Licensing inventory is complete.
11. Real benchmark corpus passes stable promotion gates.
12. Web/SaaS payment path works before public paid launch.

Vmake parity requires additional object/person removal, browser workspace, Chrome companion, strong batch UX and comparable end-user simplicity.

---

# 31. Reference Links Used For Benchmarking

Competitor/product references:

- https://vmake.ai/video-watermark-remover
- https://vmake.ai/ko/remove-object-from-video
- https://vmake.ai/pricing
- https://chromewebstore.google.com/detail/remake-extension/pidpaikimepkaeagcodlhgamignmfeah

Technical research references to validate during implementation:

- Netflix VOID: https://github.com/netflix/void-model
- RapidOCR: https://github.com/RapidAI/RapidOCR
- FFmpeg: https://ffmpeg.org/

All third-party code/model integrations require a fresh license review at the time of production inclusion.

---

# 32. Governing Product Rule

> **The strongest engine is not always the correct engine. The correct engine is the cheapest engine that can produce a result that passes quality requirements — and the system must know when it failed.**

# Loop 030 — main promotion and CI hardening

Date: 2026-09-16

## Repository / baseline audit
- `main` was still the standalone bootstrap commit while `feature/vmake-parity-core` was 67 commits ahead.
- Development head `3df5d79cba269985fa06aefa7ad76d2f34bd01a6` had a successful GitHub Actions run (`35103057405`) on Python 3.10 and 3.12.
- The main-promotion blocker in repository plumbing was that CI only listened to pushes on `feature/vmake-parity-core`; a promoted `main` would not receive equivalent push validation.
- No new video-quality claim is made in this loop. The existing real-video subtitle fixture notes still show that whole subtitle-box removal can damage background content and that tighter glyph/mask reconstruction remains the quality priority.

## External technique / license refresh
- Meta SAM 2 remains a production-eligible mask propagation candidate; official code/checkpoints are Apache-2.0. The Hugging Face `facebook/sam2-hiera-small` checkpoint is also marked Apache-2.0 and has a safetensors representation.
- Cutie and XMem remain viable video-object-segmentation/tracking candidates under MIT licenses; adoption still requires integration/runtime benchmarking against the current lightweight core.
- ProPainter remains excluded from the commercial production path because its upstream license is non-commercial only.
- E2FGVI remains excluded from the commercial production path because its upstream license is CC BY-NC 4.0 / non-commercial.

## Change kept
- CI push coverage now includes both `feature/vmake-parity-core` and `main` and adds manual dispatch support.
- Commit `66009b8d63dd64944bbbc05eeee4c03196c3a24f` passed GitHub Actions run `35106667636` before promotion.
- `main` was fast-forwarded to that verified commit without force-push.

## Promotion decision
**PROMOTED CORE TO `main`.**

Promotion means the executable core, tests, commercial-license guardrails, subtitle consensus/mask primitives, local VSR adapter, QC/escalation, scene-aware chunking/windows, and tracking safety checks are now the stable repository baseline. It does **not** claim Vmake-quality parity yet; objective paired clean/overlay video benchmarking and tighter text-shaped masks remain open work.

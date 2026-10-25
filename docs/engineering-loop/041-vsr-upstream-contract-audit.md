# 041 — raw VideoSubtitleRemover contract and licensing audit

Date: 2026-10-26
Audited upstream: `ppzflpp/VideoSubtitleRemover`
Audited commit: `af4f257`

## Why this audit was required

The local adapter previously described its target as an MIT-licensed VideoSubtitleRemover CLI and generated arguments such as `--gpu`, `--lang`, `--crf`, `--json`, and `--config`. That assumption had only been exercised against fake test processes. Real-video validation requires proving that the destructive backend interface and its commercial terms actually exist.

## Upstream evidence

The reviewed upstream snapshot does not expose the assumed production CLI:

- the documented source entrypoint is `python main.py`, which launches a PyQt GUI;
- repository searches found no application-level argparse contract matching the adapter's assumed `--gpu/--lang/--crf/--json/--config` interface;
- the README states that an NVIDIA GPU is required, with a GTX 1060 given as the minimum;
- model weights are downloaded separately and placed under `models/big-lama`, `models/sttn`, and `models/propainter`;
- the checked-out repository root contains no `LICENSE` file establishing commercial-use terms for the aggregate application;
- the application advertises ProPainter support, while this project already excludes ProPainter from the production dependency path because of non-commercial constraints.

Absence of a root license is not evidence that the software is forbidden; it is evidence that this repository snapshot cannot be treated as commercially approved without further rights verification.

## Safety decision

Do not execute the raw GUI project as the production removal backend and do not infer compatibility from a similarly named project.

The shorts-editor adapter now uses a fail-closed bridge contract:

1. destructive execution requires `commercial_use_approved=True`;
2. an explicit `backend_license` record is required with that approval;
3. before any processing, the runner must answer `--capabilities --json`;
4. the response must declare protocol `shorts-editor-vsr-bridge/v1`;
5. the bridge must advertise the requested mode and support both JSON output and config overlays.

A raw upstream executable that does not implement this handshake is rejected before destructive processing.

## Validation

Focused bridge tests cover:

- unapproved backend rejection before execution;
- incompatible protocol rejection;
- accepted reviewed bridge handshake;
- requested-mode enforcement;
- end-to-end fake bridge execution with precise-mask config.

The existing engine/mask tests remain unchanged, so the hardening narrows execution eligibility without broadening destructive masks.

## Remaining gate

A real reconstruction backend still needs all of the following before Vmake-parity claims:

- commercially verified code and model-weight terms;
- a reviewed bridge implementing the v1 contract;
- an executable runtime on authorized hardware;
- real private-clip renders;
- residual/flicker/boundary/protected-region QC on those renders.

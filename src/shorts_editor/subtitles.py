from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import mean
from unicodedata import normalize

from .tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


def _real(value: object, name: str, *, low: float | None = None, high: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    value = float(value)
    if not isfinite(value):
        raise ValueError(f"{name} must be finite")
    if low is not None and value < low:
        raise ValueError(f"{name} must be >= {low}")
    if high is not None and value > high:
        raise ValueError(f"{name} must be <= {high}")
    return value


def _integer(value: object, name: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


@dataclass(frozen=True)
class OCRDetection:
    """One OCR/text-detector observation in normalized frame coordinates."""

    frame_index: int
    box: BoundingBox
    confidence: float
    text: str = ""

    def __post_init__(self) -> None:
        _integer(self.frame_index, "frame_index", minimum=0)
        _real(self.confidence, "confidence", low=0.0, high=1.0)
        if not isinstance(self.text, str):
            raise TypeError("text must be a string")


@dataclass(frozen=True)
class SubtitleConsensusConfig:
    """Conservative geometry/temporal gates for OCR subtitle consensus.

    These defaults deliberately avoid a hard-coded bottom strip: captions may be
    near the top, above lower-thirds or UI. Position contributes to ranking,
    while temporal support and confidence are the primary evidence.
    """

    min_confidence: float = 0.45
    min_center_y: float = 0.03
    max_center_y: float = 0.98
    max_box_height: float = 0.24
    line_center_tolerance: float = 0.035
    multiline_gap: float = 0.065
    track_y_tolerance: float = 0.09
    track_x_tolerance: float = 0.34
    max_frame_gap: int = 18
    min_support_frames: int = 2
    min_support_ratio: float = 0.24
    max_candidates_per_frame: int = 3
    padding_x: float = 0.012
    padding_y: float = 0.010

    def __post_init__(self) -> None:
        for name in (
            "min_confidence",
            "min_center_y",
            "max_center_y",
            "max_box_height",
            "line_center_tolerance",
            "multiline_gap",
            "track_y_tolerance",
            "track_x_tolerance",
            "min_support_ratio",
            "padding_x",
            "padding_y",
        ):
            _real(getattr(self, name), name, low=0.0, high=1.0)
        if self.min_center_y >= self.max_center_y:
            raise ValueError("min_center_y must be below max_center_y")
        _integer(self.max_frame_gap, "max_frame_gap", minimum=1)
        _integer(self.min_support_frames, "min_support_frames", minimum=1)
        _integer(self.max_candidates_per_frame, "max_candidates_per_frame", minimum=1)


@dataclass(frozen=True)
class SubtitleTrackCandidate:
    track: RemovalTrack
    score: float
    support_ratio: float
    text_change_ratio: float

    def __post_init__(self) -> None:
        for name in ("score", "support_ratio", "text_change_ratio"):
            _real(getattr(self, name), name, low=0.0, high=1.0)
        if self.track.kind is not TargetKind.SUBTITLE:
            raise ValueError("subtitle candidate must carry a subtitle track")


def normalize_ocr_text(text: str) -> str:
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    return "".join(ch for ch in normalize("NFKC", text).casefold() if ch.isalnum())


def _union_boxes(boxes: tuple[BoundingBox, ...] | list[BoundingBox], *, pad_x: float = 0.0, pad_y: float = 0.0) -> BoundingBox:
    if not boxes:
        raise ValueError("at least one box is required")
    pad_x = _real(pad_x, "pad_x", low=0.0, high=1.0)
    pad_y = _real(pad_y, "pad_y", low=0.0, high=1.0)
    x1 = max(0.0, min(box.x for box in boxes) - pad_x)
    y1 = max(0.0, min(box.y for box in boxes) - pad_y)
    x2 = min(1.0, max(box.x + box.width for box in boxes) + pad_x)
    y2 = min(1.0, max(box.y + box.height for box in boxes) + pad_y)
    return BoundingBox(x1, y1, x2 - x1, y2 - y1)


def _vertical_gap(a: BoundingBox, b: BoundingBox) -> float:
    a1, a2 = a.y, a.y + a.height
    b1, b2 = b.y, b.y + b.height
    if a2 < b1:
        return b1 - a2
    if b2 < a1:
        return a1 - b2
    return 0.0


def _horizontal_overlap_ratio(a: BoundingBox, b: BoundingBox) -> float:
    left = max(a.x, b.x)
    right = min(a.x + a.width, b.x + b.width)
    overlap = max(0.0, right - left)
    return overlap / max(min(a.width, b.width), 1e-9)


def _subtitle_like(detection: OCRDetection, config: SubtitleConsensusConfig) -> bool:
    _, cy = detection.box.center
    return (
        detection.confidence >= config.min_confidence
        and config.min_center_y <= cy <= config.max_center_y
        and detection.box.height <= config.max_box_height
    )


def _frame_blocks(detections: list[OCRDetection], config: SubtitleConsensusConfig) -> list[tuple[BoundingBox, float, str]]:
    """Fuse OCR word/line boxes into a small set of subtitle-block candidates."""
    usable = [det for det in detections if _subtitle_like(det, config)]
    if not usable:
        return []

    lines: list[list[OCRDetection]] = []
    for det in sorted(usable, key=lambda d: (d.box.center[1], d.box.x)):
        best: list[OCRDetection] | None = None
        best_delta = 10.0
        for line in lines:
            line_cy = mean(item.box.center[1] for item in line)
            delta = abs(det.box.center[1] - line_cy)
            if delta <= config.line_center_tolerance and delta < best_delta:
                best, best_delta = line, delta
        if best is None:
            lines.append([det])
        else:
            best.append(det)

    line_blocks: list[tuple[BoundingBox, float, str]] = []
    for line in lines:
        box = _union_boxes([item.box for item in line])
        confidence = sum(item.confidence * item.box.width for item in line) / max(
            sum(item.box.width for item in line), 1e-9
        )
        text = " ".join(item.text.strip() for item in sorted(line, key=lambda d: d.box.x) if item.text.strip())
        line_blocks.append((box, confidence, text))

    blocks: list[list[tuple[BoundingBox, float, str]]] = []
    for item in sorted(line_blocks, key=lambda value: value[0].y):
        box, _, _ = item
        best: list[tuple[BoundingBox, float, str]] | None = None
        for block in blocks:
            merged = _union_boxes([part[0] for part in block])
            center_delta = abs(box.center[0] - merged.center[0])
            if _vertical_gap(box, merged) <= config.multiline_gap and (
                center_delta <= 0.18 or _horizontal_overlap_ratio(box, merged) >= 0.20
            ):
                best = block
                break
        if best is None:
            blocks.append([item])
        else:
            best.append(item)

    result: list[tuple[BoundingBox, float, str]] = []
    for block in blocks:
        box = _union_boxes([part[0] for part in block], pad_x=config.padding_x, pad_y=config.padding_y)
        confidence = sum(part[1] for part in block) / len(block)
        text = "\n".join(part[2] for part in block if part[2])
        result.append((box, confidence, text))

    def block_rank(item: tuple[BoundingBox, float, str]) -> float:
        box, confidence, _ = item
        cx, cy = box.center
        centered = 1.0 - min(1.0, abs(cx - 0.5) / 0.5)
        width_prior = min(1.0, box.width / 0.55)
        lower_prior = min(1.0, max(0.0, (cy - config.min_center_y) / max(config.max_center_y - config.min_center_y, 1e-9)))
        return 0.55 * confidence + 0.20 * centered + 0.15 * width_prior + 0.10 * lower_prior

    result.sort(key=block_rank, reverse=True)
    return result[: config.max_candidates_per_frame]


@dataclass
class _TrackBuilder:
    observations: list[tuple[int, BoundingBox, float, str]]

    @property
    def last(self) -> tuple[int, BoundingBox, float, str]:
        return self.observations[-1]


def _association_cost(previous: BoundingBox, current: BoundingBox, config: SubtitleConsensusConfig) -> float | None:
    px, py = previous.center
    cx, cy = current.center
    dy = abs(cy - py)
    dx = abs(cx - px)
    if dy > config.track_y_tolerance or dx > config.track_x_tolerance:
        return None
    height_delta = abs(current.height - previous.height)
    return dy + (0.35 * dx) + (0.25 * height_delta)


def detect_subtitle_tracks(
    detections: tuple[OCRDetection, ...] | list[OCRDetection],
    config: SubtitleConsensusConfig | None = None,
) -> tuple[SubtitleTrackCandidate, ...]:
    """Build stable subtitle-region tracks from arbitrary OCR detections."""
    if config is None:
        config = SubtitleConsensusConfig()
    if not isinstance(config, SubtitleConsensusConfig):
        raise TypeError("config must be SubtitleConsensusConfig")
    if not isinstance(detections, (tuple, list)):
        raise TypeError("detections must be a sequence")
    if any(not isinstance(det, OCRDetection) for det in detections):
        raise TypeError("detections must contain OCRDetection values")
    if not detections:
        return ()

    by_frame: dict[int, list[OCRDetection]] = {}
    for det in detections:
        by_frame.setdefault(det.frame_index, []).append(det)
    observed_frames = tuple(sorted(by_frame))

    builders: list[_TrackBuilder] = []
    for frame_index in observed_frames:
        blocks = _frame_blocks(by_frame[frame_index], config)
        claimed: set[int] = set()
        for box, confidence, text in blocks:
            choice: int | None = None
            choice_cost = 10.0
            for idx, builder in enumerate(builders):
                if idx in claimed:
                    continue
                prev_frame, prev_box, _, _ = builder.last
                gap = frame_index - prev_frame
                if gap <= 0 or gap > config.max_frame_gap:
                    continue
                cost = _association_cost(prev_box, box, config)
                if cost is not None and cost < choice_cost:
                    choice, choice_cost = idx, cost
            observation = (frame_index, box, confidence, text)
            if choice is None:
                builders.append(_TrackBuilder([observation]))
            else:
                builders[choice].observations.append(observation)
                claimed.add(choice)

    candidates: list[SubtitleTrackCandidate] = []
    observed_count = len(observed_frames)
    for builder in builders:
        obs = builder.observations
        if len(obs) < config.min_support_frames:
            continue
        support_ratio = len({item[0] for item in obs}) / observed_count
        if support_ratio < config.min_support_ratio:
            continue
        samples = tuple(TrackSample(frame, box, confidence) for frame, box, confidence, _ in obs)
        track = RemovalTrack(f"subtitle-{len(candidates) + 1}", TargetKind.SUBTITLE, samples)

        normalized_texts: list[str] = []
        for _, _, _, text in obs:
            normalized = normalize_ocr_text(text)
            if normalized:
                normalized_texts.append(normalized)
        if len(normalized_texts) <= 1:
            text_change_ratio = 0.0
        else:
            transitions = sum(a != b for a, b in zip(normalized_texts, normalized_texts[1:]))
            text_change_ratio = transitions / (len(normalized_texts) - 1)

        mean_cx = mean(sample.box.center[0] for sample in samples)
        mean_cy = mean(sample.box.center[1] for sample in samples)
        mean_width = mean(sample.box.width for sample in samples)
        centered = 1.0 - min(1.0, abs(mean_cx - 0.5) / 0.5)
        lower = min(1.0, max(0.0, (mean_cy - config.min_center_y) / max(config.max_center_y - config.min_center_y, 1e-9)))
        width_prior = min(1.0, mean_width / 0.55)
        stability = 1.0 - min(1.0, track.max_center_velocity() / 0.06)
        score = (
            0.32 * support_ratio
            + 0.25 * track.mean_confidence
            + 0.13 * centered
            + 0.08 * lower
            + 0.08 * width_prior
            + 0.09 * stability
            + 0.05 * text_change_ratio
        )
        candidates.append(
            SubtitleTrackCandidate(
                track=track,
                score=round(min(1.0, max(0.0, score)), 4),
                support_ratio=round(support_ratio, 4),
                text_change_ratio=round(text_change_ratio, 4),
            )
        )

    candidates.sort(key=lambda candidate: (candidate.score, candidate.support_ratio, candidate.track.mean_confidence), reverse=True)
    ranked: list[SubtitleTrackCandidate] = []
    for index, candidate in enumerate(candidates, start=1):
        track = RemovalTrack(f"subtitle-{index}", TargetKind.SUBTITLE, candidate.track.samples)
        ranked.append(SubtitleTrackCandidate(track, candidate.score, candidate.support_ratio, candidate.text_change_ratio))
    return tuple(ranked)


def best_subtitle_track(
    detections: tuple[OCRDetection, ...] | list[OCRDetection],
    config: SubtitleConsensusConfig | None = None,
) -> SubtitleTrackCandidate | None:
    candidates = detect_subtitle_tracks(detections, config)
    return candidates[0] if candidates else None


def densify_track(track: RemovalTrack, max_gap_frames: int = 3, confidence_decay: float = 0.92) -> RemovalTrack:
    """Linearly fill short detector dropouts without bridging long unknown spans."""
    if not isinstance(track, RemovalTrack):
        raise TypeError("track must be a RemovalTrack")
    max_gap_frames = _integer(max_gap_frames, "max_gap_frames", minimum=0)
    confidence_decay = _real(confidence_decay, "confidence_decay", low=0.0, high=1.0)
    if len(track.samples) < 2 or max_gap_frames == 0:
        return track

    output: list[TrackSample] = []
    for left, right in zip(track.samples, track.samples[1:]):
        output.append(left)
        missing = right.frame_index - left.frame_index - 1
        if 0 < missing <= max_gap_frames:
            for offset in range(1, missing + 1):
                ratio = offset / (missing + 1)
                lb, rb = left.box, right.box
                box = BoundingBox(
                    lb.x + (rb.x - lb.x) * ratio,
                    lb.y + (rb.y - lb.y) * ratio,
                    lb.width + (rb.width - lb.width) * ratio,
                    lb.height + (rb.height - lb.height) * ratio,
                )
                confidence = min(left.confidence, right.confidence) * confidence_decay
                output.append(TrackSample(left.frame_index + offset, box, confidence))
    output.append(track.samples[-1])
    output.sort(key=lambda sample: sample.frame_index)
    return RemovalTrack(track.track_id, track.kind, tuple(output))


def temporal_union_track(
    track: RemovalTrack,
    radius_frames: int = 1,
    *,
    padding_x: float = 0.006,
    padding_y: float = 0.004,
) -> RemovalTrack:
    """Local temporal envelope that stabilizes OCR/text mask edges."""
    if not isinstance(track, RemovalTrack):
        raise TypeError("track must be a RemovalTrack")
    if track.kind not in (TargetKind.SUBTITLE, TargetKind.TEXT, TargetKind.WATERMARK, TargetKind.LOGO):
        raise ValueError("temporal union is only valid for overlay-like tracks")
    radius_frames = _integer(radius_frames, "radius_frames", minimum=0)
    padding_x = _real(padding_x, "padding_x", low=0.0, high=1.0)
    padding_y = _real(padding_y, "padding_y", low=0.0, high=1.0)
    if radius_frames == 0 and padding_x == 0.0 and padding_y == 0.0:
        return track

    samples: list[TrackSample] = []
    for sample in track.samples:
        neighbours = [
            other.box
            for other in track.samples
            if abs(other.frame_index - sample.frame_index) <= radius_frames
        ]
        union = _union_boxes(neighbours, pad_x=padding_x, pad_y=padding_y)
        samples.append(TrackSample(sample.frame_index, union, sample.confidence))
    return RemovalTrack(track.track_id, track.kind, tuple(samples))


def refine_subtitle_track(
    track: RemovalTrack,
    *,
    max_gap_frames: int = 3,
    union_radius_frames: int = 1,
    padding_x: float = 0.006,
    padding_y: float = 0.004,
) -> RemovalTrack:
    """Fill short OCR misses, then stabilize the removal envelope in time."""
    if not isinstance(track, RemovalTrack):
        raise TypeError("track must be a RemovalTrack")
    if track.kind is not TargetKind.SUBTITLE:
        raise ValueError("refine_subtitle_track requires a subtitle track")
    dense = densify_track(track, max_gap_frames=max_gap_frames)
    return temporal_union_track(
        dense,
        radius_frames=union_radius_frames,
        padding_x=padding_x,
        padding_y=padding_y,
    )
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Integral, Real
from statistics import mean
from unicodedata import normalize

from .tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


def _real(value: object, name: str, *, low: float | None = None, high: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
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
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    value = int(value)
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
    return detection.confidence >= config.min_confidence and config.min_center_y <= cy <= config.max_center_y and detection.box.height <= config.max_box_height


def _frame_blocks(detections: list[OCRDetection], config: SubtitleConsensusConfig) -> list[tuple[BoundingBox, float, str]]:
    usable = [det for det in detections if _subtitle_like(det, config)]
    if not usable:
        return []
    lines: list[list[OCRDetection]] = []
    for det in sorted(usable, key=lambda d: (d.box.center[1], d.box.x)):
        best = None
        best_delta = 10.0
        for line in lines:
            delta = abs(det.box.center[1] - mean(item.box.center[1] for item in line))
            if delta <= config.line_center_tolerance and delta < best_delta:
                best, best_delta = line, delta
        if best is None: lines.append([det])
        else: best.append(det)
    line_blocks = []
    for line in lines:
        box = _union_boxes([item.box for item in line])
        confidence = sum(item.confidence * item.box.width for item in line) / max(sum(item.box.width for item in line), 1e-9)
        text = " ".join(item.text.strip() for item in sorted(line, key=lambda d: d.box.x) if item.text.strip())
        line_blocks.append((box, confidence, text))
    blocks = []
    for item in sorted(line_blocks, key=lambda value: value[0].y):
        box = item[0]; best = None
        for block in blocks:
            merged = _union_boxes([part[0] for part in block])
            if _vertical_gap(box, merged) <= config.multiline_gap and (abs(box.center[0]-merged.center[0]) <= 0.18 or _horizontal_overlap_ratio(box, merged) >= 0.20):
                best = block; break
        if best is None: blocks.append([item])
        else: best.append(item)
    result = []
    for block in blocks:
        box = _union_boxes([part[0] for part in block], pad_x=config.padding_x, pad_y=config.padding_y)
        result.append((box, sum(part[1] for part in block)/len(block), "\n".join(part[2] for part in block if part[2])))
    def rank(item):
        box, confidence, _ = item; cx, cy = box.center
        centered = 1.0-min(1.0, abs(cx-0.5)/0.5); width_prior=min(1.0, box.width/0.55)
        lower=min(1.0,max(0.0,(cy-config.min_center_y)/max(config.max_center_y-config.min_center_y,1e-9)))
        return .55*confidence+.20*centered+.15*width_prior+.10*lower
    result.sort(key=rank, reverse=True)
    return result[:config.max_candidates_per_frame]


@dataclass
class _TrackBuilder:
    observations: list[tuple[int, BoundingBox, float, str]]
    @property
    def last(self): return self.observations[-1]


def _association_cost(previous, current, config):
    px,py=previous.center; cx,cy=current.center; dy=abs(cy-py); dx=abs(cx-px)
    if dy>config.track_y_tolerance or dx>config.track_x_tolerance: return None
    return dy+.35*dx+.25*abs(current.height-previous.height)


def detect_subtitle_tracks(detections, config=None):
    if config is None: config=SubtitleConsensusConfig()
    if not isinstance(config, SubtitleConsensusConfig): raise TypeError("config must be SubtitleConsensusConfig")
    if not isinstance(detections,(tuple,list)): raise TypeError("detections must be a sequence")
    if any(not isinstance(det,OCRDetection) for det in detections): raise TypeError("detections must contain OCRDetection values")
    if not detections: return ()
    by_frame={}
    for det in detections: by_frame.setdefault(det.frame_index,[]).append(det)
    observed_frames=tuple(sorted(by_frame)); builders=[]
    for frame_index in observed_frames:
        claimed=set()
        for box,confidence,text in _frame_blocks(by_frame[frame_index],config):
            choice=None; choice_cost=10.0
            for idx,builder in enumerate(builders):
                if idx in claimed: continue
                prev_frame,prev_box,_,_=builder.last; gap=frame_index-prev_frame
                if gap<=0 or gap>config.max_frame_gap: continue
                cost=_association_cost(prev_box,box,config)
                if cost is not None and cost<choice_cost: choice,choice_cost=idx,cost
            observation=(frame_index,box,confidence,text)
            if choice is None: builders.append(_TrackBuilder([observation]))
            else: builders[choice].observations.append(observation); claimed.add(choice)
    candidates=[]; observed_count=len(observed_frames)
    for builder in builders:
        obs=builder.observations
        if len(obs)<config.min_support_frames: continue
        support_ratio=len({item[0] for item in obs})/observed_count
        if support_ratio<config.min_support_ratio: continue
        samples=tuple(TrackSample(frame,box,confidence) for frame,box,confidence,_ in obs); track=RemovalTrack(f"subtitle-{len(candidates)+1}",TargetKind.SUBTITLE,samples)
        texts=[normalize_ocr_text(text) for _,_,_,text in obs if normalize_ocr_text(text)]
        text_change_ratio=0.0 if len(texts)<=1 else sum(a!=b for a,b in zip(texts,texts[1:]))/(len(texts)-1)
        mean_cx=mean(s.box.center[0] for s in samples); mean_cy=mean(s.box.center[1] for s in samples); mean_width=mean(s.box.width for s in samples)
        centered=1-min(1,abs(mean_cx-.5)/.5); lower=min(1,max(0,(mean_cy-config.min_center_y)/max(config.max_center_y-config.min_center_y,1e-9))); width_prior=min(1,mean_width/.55); stability=1-min(1,track.max_center_velocity()/.06)
        score=.32*support_ratio+.25*track.mean_confidence+.13*centered+.08*lower+.08*width_prior+.09*stability+.05*text_change_ratio
        candidates.append(SubtitleTrackCandidate(track,round(min(1,max(0,score)),4),round(support_ratio,4),round(text_change_ratio,4)))
    candidates.sort(key=lambda c:(c.score,c.support_ratio,c.track.mean_confidence),reverse=True)
    return tuple(SubtitleTrackCandidate(RemovalTrack(f"subtitle-{i}",TargetKind.SUBTITLE,c.track.samples),c.score,c.support_ratio,c.text_change_ratio) for i,c in enumerate(candidates,1))


def best_subtitle_track(detections, config=None):
    candidates=detect_subtitle_tracks(detections,config); return candidates[0] if candidates else None


def densify_track(track, max_gap_frames=3, confidence_decay=.92):
    if not isinstance(track,RemovalTrack): raise TypeError("track must be a RemovalTrack")
    max_gap_frames=_integer(max_gap_frames,"max_gap_frames",minimum=0); confidence_decay=_real(confidence_decay,"confidence_decay",low=0,high=1)
    if len(track.samples)<2 or max_gap_frames==0: return track
    output=[]
    for left,right in zip(track.samples,track.samples[1:]):
        output.append(left); missing=right.frame_index-left.frame_index-1
        if missing<=0 or missing>max_gap_frames: continue
        for offset in range(1,missing+1):
            ratio=offset/(missing+1); box=BoundingBox(left.box.x+(right.box.x-left.box.x)*ratio,left.box.y+(right.box.y-left.box.y)*ratio,left.box.width+(right.box.width-left.box.width)*ratio,left.box.height+(right.box.height-left.box.height)*ratio)
            output.append(TrackSample(left.frame_index+offset,box,min(left.confidence,right.confidence)*(confidence_decay**min(offset,missing+1-offset))))
    output.append(track.samples[-1]); output.sort(key=lambda s:s.frame_index); return RemovalTrack(track.track_id,track.kind,tuple(output))


def temporal_union_track(track, radius_frames=1, padding_x=.006, padding_y=.006):
    if not isinstance(track,RemovalTrack): raise TypeError("track must be a RemovalTrack")
    radius_frames=_integer(radius_frames,"radius_frames",minimum=0); padding_x=_real(padding_x,"padding_x",low=0,high=1); padding_y=_real(padding_y,"padding_y",low=0,high=1)
    if radius_frames==0: return track
    return RemovalTrack(track.track_id,track.kind,tuple(TrackSample(s.frame_index,_union_boxes([o.box for o in track.samples if abs(o.frame_index-s.frame_index)<=radius_frames],pad_x=padding_x,pad_y=padding_y),s.confidence) for s in track.samples))


def refine_subtitle_track(track, *, max_gap_frames=3, union_radius_frames=1, padding_x=.006, padding_y=.006):
    return temporal_union_track(densify_track(track,max_gap_frames=max_gap_frames),radius_frames=union_radius_frames,padding_x=padding_x,padding_y=padding_y)

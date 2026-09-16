from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable


@dataclass(frozen=True)
class PreciseMaskPolygon:
    """A fine-grained mask polygon for one source frame.

    Points are normalized ``(x, y)`` coordinates in ``[0, 1]``. The class is
    intentionally model-agnostic: glyph contours may come from OCR geometry,
    colour/stroke segmentation, SAM2 refinement, or manual correction.
    """

    frame_index: int
    points: tuple[tuple[float, float], ...]
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if isinstance(self.frame_index, bool) or not isinstance(self.frame_index, int):
            raise TypeError("frame_index must be an integer")
        if self.frame_index < 0:
            raise ValueError("frame_index must be >= 0")
        if not isinstance(self.points, (tuple, list)) or len(self.points) < 3:
            raise ValueError("points must contain at least three vertices")
        normalized_points: list[tuple[float, float]] = []
        for point in self.points:
            if not isinstance(point, (tuple, list)) or len(point) != 2:
                raise TypeError("each point must be a two-value coordinate")
            for value in point:
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise TypeError("polygon coordinates must be real numbers")
                if not isfinite(value) or not 0.0 <= float(value) <= 1.0:
                    raise ValueError("polygon coordinates must be finite and in [0, 1]")
            normalized_points.append((float(point[0]), float(point[1])))
        object.__setattr__(self, "points", tuple(normalized_points))
        if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
            raise TypeError("confidence must be a real number")
        if not isfinite(self.confidence) or not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be finite and in [0, 1]")
        if self.area_ratio <= 0.0:
            raise ValueError("polygon must have non-zero area")

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        xs = [float(point[0]) for point in self.points]
        ys = [float(point[1]) for point in self.points]
        return min(xs), min(ys), max(xs), max(ys)

    @property
    def area_ratio(self) -> float:
        area = 0.0
        points = self.points
        for left, right in zip(points, points[1:] + points[:1]):
            area += float(left[0]) * float(right[1]) - float(right[0]) * float(left[1])
        return abs(area) * 0.5


def rectangle_mask_polygon(
    frame_index: int,
    *,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    confidence: float = 1.0,
) -> PreciseMaskPolygon:
    """Create a precise polygon from a normalized glyph/stroke rectangle."""
    if not x2 > x1 or not y2 > y1:
        raise ValueError("rectangle must satisfy x2>x1 and y2>y1")
    return PreciseMaskPolygon(
        frame_index,
        ((x1, y1), (x2, y1), (x2, y2), (x1, y2)),
        confidence,
    )


def _bbox_iou(a: PreciseMaskPolygon, b: PreciseMaskPolygon) -> float:
    ax1, ay1, ax2, ay2 = a.bbox
    bx1, by1, bx2, by2 = b.bbox
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if intersection <= 0.0:
        return 0.0
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    return intersection / max(area_a + area_b - intersection, 1e-12)


def dedupe_precise_masks(
    masks: Iterable[PreciseMaskPolygon],
    *,
    iou_threshold: float = 0.88,
) -> tuple[PreciseMaskPolygon, ...]:
    """Suppress duplicate masks on the same frame, keeping higher confidence."""
    if isinstance(iou_threshold, bool) or not isinstance(iou_threshold, (int, float)):
        raise TypeError("iou_threshold must be a real number")
    iou_threshold = float(iou_threshold)
    if not isfinite(iou_threshold) or not 0.0 <= iou_threshold <= 1.0:
        raise ValueError("iou_threshold must be finite and in [0, 1]")

    values = tuple(masks)
    if any(not isinstance(mask, PreciseMaskPolygon) for mask in values):
        raise TypeError("masks must contain PreciseMaskPolygon values")
    kept: list[PreciseMaskPolygon] = []
    for candidate in sorted(values, key=lambda item: (item.frame_index, -item.confidence, -item.area_ratio)):
        duplicate = any(
            previous.frame_index == candidate.frame_index
            and _bbox_iou(previous, candidate) >= iou_threshold
            for previous in kept
        )
        if not duplicate:
            kept.append(candidate)
    return tuple(sorted(kept, key=lambda item: (item.frame_index, item.bbox)))


def _pixel_polygon(mask: PreciseMaskPolygon, frame_width: int, frame_height: int) -> list[int]:
    coords: list[int] = []
    for x, y in mask.points:
        px = max(0, min(frame_width - 1, round(float(x) * (frame_width - 1))))
        py = max(0, min(frame_height - 1, round(float(y) * (frame_height - 1))))
        coords.extend((px, py))
    if len({tuple(coords[index:index + 2]) for index in range(0, len(coords), 2)}) < 3:
        raise ValueError("polygon collapses to fewer than three pixel vertices")
    return coords


def precise_masks_to_vsr_corrections(
    masks: Iterable[PreciseMaskPolygon],
    *,
    frame_width: int,
    frame_height: int,
    fps: float,
    min_confidence: float = 0.30,
    hold_frames: int = 0,
    dedupe_iou: float = 0.88,
    max_polygons_per_frame: int = 192,
) -> list[dict[str, object]]:
    """Convert fine masks to bounded VSR ``manual_mask_corrections``.

    Corrections are short-lived by design so a missed/incorrect glyph cannot
    smear a foreground object across a long clip. VSR OCR stays enabled and
    can still supply masks where fine detections are absent.
    """
    for name, value in (("frame_width", frame_width), ("frame_height", frame_height), ("max_polygons_per_frame", max_polygons_per_frame)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be an integer")
        if value <= 0:
            raise ValueError(f"{name} must be > 0")
    if isinstance(hold_frames, bool) or not isinstance(hold_frames, int):
        raise TypeError("hold_frames must be an integer")
    if hold_frames < 0:
        raise ValueError("hold_frames must be >= 0")
    if isinstance(fps, bool) or not isinstance(fps, (int, float)):
        raise TypeError("fps must be a real number")
    fps = float(fps)
    if not isfinite(fps) or fps <= 0:
        raise ValueError("fps must be finite and > 0")
    if isinstance(min_confidence, bool) or not isinstance(min_confidence, (int, float)):
        raise TypeError("min_confidence must be a real number")
    min_confidence = float(min_confidence)
    if not isfinite(min_confidence) or not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be finite and in [0, 1]")

    raw = tuple(masks)
    if any(not isinstance(mask, PreciseMaskPolygon) for mask in raw):
        raise TypeError("masks must contain PreciseMaskPolygon values")
    filtered = [mask for mask in raw if mask.confidence >= min_confidence]
    deduped = dedupe_precise_masks(filtered, iou_threshold=dedupe_iou)

    by_frame: dict[int, list[PreciseMaskPolygon]] = {}
    for mask in deduped:
        by_frame.setdefault(mask.frame_index, []).append(mask)

    corrections: list[dict[str, object]] = []
    for frame_index in sorted(by_frame):
        selected = sorted(
            by_frame[frame_index],
            key=lambda item: (-item.confidence, -item.area_ratio, item.bbox),
        )[:max_polygons_per_frame]
        polygons = [_pixel_polygon(mask, frame_width, frame_height) for mask in selected]
        if not polygons:
            continue
        start = frame_index / fps
        end = (frame_index + hold_frames + 1) / fps
        corrections.append(
            {
                "polygons": polygons,
                "start": round(start, 6),
                "end": round(end, 6),
            }
        )
    return corrections

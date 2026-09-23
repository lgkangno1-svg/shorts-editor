from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite
from numbers import Integral, Real
from typing import Mapping

from .precision_masks import PreciseMaskPolygon, rectangle_mask_polygon
from .tracks import RemovalTrack, TargetKind, TrackSample


@dataclass(frozen=True)
class CaptionPlateConfig:
    """Conservative detector settings for opaque dark subtitle backplates.

    Detection is intentionally stricter than ordinary glyph masking. A plate is
    destructive to remove because it covers more scene pixels than the text, so
    the detector requires dark support on all four sides of a confirmed subtitle
    box, a visible boundary contrast around the plate, and temporal agreement.
    """

    dark_threshold: float = 0.38
    edge_dark_fraction: float = 0.72
    min_ring_dark_fraction: float = 0.78
    min_edge_contrast: float = 0.10
    min_contrast_sides: int = 2
    max_search_pad_x: float = 0.22
    max_search_pad_y: float = 0.08
    min_margin_x: float = 0.004
    min_margin_y: float = 0.003
    max_plate_height: float = 0.22
    min_plate_aspect: float = 1.8
    min_temporal_support: float = 0.50
    min_support_frames: int = 2
    max_center_y_drift: float = 0.035
    max_height_drift: float = 0.045
    max_bright_gap_pixels: int = 2

    def __post_init__(self) -> None:
        for name in (
            "dark_threshold",
            "edge_dark_fraction",
            "min_ring_dark_fraction",
            "min_edge_contrast",
            "max_search_pad_x",
            "max_search_pad_y",
            "min_margin_x",
            "min_margin_y",
            "max_plate_height",
            "min_temporal_support",
            "max_center_y_drift",
            "max_height_drift",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
            value = float(value)
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")

        if isinstance(self.min_plate_aspect, bool) or not isinstance(self.min_plate_aspect, Real):
            raise TypeError("min_plate_aspect must be a real number")
        if not isfinite(float(self.min_plate_aspect)) or float(self.min_plate_aspect) <= 0.0:
            raise ValueError("min_plate_aspect must be finite and > 0")

        for name, minimum in (("min_contrast_sides", 1), ("min_support_frames", 1), ("max_bright_gap_pixels", 0)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Integral):
                raise TypeError(f"{name} must be an integer")
            if int(value) < minimum:
                raise ValueError(f"{name} must be >= {minimum}")

        if self.min_contrast_sides > 4:
            raise ValueError("min_contrast_sides must be <= 4")
        if self.min_ring_dark_fraction < self.edge_dark_fraction:
            raise ValueError("min_ring_dark_fraction must be >= edge_dark_fraction")


@dataclass(frozen=True)
class CaptionPlateDetection:
    mask: PreciseMaskPolygon
    score: float
    ring_dark_fraction: float
    edge_contrast: float
    margin_x: float
    margin_y: float

    def __post_init__(self) -> None:
        if not isinstance(self.mask, PreciseMaskPolygon):
            raise TypeError("mask must be a PreciseMaskPolygon")
        for name in ("score", "ring_dark_fraction", "edge_contrast", "margin_x", "margin_y"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
            if not isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")


def _require_numpy():
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - exercised only in minimal installs
        raise RuntimeError("opaque caption-plate detection requires NumPy") from exc
    return np


def _normalized_luma(frame: object):
    np = _require_numpy()
    array = np.asarray(frame)
    if array.ndim not in (2, 3):
        raise ValueError("frame must be a 2D grayscale or 3D color array")
    if array.shape[0] < 2 or array.shape[1] < 2:
        raise ValueError("frame must be at least 2x2")

    if array.ndim == 3:
        if array.shape[2] < 1:
            raise ValueError("color frame must contain at least one channel")
        channels = array[..., : min(3, array.shape[2])].astype(np.float32, copy=False)
        luma = channels.mean(axis=2)
    else:
        luma = array.astype(np.float32, copy=False)

    if np.issubdtype(array.dtype, np.integer):
        max_value = float(np.iinfo(array.dtype).max)
        if max_value <= 0.0:
            raise ValueError("integer frame dtype has no positive range")
        luma = luma / max_value
    else:
        if not np.isfinite(luma).all():
            raise ValueError("frame pixels must be finite")
        observed_min = float(luma.min())
        observed_max = float(luma.max())
        if observed_min < 0.0:
            raise ValueError("frame pixels must be non-negative")
        if observed_max > 1.0:
            if observed_max <= 255.0:
                luma = luma / 255.0
            else:
                raise ValueError("floating frame pixels must be in [0,1] or [0,255]")

    if not np.isfinite(luma).all():
        raise ValueError("frame pixels must be finite")
    return np.clip(luma, 0.0, 1.0)


def _pixel_box(sample: TrackSample, width: int, height: int) -> tuple[int, int, int, int]:
    box = sample.box
    x1 = max(0, min(width - 1, round(box.x * width)))
    y1 = max(0, min(height - 1, round(box.y * height)))
    x2 = max(x1 + 1, min(width, round((box.x + box.width) * width)))
    y2 = max(y1 + 1, min(height, round((box.y + box.height) * height)))
    return x1, y1, x2, y2


def _contiguous_margin(profile, *, reverse: bool, threshold: float, max_gap: int) -> int:
    values = profile[::-1] if reverse else profile
    accepted = 0
    gap = 0
    for value in values:
        if float(value) >= threshold:
            accepted += 1 + gap
            gap = 0
            continue
        gap += 1
        if gap > max_gap:
            break
    return accepted


def _ring_arrays(array, *, x1: int, y1: int, x2: int, y2: int, bx1: int, by1: int, bx2: int, by2: int):
    parts = []
    if y1 < by1:
        parts.append(array[y1:by1, x1:x2].reshape(-1))
    if by2 < y2:
        parts.append(array[by2:y2, x1:x2].reshape(-1))
    if x1 < bx1:
        parts.append(array[by1:by2, x1:bx1].reshape(-1))
    if bx2 < x2:
        parts.append(array[by1:by2, bx2:x2].reshape(-1))
    return [part for part in parts if part.size]


def _edge_contrasts(luma, *, x1: int, y1: int, x2: int, y2: int, inside_mean: float) -> tuple[float, ...]:
    height, width = int(luma.shape[0]), int(luma.shape[1])
    thickness = max(1, min(6, round((y2 - y1) * 0.08)))
    outside = []
    if y1 > 0:
        outside.append(luma[max(0, y1 - thickness):y1, x1:x2])
    if y2 < height:
        outside.append(luma[y2:min(height, y2 + thickness), x1:x2])
    if x1 > 0:
        outside.append(luma[y1:y2, max(0, x1 - thickness):x1])
    if x2 < width:
        outside.append(luma[y1:y2, x2:min(width, x2 + thickness)])
    return tuple(max(0.0, float(region.mean()) - inside_mean) for region in outside if region.size)


def detect_opaque_caption_plate(
    frame: object,
    sample: TrackSample,
    config: CaptionPlateConfig | None = None,
) -> CaptionPlateDetection | None:
    """Detect one opaque dark plate around a confirmed subtitle sample.

    Bright glyphs are intentionally ignored while finding the plate boundary:
    only the dark margins outside the OCR box are measured. Natural dark scenes
    are rejected unless the inferred rectangle also has a brighter outer edge on
    enough sides to provide evidence of a real overlay boundary.
    """
    if not isinstance(sample, TrackSample):
        raise TypeError("sample must be a TrackSample")
    if config is None:
        config = CaptionPlateConfig()
    if not isinstance(config, CaptionPlateConfig):
        raise TypeError("config must be CaptionPlateConfig")

    np = _require_numpy()
    luma = _normalized_luma(frame)
    height, width = int(luma.shape[0]), int(luma.shape[1])
    bx1, by1, bx2, by2 = _pixel_box(sample, width, height)
    box_w, box_h = bx2 - bx1, by2 - by1

    search_x = max(
        2,
        min(
            round(width * float(config.max_search_pad_x)),
            max(round(box_w * 1.75), 2),
        ),
    )
    search_y = max(
        2,
        min(
            round(height * float(config.max_search_pad_y)),
            max(round(box_h * 1.75), 2),
        ),
    )
    sx1, sx2 = max(0, bx1 - search_x), min(width, bx2 + search_x)
    sy1, sy2 = max(0, by1 - search_y), min(height, by2 + search_y)
    dark = luma <= float(config.dark_threshold)

    left_profile = dark[by1:by2, sx1:bx1].mean(axis=0) if sx1 < bx1 else np.empty(0)
    right_profile = dark[by1:by2, bx2:sx2].mean(axis=0) if bx2 < sx2 else np.empty(0)
    top_profile = dark[sy1:by1, bx1:bx2].mean(axis=1) if sy1 < by1 else np.empty(0)
    bottom_profile = dark[by2:sy2, bx1:bx2].mean(axis=1) if by2 < sy2 else np.empty(0)

    left = _contiguous_margin(
        left_profile,
        reverse=True,
        threshold=float(config.edge_dark_fraction),
        max_gap=int(config.max_bright_gap_pixels),
    )
    right = _contiguous_margin(
        right_profile,
        reverse=False,
        threshold=float(config.edge_dark_fraction),
        max_gap=int(config.max_bright_gap_pixels),
    )
    top = _contiguous_margin(
        top_profile,
        reverse=True,
        threshold=float(config.edge_dark_fraction),
        max_gap=int(config.max_bright_gap_pixels),
    )
    bottom = _contiguous_margin(
        bottom_profile,
        reverse=False,
        threshold=float(config.edge_dark_fraction),
        max_gap=int(config.max_bright_gap_pixels),
    )

    min_margin_x_px = max(1, round(width * float(config.min_margin_x)))
    min_margin_y_px = max(1, round(height * float(config.min_margin_y)))
    if min(left, right) < min_margin_x_px or min(top, bottom) < min_margin_y_px:
        return None

    x1, x2 = bx1 - left, bx2 + right
    y1, y2 = by1 - top, by2 + bottom
    plate_w, plate_h = x2 - x1, y2 - y1
    if plate_h / height > float(config.max_plate_height):
        return None
    if plate_w / max(plate_h, 1) < float(config.min_plate_aspect):
        return None

    ring_dark_parts = _ring_arrays(
        dark,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        bx1=bx1,
        by1=by1,
        bx2=bx2,
        by2=by2,
    )
    ring_luma_parts = _ring_arrays(
        luma,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        bx1=bx1,
        by1=by1,
        bx2=bx2,
        by2=by2,
    )
    if not ring_dark_parts or not ring_luma_parts:
        return None

    ring_dark_fraction = float(np.concatenate(ring_dark_parts).mean())
    if ring_dark_fraction < float(config.min_ring_dark_fraction):
        return None
    ring_luma_mean = float(np.concatenate(ring_luma_parts).mean())

    contrasts = _edge_contrasts(
        luma,
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        inside_mean=ring_luma_mean,
    )
    supported_contrasts = [value for value in contrasts if value >= float(config.min_edge_contrast)]
    if len(supported_contrasts) < int(config.min_contrast_sides):
        return None
    edge_contrast = min(1.0, sum(supported_contrasts) / len(supported_contrasts))

    margin_x = min(1.0, min(left, right) / max(box_w, 1))
    margin_y = min(1.0, min(top, bottom) / max(box_h, 1))
    geometry = min(1.0, (plate_w / max(plate_h, 1)) / 6.0)
    score = min(
        1.0,
        0.38 * ring_dark_fraction
        + 0.28 * float(sample.confidence)
        + 0.14 * min(1.0, margin_x * 2.0)
        + 0.10 * geometry
        + 0.10 * min(1.0, edge_contrast / max(float(config.min_edge_contrast), 1e-9)),
    )

    mask = rectangle_mask_polygon(
        sample.frame_index,
        x1=x1 / width,
        y1=y1 / height,
        x2=x2 / width,
        y2=y2 / height,
        confidence=score,
    )
    return CaptionPlateDetection(
        mask=mask,
        score=round(score, 4),
        ring_dark_fraction=round(ring_dark_fraction, 4),
        edge_contrast=round(edge_contrast, 4),
        margin_x=round(margin_x, 4),
        margin_y=round(margin_y, 4),
    )


def _mask_center_height(mask: PreciseMaskPolygon) -> tuple[float, float]:
    _, y1, _, y2 = mask.bbox
    return ((y1 + y2) * 0.5, y2 - y1)


def detect_opaque_caption_plate_masks(
    frames: Mapping[int, object],
    track: RemovalTrack,
    config: CaptionPlateConfig | None = None,
) -> tuple[PreciseMaskPolygon, ...]:
    """Return temporally supported plate masks for a confirmed subtitle track.

    The public API deliberately accepts only ``TargetKind.SUBTITLE``. This keeps
    stable product labels, logos and scene text out of the broad plate-removal
    path even if they happen to sit on dark rectangles.
    """
    if not isinstance(frames, Mapping):
        raise TypeError("frames must be a mapping of frame_index to frame")
    if not isinstance(track, RemovalTrack):
        raise TypeError("track must be a RemovalTrack")
    if track.kind is not TargetKind.SUBTITLE:
        raise ValueError("opaque caption plates are only valid for subtitle tracks")
    if config is None:
        config = CaptionPlateConfig()
    if not isinstance(config, CaptionPlateConfig):
        raise TypeError("config must be CaptionPlateConfig")

    inspected = 0
    detections: list[CaptionPlateDetection] = []
    for sample in track.samples:
        if sample.frame_index not in frames:
            continue
        inspected += 1
        result = detect_opaque_caption_plate(frames[sample.frame_index], sample, config)
        if result is not None:
            detections.append(result)

    required = max(
        int(config.min_support_frames),
        ceil(inspected * float(config.min_temporal_support)) if inspected else int(config.min_support_frames),
    )
    if inspected < int(config.min_support_frames) or len(detections) < required:
        return ()

    centers_heights = [_mask_center_height(item.mask) for item in detections]
    center_values = [item[0] for item in centers_heights]
    height_values = [item[1] for item in centers_heights]
    if max(center_values) - min(center_values) > float(config.max_center_y_drift):
        return ()
    if max(height_values) - min(height_values) > float(config.max_height_drift):
        return ()

    return tuple(item.mask for item in detections)

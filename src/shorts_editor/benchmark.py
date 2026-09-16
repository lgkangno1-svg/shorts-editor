from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import isfinite
from numbers import Integral, Real

from .qc import QCDecision, QCMetrics, evaluate_qc


@dataclass(frozen=True)
class PairedBenchmarkResult:
    """Objective quality result for overlay/candidate/clean paired frame stacks."""

    metrics: QCMetrics
    decision: QCDecision
    source_overlay_strength: float
    mask_coverage: float
    frame_count: int

    def __post_init__(self) -> None:
        if not isinstance(self.metrics, QCMetrics):
            raise TypeError("metrics must be QCMetrics")
        if not isinstance(self.decision, QCDecision):
            raise TypeError("decision must be QCDecision")
        for name in ("source_overlay_strength", "mask_coverage"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real number")
            if not isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if isinstance(self.frame_count, bool) or not isinstance(self.frame_count, Integral):
            raise TypeError("frame_count must be an integer")
        if int(self.frame_count) <= 0:
            raise ValueError("frame_count must be > 0")


def _numpy():
    try:
        return import_module("numpy")
    except ImportError as exc:
        raise RuntimeError("paired benchmark requires NumPy; install shorts-editor-cleanup[benchmark]") from exc


def _positive_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and > 0")
    return result


def _nonnegative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer")
    result = int(value)
    if result < 0:
        raise ValueError(f"{name} must be >= 0")
    return result


def _video_array(value: object, name: str):
    np = _numpy()
    array = np.asarray(value)
    if array.ndim != 4:
        raise ValueError(f"{name} must have shape [frames, height, width, channels]")
    if array.shape[0] <= 0 or array.shape[1] <= 0 or array.shape[2] <= 0 or array.shape[3] <= 0:
        raise ValueError(f"{name} dimensions must be non-empty")
    array = array.astype(np.float32, copy=False)
    if not bool(np.isfinite(array).all()):
        raise ValueError(f"{name} must contain only finite pixels")
    return array


def _mask_array(value: object, expected_shape: tuple[int, int, int]):
    np = _numpy()
    array = np.asarray(value)
    if array.shape != expected_shape:
        raise ValueError("removal_mask must have shape [frames, height, width] matching the videos")
    if array.dtype.kind in "fc" and not bool(np.isfinite(array).all()):
        raise ValueError("removal_mask must contain only finite values")
    if array.dtype.kind not in "bui f".replace(" ", ""):
        raise TypeError("removal_mask must contain boolean or numeric values")
    if not bool(np.logical_or(array == 0, array == 1).all()):
        raise ValueError("removal_mask must contain only binary 0/1 values")
    return array.astype(bool, copy=False)


def _dilate_mask(mask, radius: int):
    np = _numpy()
    if radius == 0:
        return mask.copy()
    frames, height, width = mask.shape
    padded = np.pad(mask, ((0, 0), (radius, radius), (radius, radius)), mode="constant", constant_values=False)
    output = np.zeros_like(mask, dtype=bool)
    size = 2 * radius + 1
    for dy in range(size):
        for dx in range(size):
            output |= padded[:, dy : dy + height, dx : dx + width]
    return output


def _score_distribution(values, pixel_range: float, *, percentile: float = 95.0) -> float:
    np = _numpy()
    if values.size == 0:
        return 0.0
    mean_value = float(np.mean(values)) / pixel_range
    tail_value = float(np.percentile(values, percentile)) / pixel_range
    return round(min(1.0, max(0.0, (0.65 * mean_value) + (0.35 * tail_value))), 4)


def evaluate_paired_video(
    overlay_frames: object,
    candidate_frames: object,
    clean_frames: object,
    removal_mask: object,
    *,
    pixel_range: float = 255.0,
    boundary_radius: int = 2,
    protected_margin: int = 2,
    min_overlay_strength: float = 0.01,
    qc_threshold: float = 0.72,
) -> PairedBenchmarkResult:
    """Score a removal candidate against clean reference frames."""
    np = _numpy()
    pixel_range = _positive_real(pixel_range, "pixel_range")
    boundary_radius = _nonnegative_int(boundary_radius, "boundary_radius")
    protected_margin = _nonnegative_int(protected_margin, "protected_margin")
    min_overlay_strength = _positive_real(min_overlay_strength, "min_overlay_strength")
    if min_overlay_strength > 1.0:
        raise ValueError("min_overlay_strength must be <= 1")

    overlay = _video_array(overlay_frames, "overlay_frames")
    candidate = _video_array(candidate_frames, "candidate_frames")
    clean = _video_array(clean_frames, "clean_frames")
    if overlay.shape != candidate.shape or overlay.shape != clean.shape:
        raise ValueError("overlay, candidate and clean videos must have identical shapes")

    frame_count, height, width, _channels = overlay.shape
    mask = _mask_array(removal_mask, (frame_count, height, width))
    if not bool(mask.any()):
        raise ValueError("removal_mask must contain at least one target pixel")

    overlay_error = np.mean(np.abs(overlay - clean), axis=-1)
    candidate_error = np.mean(np.abs(candidate - clean), axis=-1)
    source_inside = float(np.mean(overlay_error[mask])) / pixel_range
    if source_inside < min_overlay_strength:
        raise ValueError("paired fixture has insufficient overlay signal inside removal_mask")

    candidate_inside = float(np.mean(candidate_error[mask])) / pixel_range
    residual_score = round(min(1.0, max(0.0, candidate_inside / source_inside)), 4)
    expanded = _dilate_mask(mask, protected_margin)
    protected_damage_score = _score_distribution(candidate_error[~expanded], pixel_range)
    boundary_ring = _dilate_mask(mask, boundary_radius) & ~mask
    boundary_score = _score_distribution(candidate_error[boundary_ring], pixel_range, percentile=90.0)

    if frame_count < 2:
        flicker_score = 0.0
    else:
        temporal_error = np.mean(np.abs((candidate[1:] - candidate[:-1]) - (clean[1:] - clean[:-1])), axis=-1)
        temporal_mask = mask[1:] | mask[:-1]
        flicker_score = _score_distribution(temporal_error[temporal_mask], pixel_range, percentile=90.0)

    metrics = QCMetrics(residual_score, flicker_score, boundary_score, protected_damage_score)
    decision = evaluate_qc(metrics, threshold=qc_threshold)
    return PairedBenchmarkResult(metrics, decision, round(min(1.0, max(0.0, source_inside)), 4), round(float(np.mean(mask)), 6), frame_count)

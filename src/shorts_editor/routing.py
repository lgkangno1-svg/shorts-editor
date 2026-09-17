from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from numbers import Real


class Engine(str, Enum):
    LOCAL_FAST = "local_fast"
    LOCAL_TEMPORAL = "local_temporal"
    SMART_PRO = "smart_pro"


@dataclass(frozen=True)
class CleanupRequest:
    """Engine-neutral difficulty signals. Values are normalized to [0, 1]."""

    mask_area_ratio: float
    motion_score: float
    texture_score: float
    occlusion_score: float
    mask_confidence: float
    duration_seconds: float

    def __post_init__(self) -> None:
        for name in ("mask_area_ratio", "motion_score", "texture_score", "occlusion_score", "mask_confidence"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a real numeric signal")
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")
        if isinstance(self.duration_seconds, bool) or not isinstance(self.duration_seconds, Real):
            raise TypeError("duration_seconds must be a real numeric duration")
        if not math.isfinite(self.duration_seconds) or self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be finite and > 0")


@dataclass(frozen=True)
class RouteDecision:
    engine: Engine
    difficulty: float
    reason: str


def difficulty_score(request: CleanupRequest) -> float:
    """Conservative score used before expensive inference."""
    score = (
        0.22 * request.mask_area_ratio
        + 0.22 * request.motion_score
        + 0.20 * request.texture_score
        + 0.20 * request.occlusion_score
        + 0.16 * (1.0 - request.mask_confidence)
    )
    return round(min(1.0, max(0.0, score)), 4)


def route_cleanup(request: CleanupRequest) -> RouteDecision:
    score = difficulty_score(request)
    if request.mask_confidence < 0.45:
        return RouteDecision(Engine.SMART_PRO, score, "low mask confidence")

    # Frame-local cleanup is deliberately limited to short, simple clips.
    # On longer clips, even a small static mask can expose frame-to-frame
    # reconstruction drift that is more visible than the removed overlay.
    if score < 0.28 and request.mask_area_ratio < 0.12 and request.duration_seconds <= 30.0:
        return RouteDecision(Engine.LOCAL_FAST, score, "small, short, low-complexity removal")
    if score < 0.62:
        reason = "long clip requires temporal consistency" if request.duration_seconds > 30.0 else "temporal reconstruction required"
        return RouteDecision(Engine.LOCAL_TEMPORAL, score, reason)
    return RouteDecision(Engine.SMART_PRO, score, "high-complexity reconstruction")

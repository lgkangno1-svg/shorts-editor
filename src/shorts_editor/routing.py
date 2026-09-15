from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


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
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be > 0")


@dataclass(frozen=True)
class RouteDecision:
    engine: Engine
    difficulty: float
    reason: str


def difficulty_score(request: CleanupRequest) -> float:
    """Conservative score used before expensive inference.

    Low mask confidence increases difficulty because an inaccurate mask can
    damage protected content even when reconstruction itself is easy.
    """
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
    if score < 0.28 and request.mask_area_ratio < 0.12:
        return RouteDecision(Engine.LOCAL_FAST, score, "small, low-complexity removal")
    if score < 0.62:
        return RouteDecision(Engine.LOCAL_TEMPORAL, score, "temporal reconstruction required")
    return RouteDecision(Engine.SMART_PRO, score, "high-complexity reconstruction")

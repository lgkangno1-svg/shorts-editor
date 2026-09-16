"""Video cleanup core."""

from .local_vsr import VSRRunnerConfig, run_vsr_local
from .precision_masks import (
    PreciseMaskPolygon,
    dedupe_precise_masks,
    precise_masks_to_vsr_corrections,
    rectangle_mask_polygon,
)
from .routing import CleanupRequest, Engine, RouteDecision, route_cleanup
from .subtitles import (
    OCRDetection,
    SubtitleConsensusConfig,
    SubtitleTrackCandidate,
    best_subtitle_track,
    detect_subtitle_tracks,
    refine_subtitle_track,
)

__all__ = [
    "CleanupRequest",
    "Engine",
    "OCRDetection",
    "PreciseMaskPolygon",
    "RouteDecision",
    "SubtitleConsensusConfig",
    "SubtitleTrackCandidate",
    "VSRRunnerConfig",
    "best_subtitle_track",
    "dedupe_precise_masks",
    "detect_subtitle_tracks",
    "precise_masks_to_vsr_corrections",
    "rectangle_mask_polygon",
    "refine_subtitle_track",
    "route_cleanup",
    "run_vsr_local",
]

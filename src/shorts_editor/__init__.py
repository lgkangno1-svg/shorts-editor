"""Video cleanup core."""

from .benchmark import PairedBenchmarkResult, evaluate_paired_video
from .local_vsr import VSRRunnerConfig, run_vsr_local
from .ocr_adapters import (
    OCRFrameAdapterResult,
    adapt_rapidocr_output,
    create_rapidocr_engine,
    run_rapidocr_frame,
)
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
    "OCRFrameAdapterResult",
    "PairedBenchmarkResult",
    "PreciseMaskPolygon",
    "RouteDecision",
    "SubtitleConsensusConfig",
    "SubtitleTrackCandidate",
    "VSRRunnerConfig",
    "adapt_rapidocr_output",
    "best_subtitle_track",
    "create_rapidocr_engine",
    "dedupe_precise_masks",
    "detect_subtitle_tracks",
    "evaluate_paired_video",
    "precise_masks_to_vsr_corrections",
    "rectangle_mask_polygon",
    "refine_subtitle_track",
    "route_cleanup",
    "run_rapidocr_frame",
    "run_vsr_local",
]

"""Video cleanup core."""

from .benchmark import PairedBenchmarkResult, evaluate_paired_video
from .caption_plates import (
    CaptionPlateConfig,
    CaptionPlateDetection,
    detect_opaque_caption_plate,
    detect_opaque_caption_plate_masks,
)
from .local_vsr import (
    VSR_RUNNER_PROTOCOL,
    VSRRunnerCapabilities,
    VSRRunnerConfig,
    probe_vsr_runner,
    run_vsr_local,
)
from .media import DecodedFrame, MediaProbe, decode_frame_rgb, probe_media
from .opencv_bridge import create_builtin_opencv_runner_config
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
    "CaptionPlateConfig",
    "CaptionPlateDetection",
    "CleanupRequest",
    "DecodedFrame",
    "Engine",
    "MediaProbe",
    "OCRDetection",
    "OCRFrameAdapterResult",
    "PairedBenchmarkResult",
    "PreciseMaskPolygon",
    "RouteDecision",
    "SubtitleConsensusConfig",
    "SubtitleTrackCandidate",
    "VSR_RUNNER_PROTOCOL",
    "VSRRunnerCapabilities",
    "VSRRunnerConfig",
    "adapt_rapidocr_output",
    "best_subtitle_track",
    "create_builtin_opencv_runner_config",
    "create_rapidocr_engine",
    "decode_frame_rgb",
    "dedupe_precise_masks",
    "detect_opaque_caption_plate",
    "detect_opaque_caption_plate_masks",
    "detect_subtitle_tracks",
    "evaluate_paired_video",
    "precise_masks_to_vsr_corrections",
    "probe_media",
    "probe_vsr_runner",
    "rectangle_mask_polygon",
    "refine_subtitle_track",
    "route_cleanup",
    "run_rapidocr_frame",
    "run_vsr_local",
]

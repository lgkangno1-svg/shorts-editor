from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral

from .chunking import FrameChunk


@dataclass(frozen=True)
class ProcessingWindow:
    """A temporal inference window with a non-overlapping output region.

    `context` may overlap adjacent windows, but `emit` partitions the source
    chunk exactly once. This lets temporal engines see neighbouring frames
    without duplicating frames when outputs are concatenated.
    """

    context: FrameChunk
    emit: FrameChunk

    def __post_init__(self) -> None:
        if self.context.start > self.emit.start or self.context.end < self.emit.end:
            raise ValueError("context must fully contain emit region")


def plan_processing_windows(
    chunk: FrameChunk,
    max_frames: int,
    overlap_frames: int = 0,
) -> tuple[ProcessingWindow, ...]:
    """Split a shot-bounded chunk into inference windows with temporal context.

    Windows never extend outside `chunk`, so callers can first use scene-aware
    chunking and safely add overlap without leaking context across shot cuts.
    """
    if isinstance(max_frames, bool) or not isinstance(max_frames, Integral):
        raise TypeError("max_frames must be an integer frame count")
    if isinstance(overlap_frames, bool) or not isinstance(overlap_frames, Integral):
        raise TypeError("overlap_frames must be an integer frame count")
    max_frames = int(max_frames)
    overlap_frames = int(overlap_frames)
    if max_frames <= 0:
        raise ValueError("max_frames must be > 0")
    if overlap_frames < 0:
        raise ValueError("overlap_frames must be >= 0")
    if overlap_frames * 2 >= max_frames:
        raise ValueError("overlap must leave at least one non-context frame")

    emit_size = max_frames - (2 * overlap_frames)
    windows: list[ProcessingWindow] = []
    emit_start = chunk.start
    while emit_start < chunk.end:
        emit_end = min(emit_start + emit_size, chunk.end)
        context_start = max(chunk.start, emit_start - overlap_frames)
        context_end = min(chunk.end, emit_end + overlap_frames)
        windows.append(
            ProcessingWindow(
                context=FrameChunk(context_start, context_end),
                emit=FrameChunk(emit_start, emit_end),
            )
        )
        emit_start = emit_end
    return tuple(windows)

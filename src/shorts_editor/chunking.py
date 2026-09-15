from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FrameChunk:
    start: int
    end: int

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("chunk must satisfy 0 <= start < end")

    @property
    def length(self) -> int:
        return self.end - self.start


def plan_chunks(frame_count: int, max_frames: int, scene_cuts: tuple[int, ...] = ()) -> tuple[FrameChunk, ...]:
    """Create bounded chunks without crossing known scene cuts.

    Scene-cut indices are the first frame of a new shot. This prevents temporal
    reconstruction from borrowing pixels/context across unrelated shots.
    """
    if frame_count <= 0:
        raise ValueError("frame_count must be > 0")
    if max_frames <= 0:
        raise ValueError("max_frames must be > 0")

    cuts = tuple(sorted(set(scene_cuts)))
    if any(cut <= 0 or cut >= frame_count for cut in cuts):
        raise ValueError("scene cuts must be inside the video")

    boundaries = (0, *cuts, frame_count)
    chunks: list[FrameChunk] = []
    for shot_start, shot_end in zip(boundaries, boundaries[1:]):
        start = shot_start
        while start < shot_end:
            end = min(start + max_frames, shot_end)
            chunks.append(FrameChunk(start, end))
            start = end
    return tuple(chunks)

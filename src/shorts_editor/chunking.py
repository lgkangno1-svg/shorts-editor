from __future__ import annotations

from dataclasses import dataclass


def _require_frame_index(value: object, name: str, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer frame count")
    if positive and value <= 0:
        raise ValueError(f"{name} must be > 0")
    return value


@dataclass(frozen=True)
class FrameChunk:
    start: int
    end: int

    def __post_init__(self) -> None:
        _require_frame_index(self.start, "start")
        _require_frame_index(self.end, "end")
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
    _require_frame_index(frame_count, "frame_count", positive=True)
    _require_frame_index(max_frames, "max_frames", positive=True)

    for cut in scene_cuts:
        _require_frame_index(cut, "scene cut")
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

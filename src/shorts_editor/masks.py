from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x1: int
    y1: int
    x2: int
    y2: int

    def __post_init__(self) -> None:
        if min(self.x1, self.y1) < 0 or self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("box must satisfy non-negative x1/y1 and x2>x1, y2>y1")

    @property
    def area(self) -> int:
        return (self.x2 - self.x1) * (self.y2 - self.y1)


def expand_box(box: Box, padding: int, frame_width: int, frame_height: int) -> Box:
    """Pad a removal region while clipping it to the frame."""
    if padding < 0:
        raise ValueError("padding must be >= 0")
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be > 0")
    if box.x2 > frame_width or box.y2 > frame_height:
        raise ValueError("box must be inside the frame")

    return Box(
        max(0, box.x1 - padding),
        max(0, box.y1 - padding),
        min(frame_width, box.x2 + padding),
        min(frame_height, box.y2 + padding),
    )


def crop_savings(box: Box, frame_width: int, frame_height: int) -> float:
    """Fraction of pixels avoided when processing only this crop."""
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be > 0")
    if box.x2 > frame_width or box.y2 > frame_height:
        raise ValueError("box must be inside the frame")
    return 1.0 - (box.area / (frame_width * frame_height))

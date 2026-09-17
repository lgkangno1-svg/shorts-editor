from __future__ import annotations

from dataclasses import dataclass
from numbers import Integral


def _pixel_int(value: object, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise TypeError(f"{name} must be an integer pixel count")
    return int(value)


@dataclass(frozen=True)
class Box:
    x1: int
    y1: int
    x2: int
    y2: int

    def __post_init__(self) -> None:
        for name in ("x1", "y1", "x2", "y2"):
            object.__setattr__(self, name, _pixel_int(getattr(self, name), name="box coordinates"))
        if min(self.x1, self.y1) < 0 or self.x2 <= self.x1 or self.y2 <= self.y1:
            raise ValueError("box must satisfy non-negative x1/y1 and x2>x1, y2>y1")

    @property
    def area(self) -> int:
        return (self.x2 - self.x1) * (self.y2 - self.y1)


def expand_box(box: Box, padding: int, frame_width: int, frame_height: int) -> Box:
    """Pad a removal region while clipping it to the frame."""
    padding = _pixel_int(padding, name="padding")
    frame_width = _pixel_int(frame_width, name="frame dimensions")
    frame_height = _pixel_int(frame_height, name="frame dimensions")
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
    frame_width = _pixel_int(frame_width, name="frame dimensions")
    frame_height = _pixel_int(frame_height, name="frame dimensions")
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame dimensions must be > 0")
    if box.x2 > frame_width or box.y2 > frame_height:
        raise ValueError("box must be inside the frame")
    return 1.0 - (box.area / (frame_width * frame_height))

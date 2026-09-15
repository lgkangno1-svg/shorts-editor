from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TargetKind(str, Enum):
    SUBTITLE = "subtitle"
    TEXT = "text"
    WATERMARK = "watermark"
    LOGO = "logo"
    OBJECT = "object"
    PERSON = "person"


@dataclass(frozen=True)
class BoundingBox:
    """Normalized rectangle in [0, 1] coordinates."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("box values must be in [0, 1]")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("box width and height must be > 0")
        if self.x + self.width > 1.0 or self.y + self.height > 1.0:
            raise ValueError("box must fit inside the frame")

    @property
    def area_ratio(self) -> float:
        return self.width * self.height


@dataclass(frozen=True)
class TrackSample:
    frame_index: int
    box: BoundingBox
    confidence: float

    def __post_init__(self) -> None:
        if self.frame_index < 0:
            raise ValueError("frame_index must be >= 0")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class RemovalTrack:
    """Engine-neutral removal target shared by subtitles, watermarks and objects."""

    track_id: str
    kind: TargetKind
    samples: tuple[TrackSample, ...]

    def __post_init__(self) -> None:
        if not self.track_id.strip():
            raise ValueError("track_id must not be empty")
        if not self.samples:
            raise ValueError("track must contain at least one sample")
        indices = [sample.frame_index for sample in self.samples]
        if indices != sorted(indices) or len(indices) != len(set(indices)):
            raise ValueError("track samples must have unique ascending frame indices")

    @property
    def mean_confidence(self) -> float:
        return sum(sample.confidence for sample in self.samples) / len(self.samples)

    @property
    def max_area_ratio(self) -> float:
        return max(sample.box.area_ratio for sample in self.samples)

    @property
    def is_moving(self) -> bool:
        first = self.samples[0].box
        return any((sample.box.x, sample.box.y) != (first.x, first.y) for sample in self.samples[1:])

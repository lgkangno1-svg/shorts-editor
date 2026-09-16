from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import hypot


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

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2.0, self.y + self.height / 2.0)


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
    def min_confidence(self) -> float:
        return min(sample.confidence for sample in self.samples)

    @property
    def max_area_ratio(self) -> float:
        return max(sample.box.area_ratio for sample in self.samples)

    def max_center_jump(self) -> float:
        """Largest raw normalized displacement between sampled centers."""
        if len(self.samples) < 2:
            return 0.0
        return max(
            hypot(b.box.center[0] - a.box.center[0], b.box.center[1] - a.box.center[1])
            for a, b in zip(self.samples, self.samples[1:])
        )

    def max_center_velocity(self) -> float:
        """Largest normalized center displacement per frame."""
        if len(self.samples) < 2:
            return 0.0
        return max(
            hypot(b.box.center[0] - a.box.center[0], b.box.center[1] - a.box.center[1])
            / (b.frame_index - a.frame_index)
            for a, b in zip(self.samples, self.samples[1:])
        )

    def has_tracking_risk(
        self,
        *,
        min_confidence: float = 0.5,
        max_center_velocity: float = 0.25,
        max_center_jump: float | None = None,
    ) -> bool:
        """Return whether a track should fail closed before destructive removal.

        ``max_center_velocity`` is normalized center displacement per frame and is
        the preferred threshold. ``max_center_jump`` is retained as a deprecated
        compatibility alias so existing callers do not silently change behavior.
        Supplying both thresholds is rejected because their units/intent would be
        ambiguous at the call site.
        """
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be in [0, 1]")
        if max_center_jump is not None:
            if max_center_velocity != 0.25:
                raise ValueError("use only max_center_velocity; max_center_jump is a compatibility alias")
            max_center_velocity = max_center_jump
        if max_center_velocity < 0.0:
            raise ValueError("max_center_velocity must be >= 0")
        return self.min_confidence < min_confidence or self.max_center_velocity() > max_center_velocity

    @property
    def is_moving(self) -> bool:
        first = self.samples[0].box.center
        return any(sample.box.center != first for sample in self.samples[1:])

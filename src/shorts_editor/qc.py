from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class QCMetrics:
    residual_score: float
    flicker_score: float
    boundary_score: float
    protected_damage_score: float

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a real numeric metric")
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be finite and in [0, 1]")


@dataclass(frozen=True)
class QCDecision:
    passed: bool
    score: float
    reason: str

    def __post_init__(self) -> None:
        if type(self.passed) is not bool:
            raise ValueError("passed must be a boolean")
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)):
            raise ValueError("score must be a real number")
        if not math.isfinite(self.score) or not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be finite and in [0, 1]")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")


def evaluate_qc(metrics: QCMetrics, threshold: float = 0.72) -> QCDecision:
    """Fail closed: protected-region damage is weighted most heavily."""
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
        raise TypeError("threshold must be a real number")
    if not math.isfinite(threshold) or not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be finite and in [0, 1]")
    penalty = (
        0.30 * metrics.residual_score
        + 0.25 * metrics.flicker_score
        + 0.15 * metrics.boundary_score
        + 0.30 * metrics.protected_damage_score
    )
    score = round(1.0 - penalty, 4)
    if metrics.protected_damage_score > 0.30:
        return QCDecision(False, score, "protected-region damage")
    if metrics.residual_score > 0.45:
        return QCDecision(False, score, "visible removal residual")
    if score < threshold:
        return QCDecision(False, score, "aggregate quality below threshold")
    return QCDecision(True, score, "quality gate passed")

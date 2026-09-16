from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real



def _real_metric(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
    return result


@dataclass(frozen=True)
class QCMetrics:
    residual_score: float
    flicker_score: float
    boundary_score: float
    protected_damage_score: float

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            _real_metric(value, name)


@dataclass(frozen=True)
class QCDecision:
    passed: bool
    score: float
    reason: str

    def __post_init__(self) -> None:
        if type(self.passed) is not bool:
            raise ValueError("passed must be a boolean")
        _real_metric(self.score, "score")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("reason must be a non-empty string")


def evaluate_qc(metrics: QCMetrics, threshold: float = 0.72) -> QCDecision:
    """Fail closed: protected-region damage is weighted most heavily."""
    if not isinstance(metrics, QCMetrics):
        raise TypeError("metrics must be QCMetrics")
    threshold_value = _real_metric(threshold, "threshold")
    penalty = (
        0.30 * float(metrics.residual_score)
        + 0.25 * float(metrics.flicker_score)
        + 0.15 * float(metrics.boundary_score)
        + 0.30 * float(metrics.protected_damage_score)
    )
    score = round(1.0 - penalty, 4)
    if float(metrics.protected_damage_score) > 0.30:
        return QCDecision(False, score, "protected-region damage")
    if float(metrics.residual_score) > 0.45:
        return QCDecision(False, score, "visible removal residual")
    if score < threshold_value:
        return QCDecision(False, score, "aggregate quality below threshold")
    return QCDecision(True, score, "quality gate passed")

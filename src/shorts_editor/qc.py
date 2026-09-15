from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class QCMetrics:
    residual_score: float
    flicker_score: float
    boundary_score: float
    protected_damage_score: float

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


@dataclass(frozen=True)
class QCDecision:
    passed: bool
    score: float
    reason: str


def evaluate_qc(metrics: QCMetrics, threshold: float = 0.72) -> QCDecision:
    """Fail closed: protected-region damage is weighted most heavily."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
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

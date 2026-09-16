from __future__ import annotations

from dataclasses import dataclass

from .qc import QCDecision
from .routing import Engine


_ESCALATION_ORDER = (Engine.LOCAL_FAST, Engine.LOCAL_TEMPORAL, Engine.SMART_PRO)


@dataclass(frozen=True)
class EscalationDecision:
    retry: bool
    engine: Engine
    reason: str


def _require_engine(current: Engine) -> None:
    if not isinstance(current, Engine):
        raise TypeError("current must be an Engine")


def next_engine(current: Engine) -> Engine | None:
    """Return the next stronger engine, or None when no stronger engine exists."""
    _require_engine(current)
    index = _ESCALATION_ORDER.index(current)
    if index + 1 >= len(_ESCALATION_ORDER):
        return None
    return _ESCALATION_ORDER[index + 1]


def decide_escalation(current: Engine, qc: QCDecision) -> EscalationDecision:
    """Retry a failed render with a stronger engine; never loop at Smart Pro."""
    _require_engine(current)
    if not isinstance(qc, QCDecision):
        raise TypeError("qc must be a QCDecision")
    if qc.passed:
        return EscalationDecision(False, current, "quality gate passed")

    stronger = next_engine(current)
    if stronger is None:
        return EscalationDecision(False, current, f"manual review required: {qc.reason}")

    return EscalationDecision(True, stronger, f"QC failed: {qc.reason}")

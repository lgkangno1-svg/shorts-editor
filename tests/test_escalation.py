import pytest

from shorts_editor.escalation import decide_escalation, next_engine
from shorts_editor.qc import QCDecision
from shorts_editor.routing import Engine


def test_engine_order_is_bounded():
    assert next_engine(Engine.LOCAL_FAST) is Engine.LOCAL_TEMPORAL
    assert next_engine(Engine.LOCAL_TEMPORAL) is Engine.SMART_PRO
    assert next_engine(Engine.SMART_PRO) is None


def test_failed_fast_render_escalates():
    qc = QCDecision(False, 0.5, "visible removal residual")
    decision = decide_escalation(Engine.LOCAL_FAST, qc)
    assert decision.retry is True
    assert decision.engine is Engine.LOCAL_TEMPORAL


def test_failed_smart_pro_stops_for_review():
    qc = QCDecision(False, 0.5, "protected-region damage")
    decision = decide_escalation(Engine.SMART_PRO, qc)
    assert decision.retry is False
    assert decision.engine is Engine.SMART_PRO
    assert "manual review" in decision.reason


def test_passing_render_never_retries():
    qc = QCDecision(True, 0.9, "quality gate passed")
    decision = decide_escalation(Engine.LOCAL_FAST, qc)
    assert decision.retry is False
    assert decision.engine is Engine.LOCAL_FAST


@pytest.mark.parametrize("current", ["local_fast", None, True, 0])
def test_escalation_rejects_non_engine_inputs(current):
    with pytest.raises(TypeError):
        next_engine(current)


def test_decide_escalation_rejects_non_qc_decision():
    with pytest.raises(TypeError):
        decide_escalation(Engine.LOCAL_FAST, {"passed": False, "score": 0.5})

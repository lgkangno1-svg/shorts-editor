import pytest

from shorts_editor.qc import QCDecision, QCMetrics, evaluate_qc
from shorts_editor.routing import CleanupRequest, Engine, route_cleanup


def req(**overrides):
    values = dict(mask_area_ratio=0.05, motion_score=0.1, texture_score=0.1,
                  occlusion_score=0.05, mask_confidence=0.95, duration_seconds=10)
    values.update(overrides)
    return CleanupRequest(**values)


def test_easy_job_stays_local_fast():
    assert route_cleanup(req()).engine is Engine.LOCAL_FAST


def test_routing_accepts_numpy_real_scalars():
    np = pytest.importorskip("numpy")
    decision = route_cleanup(req(
        mask_area_ratio=np.float32(0.05),
        motion_score=np.float64(0.1),
        texture_score=np.float32(0.1),
        occlusion_score=np.float64(0.05),
        mask_confidence=np.float32(0.95),
        duration_seconds=np.float64(10.0),
    ))
    assert decision.engine is Engine.LOCAL_FAST


def test_long_easy_job_uses_temporal_engine():
    decision = route_cleanup(req(duration_seconds=90))
    assert decision.engine is Engine.LOCAL_TEMPORAL
    assert decision.reason == "long clip requires temporal consistency"


def test_motion_routes_to_temporal():
    decision = route_cleanup(req(mask_area_ratio=0.15, motion_score=0.7, texture_score=0.5))
    assert decision.engine is Engine.LOCAL_TEMPORAL


def test_uncertain_mask_escalates():
    assert route_cleanup(req(mask_confidence=0.2)).engine is Engine.SMART_PRO


def test_invalid_signal_rejected():
    with pytest.raises(ValueError):
        req(motion_score=1.1)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_routing_rejects_non_finite_normalized_signals(value):
    with pytest.raises(ValueError):
        req(motion_score=value)


@pytest.mark.parametrize("value", [True, False, "0.5", None])
def test_routing_rejects_boolean_or_nonnumeric_normalized_signals(value):
    with pytest.raises(TypeError):
        req(motion_score=value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_routing_rejects_non_finite_duration(value):
    with pytest.raises(ValueError):
        req(duration_seconds=value)


@pytest.mark.parametrize("value", [True, False, "10", None])
def test_routing_rejects_boolean_or_nonnumeric_duration(value):
    with pytest.raises(TypeError):
        req(duration_seconds=value)


def test_qc_passes_clean_result():
    result = evaluate_qc(QCMetrics(0.05, 0.05, 0.05, 0.01))
    assert result.passed


def test_qc_accepts_numpy_real_scalars():
    np = pytest.importorskip("numpy")
    metrics = QCMetrics(np.float32(0.05), np.float64(0.05), np.float32(0.05), np.float64(0.01))
    result = evaluate_qc(metrics, threshold=np.float32(0.72))
    assert result.passed


def test_qc_fails_protected_damage_even_if_other_metrics_are_good():
    result = evaluate_qc(QCMetrics(0.01, 0.01, 0.01, 0.31))
    assert not result.passed
    assert result.reason == "protected-region damage"


def test_qc_fails_large_residual():
    result = evaluate_qc(QCMetrics(0.46, 0.01, 0.01, 0.01))
    assert not result.passed


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_qc_rejects_non_finite_metrics(value):
    with pytest.raises(ValueError):
        QCMetrics(value, 0.01, 0.01, 0.01)


@pytest.mark.parametrize("value", [True, False, "0.1", None])
def test_qc_rejects_boolean_or_nonnumeric_metrics(value):
    with pytest.raises(TypeError):
        QCMetrics(value, 0.01, 0.01, 0.01)


def test_qc_rejects_non_finite_threshold():
    with pytest.raises(ValueError):
        evaluate_qc(QCMetrics(0.01, 0.01, 0.01, 0.01), threshold=float("nan"))


@pytest.mark.parametrize("value", [True, False, "0.72", None])
def test_qc_rejects_boolean_or_nonnumeric_threshold(value):
    with pytest.raises(TypeError):
        evaluate_qc(QCMetrics(0.01, 0.01, 0.01, 0.01), threshold=value)


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -0.1, 1.1, True])
def test_qc_decision_rejects_invalid_score(value):
    with pytest.raises((TypeError, ValueError)):
        QCDecision(False, value, "invalid render")


@pytest.mark.parametrize("value", [0, 1, "yes", None])
def test_qc_decision_requires_boolean_passed(value):
    with pytest.raises(ValueError):
        QCDecision(value, 0.5, "invalid render")


@pytest.mark.parametrize("value", ["", "   ", None])
def test_qc_decision_requires_reason(value):
    with pytest.raises(ValueError):
        QCDecision(False, 0.5, value)

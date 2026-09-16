import pytest

from shorts_editor.tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


def sample(frame: int, x: float = 0.1, confidence: float = 0.9) -> TrackSample:
    return TrackSample(frame, BoundingBox(x, 0.1, 0.1, 0.1), confidence)


def test_static_watermark_track():
    track = RemovalTrack("wm-1", TargetKind.WATERMARK, (sample(0), sample(1)))
    assert not track.is_moving
    assert track.mean_confidence == pytest.approx(0.9)
    assert track.min_confidence == pytest.approx(0.9)
    assert track.max_area_ratio == pytest.approx(0.01)
    assert track.max_center_jump() == pytest.approx(0.0)
    assert track.max_center_velocity() == pytest.approx(0.0)
    assert not track.has_tracking_risk()


def test_moving_watermark_track():
    track = RemovalTrack("wm-2", TargetKind.WATERMARK, (sample(0), sample(1, x=0.2)))
    assert track.is_moving
    assert track.max_center_jump() == pytest.approx(0.1)
    assert track.max_center_velocity() == pytest.approx(0.1)
    assert not track.has_tracking_risk()


def test_tracking_risk_flags_confidence_collapse_and_large_velocity():
    low_conf = RemovalTrack(
        "wm-low", TargetKind.WATERMARK, (sample(0), sample(1, confidence=0.2))
    )
    jump = RemovalTrack("wm-jump", TargetKind.WATERMARK, (sample(0), sample(1, x=0.5)))
    assert low_conf.has_tracking_risk()
    assert jump.has_tracking_risk(max_center_velocity=0.25)


def test_sparse_samples_use_per_frame_motion_for_risk():
    track = RemovalTrack("sparse", TargetKind.OBJECT, (sample(0), sample(10, x=0.5)))
    assert track.max_center_jump() == pytest.approx(0.4)
    assert track.max_center_velocity() == pytest.approx(0.04)
    assert not track.has_tracking_risk(max_center_velocity=0.25)


def test_legacy_jump_keyword_keeps_velocity_semantics():
    track = RemovalTrack("legacy", TargetKind.OBJECT, (sample(0), sample(10, x=0.5)))
    assert not track.has_tracking_risk(max_center_jump=0.25)


def test_tracking_risk_thresholds_are_validated():
    track = RemovalTrack("wm-1", TargetKind.WATERMARK, (sample(0),))
    with pytest.raises(ValueError):
        track.has_tracking_risk(min_confidence=1.1)
    with pytest.raises(ValueError):
        track.has_tracking_risk(max_center_velocity=-0.1)
    with pytest.raises(ValueError):
        track.has_tracking_risk(max_center_velocity=0.2, max_center_jump=0.2)
    with pytest.raises(ValueError):
        track.has_tracking_risk(min_confidence=float("nan"))
    with pytest.raises(ValueError):
        track.has_tracking_risk(max_center_velocity=float("inf"))


def test_box_rejects_out_of_frame_region():
    with pytest.raises(ValueError):
        BoundingBox(0.95, 0.1, 0.1, 0.1)


def test_tracking_inputs_reject_non_finite_values():
    for value in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            BoundingBox(value, 0.1, 0.1, 0.1)
        with pytest.raises(ValueError):
            BoundingBox(0.1, 0.1, value, 0.1)
        with pytest.raises(ValueError):
            TrackSample(0, BoundingBox(0.1, 0.1, 0.1, 0.1), value)


def test_track_rejects_duplicate_or_unsorted_frames():
    with pytest.raises(ValueError):
        RemovalTrack("bad", TargetKind.LOGO, (sample(1), sample(1)))
    with pytest.raises(ValueError):
        RemovalTrack("bad", TargetKind.LOGO, (sample(2), sample(1)))

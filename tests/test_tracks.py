import pytest

from shorts_editor.tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


def sample(frame: int, x: float = 0.1, confidence: float = 0.9) -> TrackSample:
    return TrackSample(frame, BoundingBox(x, 0.1, 0.1, 0.1), confidence)


def test_static_watermark_track():
    track = RemovalTrack("wm-1", TargetKind.WATERMARK, (sample(0), sample(1)))
    assert not track.is_moving
    assert track.mean_confidence == pytest.approx(0.9)
    assert track.max_area_ratio == pytest.approx(0.01)


def test_moving_watermark_track():
    track = RemovalTrack("wm-2", TargetKind.WATERMARK, (sample(0), sample(1, x=0.2)))
    assert track.is_moving


def test_box_rejects_out_of_frame_region():
    with pytest.raises(ValueError):
        BoundingBox(0.95, 0.1, 0.1, 0.1)


def test_track_rejects_duplicate_or_unsorted_frames():
    with pytest.raises(ValueError):
        RemovalTrack("bad", TargetKind.LOGO, (sample(1), sample(1)))
    with pytest.raises(ValueError):
        RemovalTrack("bad", TargetKind.LOGO, (sample(2), sample(1)))

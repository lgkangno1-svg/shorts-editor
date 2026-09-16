import math
import pytest

from shorts_editor.subtitles import (
    OCRDetection,
    SubtitleConsensusConfig,
    best_subtitle_track,
    densify_track,
    detect_subtitle_tracks,
    refine_subtitle_track,
    temporal_union_track,
)
from shorts_editor.tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


def det(frame, x, y, w, h, confidence=0.9, text="hello"):
    return OCRDetection(frame, BoundingBox(x, y, w, h), confidence, text)


def test_temporal_consensus_prefers_centered_changing_subtitle_over_corner_label():
    detections = []
    for frame, text in [(0, "hello"), (5, "world"), (10, "again"), (15, "bye")]:
        detections.append(det(frame, 0.22, 0.79, 0.56, 0.07, 0.92, text))
        detections.append(det(frame, 0.83, 0.73, 0.12, 0.05, 0.96, "SALE"))
    best = best_subtitle_track(detections)
    assert best is not None
    assert best.track.samples[0].box.width > 0.5
    assert best.text_change_ratio == 1.0


def test_word_boxes_and_two_lines_fuse_into_one_caption_block():
    detections = [
        det(0, 0.25, 0.78, 0.18, 0.035, text="one"),
        det(0, 0.45, 0.78, 0.20, 0.035, text="two"),
        det(0, 0.30, 0.825, 0.40, 0.035, text="line two"),
        det(6, 0.24, 0.78, 0.42, 0.035, text="next"),
        det(6, 0.31, 0.825, 0.38, 0.035, text="caption"),
    ]
    best = best_subtitle_track(detections)
    assert best is not None
    box = best.track.samples[0].box
    assert box.y < 0.78
    assert box.height > 0.08
    assert box.width > 0.44


def test_persistent_same_text_subtitle_is_still_accepted():
    detections = [
        det(0, 0.20, 0.80, 0.60, 0.06, text="same caption"),
        det(5, 0.20, 0.80, 0.60, 0.06, text="same caption"),
        det(10, 0.20, 0.80, 0.60, 0.06, text="same caption"),
    ]
    best = best_subtitle_track(detections)
    assert best is not None
    assert best.text_change_ratio == 0.0


def test_single_frame_scene_text_is_rejected_by_support_gate():
    detections = [det(0, 0.25, 0.7, 0.5, 0.08, text="sign")]
    assert detect_subtitle_tracks(detections) == ()


def test_config_can_support_upper_captions_without_bottom_strip_assumption():
    detections = [
        det(0, 0.20, 0.20, 0.60, 0.06, text="a"),
        det(5, 0.20, 0.20, 0.60, 0.06, text="b"),
    ]
    assert best_subtitle_track(detections) is None
    cfg = SubtitleConsensusConfig(min_center_y=0.1)
    assert best_subtitle_track(detections, cfg) is not None


def test_densify_fills_only_short_gaps():
    track = RemovalTrack(
        "s",
        TargetKind.SUBTITLE,
        (
            TrackSample(0, BoundingBox(0.2, 0.8, 0.5, 0.05), 0.9),
            TrackSample(3, BoundingBox(0.22, 0.8, 0.5, 0.05), 0.8),
            TrackSample(10, BoundingBox(0.3, 0.8, 0.5, 0.05), 0.9),
        ),
    )
    dense = densify_track(track, max_gap_frames=2)
    assert [s.frame_index for s in dense.samples] == [0, 1, 2, 3, 10]
    assert dense.samples[1].confidence < 0.8


def test_temporal_union_expands_neighbour_jitter_but_stays_in_frame():
    track = RemovalTrack(
        "s",
        TargetKind.SUBTITLE,
        (
            TrackSample(0, BoundingBox(0.01, 0.8, 0.4, 0.05), 0.9),
            TrackSample(1, BoundingBox(0.03, 0.79, 0.45, 0.06), 0.9),
        ),
    )
    refined = temporal_union_track(track, radius_frames=1, padding_x=0.02, padding_y=0.01)
    assert refined.samples[0].box.x == 0.0
    assert refined.samples[0].box.width >= 0.49
    assert refined.samples[0].box.y >= 0.0
    assert refined.samples[0].box.y + refined.samples[0].box.height <= 1.0


def test_refine_densifies_then_unions_to_prevent_mask_flicker():
    track = RemovalTrack(
        "s",
        TargetKind.SUBTITLE,
        (
            TrackSample(0, BoundingBox(0.2, 0.8, 0.4, 0.05), 0.9),
            TrackSample(2, BoundingBox(0.25, 0.79, 0.5, 0.06), 0.9),
        ),
    )
    refined = refine_subtitle_track(track, max_gap_frames=2, union_radius_frames=1, padding_x=0.0, padding_y=0.0)
    assert [s.frame_index for s in refined.samples] == [0, 1, 2]
    assert refined.samples[1].box.x <= 0.2
    assert refined.samples[1].box.x + refined.samples[1].box.width >= 0.75


@pytest.mark.parametrize("value", [True, 1.2, "3"])
def test_frame_index_type_safety(value):
    with pytest.raises((TypeError, ValueError)):
        OCRDetection(value, BoundingBox(0.2, 0.8, 0.4, 0.05), 0.9)


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_confidence_non_finite_is_rejected(value):
    with pytest.raises(ValueError):
        OCRDetection(0, BoundingBox(0.2, 0.8, 0.4, 0.05), value)

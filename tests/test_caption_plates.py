import numpy as np
import pytest

from shorts_editor.caption_plates import (
    CaptionPlateConfig,
    detect_opaque_caption_plate,
    detect_opaque_caption_plate_masks,
)
from shorts_editor.tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


HEIGHT = 200
WIDTH = 120


def sample(frame_index=0, confidence=0.92):
    return TrackSample(
        frame_index,
        BoundingBox(35 / WIDTH, 148 / HEIGHT, 50 / WIDTH, 14 / HEIGHT),
        confidence,
    )


def frame_with_plate(*, plate_value=20, background_value=180):
    frame = np.full((HEIGHT, WIDTH, 3), background_value, dtype=np.uint8)
    frame[140:170, 10:110] = plate_value
    # Deliberately make the entire OCR glyph box bright. Detection must rely on
    # the surrounding plate margins rather than dark pixels inside the text.
    frame[148:162, 35:85] = 240
    return frame


def test_detects_opaque_plate_around_bright_caption_text():
    result = detect_opaque_caption_plate(frame_with_plate(), sample())

    assert result is not None
    x1, y1, x2, y2 = result.mask.bbox
    assert x1 == pytest.approx(10 / WIDTH, abs=1 / WIDTH)
    assert y1 == pytest.approx(140 / HEIGHT, abs=1 / HEIGHT)
    assert x2 == pytest.approx(110 / WIDTH, abs=1 / WIDTH)
    assert y2 == pytest.approx(170 / HEIGHT, abs=1 / HEIGHT)
    assert result.ring_dark_fraction > 0.95
    assert result.edge_contrast > 0.4


def test_rejects_naturally_dark_scene_without_plate_boundary_contrast():
    frame = np.full((HEIGHT, WIDTH, 3), 20, dtype=np.uint8)
    frame[148:162, 35:85] = 240

    assert detect_opaque_caption_plate(frame, sample()) is None


def test_temporal_plate_masks_require_repeated_support():
    track = RemovalTrack(
        "subtitle-main",
        TargetKind.SUBTITLE,
        (sample(0), sample(5), sample(10)),
    )
    frames = {
        0: frame_with_plate(),
        5: frame_with_plate(),
        10: np.full((HEIGHT, WIDTH, 3), 180, dtype=np.uint8),
    }

    masks = detect_opaque_caption_plate_masks(frames, track)

    assert [mask.frame_index for mask in masks] == [0, 5]


def test_temporal_plate_masks_fail_closed_on_single_frame_hit():
    track = RemovalTrack(
        "subtitle-main",
        TargetKind.SUBTITLE,
        (sample(0), sample(5)),
    )
    frames = {
        0: frame_with_plate(),
        5: np.full((HEIGHT, WIDTH, 3), 180, dtype=np.uint8),
    }

    assert detect_opaque_caption_plate_masks(frames, track) == ()


def test_broad_plate_path_rejects_product_or_scene_text_tracks():
    track = RemovalTrack(
        "product-label",
        TargetKind.TEXT,
        (sample(0), sample(5)),
    )

    with pytest.raises(ValueError, match="only valid for subtitle tracks"):
        detect_opaque_caption_plate_masks({0: frame_with_plate(), 5: frame_with_plate()}, track)


def test_temporal_geometry_drift_is_rejected():
    first = sample(0)
    shifted = TrackSample(
        5,
        BoundingBox(35 / WIDTH, 90 / HEIGHT, 50 / WIDTH, 14 / HEIGHT),
        0.92,
    )
    track = RemovalTrack("subtitle-main", TargetKind.SUBTITLE, (first, shifted))
    frame_a = frame_with_plate()
    frame_b = np.full((HEIGHT, WIDTH, 3), 180, dtype=np.uint8)
    frame_b[82:112, 10:110] = 20
    frame_b[90:104, 35:85] = 240

    assert detect_opaque_caption_plate_masks({0: frame_a, 5: frame_b}, track) == ()


def test_nonfinite_float_frame_is_rejected_before_mask_generation():
    frame = frame_with_plate().astype(np.float32) / 255.0
    frame[0, 0, 0] = np.nan

    with pytest.raises(ValueError, match="finite"):
        detect_opaque_caption_plate(frame, sample())


def test_config_rejects_weak_ring_gate_below_edge_gate():
    with pytest.raises(ValueError, match="min_ring_dark_fraction"):
        CaptionPlateConfig(edge_dark_fraction=0.8, min_ring_dark_fraction=0.7)

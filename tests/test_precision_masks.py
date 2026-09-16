import pytest

from shorts_editor.precision_masks import (
    PreciseMaskPolygon,
    dedupe_precise_masks,
    precise_masks_to_vsr_corrections,
    rectangle_mask_polygon,
)


def test_rectangle_polygon_has_expected_area():
    mask = rectangle_mask_polygon(5, x1=0.1, y1=0.2, x2=0.2, y2=0.25, confidence=0.9)
    assert mask.area_ratio == pytest.approx(0.005)


def test_duplicate_glyph_boxes_are_suppressed_per_frame():
    strong = rectangle_mask_polygon(5, x1=0.1, y1=0.2, x2=0.2, y2=0.25, confidence=0.95)
    weak = rectangle_mask_polygon(5, x1=0.101, y1=0.201, x2=0.201, y2=0.251, confidence=0.6)
    kept = dedupe_precise_masks([weak, strong], iou_threshold=0.8)
    assert kept == (strong,)


def test_same_shape_on_different_frames_is_not_deduped():
    first = rectangle_mask_polygon(5, x1=0.1, y1=0.2, x2=0.2, y2=0.25)
    second = rectangle_mask_polygon(6, x1=0.1, y1=0.2, x2=0.2, y2=0.25)
    assert len(dedupe_precise_masks([first, second])) == 2


def test_vsr_corrections_are_frame_bounded_and_pixel_clipped():
    mask = PreciseMaskPolygon(30, ((0.0, 0.5), (1.0, 0.5), (1.0, 0.6), (0.0, 0.6)), 0.9)
    corrections = precise_masks_to_vsr_corrections([mask], frame_width=720, frame_height=1280, fps=30)
    assert corrections == [{
        "polygons": [[0, 640, 719, 640, 719, 767, 0, 767]],
        "start": 1.0,
        "end": 1.033333,
    }]


def test_low_confidence_masks_are_not_destructive():
    mask = rectangle_mask_polygon(0, x1=0.1, y1=0.2, x2=0.2, y2=0.25, confidence=0.1)
    assert precise_masks_to_vsr_corrections([mask], frame_width=100, frame_height=100, fps=25) == []


def test_invalid_polygon_rejected_fail_closed():
    with pytest.raises(ValueError):
        PreciseMaskPolygon(0, ((0.1, 0.1), (0.2, 0.2), (0.3, 0.3)))
    with pytest.raises(TypeError):
        PreciseMaskPolygon(True, ((0.1, 0.1), (0.2, 0.1), (0.2, 0.2)))

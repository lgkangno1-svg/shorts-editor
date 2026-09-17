import numpy as np
import pytest

from shorts_editor.masks import Box, crop_savings, expand_box


def test_expand_box_clips_to_frame():
    assert expand_box(Box(2, 3, 10, 12), 5, 100, 80) == Box(0, 0, 15, 17)


def test_expand_box_rejects_out_of_frame_input():
    with pytest.raises(ValueError):
        expand_box(Box(2, 3, 101, 12), 2, 100, 80)


def test_crop_savings_for_small_corner_region():
    box = Box(0, 0, 100, 100)
    assert crop_savings(box, 1000, 1000) == pytest.approx(0.99)


def test_negative_padding_fails_closed():
    with pytest.raises(ValueError):
        expand_box(Box(1, 1, 5, 5), -1, 10, 10)


def test_pixel_geometry_accepts_numpy_integral_values():
    box = Box(np.int32(1), np.int64(2), np.int32(5), np.int64(7))
    assert box == Box(1, 2, 5, 7)
    assert all(type(value) is int for value in (box.x1, box.y1, box.x2, box.y2))
    assert expand_box(box, np.int32(1), np.int64(10), np.int32(10)) == Box(0, 1, 6, 8)
    assert crop_savings(box, np.int64(10), np.int32(10)) == pytest.approx(0.8)


def test_pixel_geometry_rejects_fractional_and_boolean_values():
    with pytest.raises(TypeError):
        Box(0.5, 1, 5, 5)
    with pytest.raises(TypeError):
        Box(False, 1, 5, 5)
    with pytest.raises(TypeError):
        expand_box(Box(1, 1, 5, 5), 0.5, 10, 10)
    with pytest.raises(TypeError):
        expand_box(Box(1, 1, 5, 5), 1, 10.5, 10)
    with pytest.raises(TypeError):
        crop_savings(Box(1, 1, 5, 5), True, 10)

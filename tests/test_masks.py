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

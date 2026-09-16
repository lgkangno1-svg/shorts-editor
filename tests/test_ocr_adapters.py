from dataclasses import dataclass

import pytest

from shorts_editor.ocr_adapters import (
    adapt_rapidocr_output,
    run_rapidocr_frame,
)


@dataclass
class FakeRapidOutput:
    boxes: object
    txts: object
    scores: object
    word_results: object = None


def test_rapidocr_line_boxes_become_tracking_detections_and_words_become_masks():
    result = FakeRapidOutput(
        boxes=[[[10, 30], [90, 30], [90, 40], [10, 40]]],
        txts=("안녕하세요",),
        scores=(0.90,),
        word_results=((
            ("안녕", 0.95, [[10, 30], [35, 30], [35, 40], [10, 40]]),
            ("하세요", 0.91, [[40, 30], [90, 30], [90, 40], [40, 40]]),
        ),),
    )

    adapted = adapt_rapidocr_output(
        result,
        frame_index=7,
        frame_width=100,
        frame_height=50,
    )

    assert len(adapted.detections) == 1
    assert adapted.detections[0].text == "안녕하세요"
    assert adapted.detections[0].frame_index == 7
    assert adapted.detections[0].confidence == pytest.approx(0.90)
    assert len(adapted.precise_masks) == 2
    assert all(mask.frame_index == 7 for mask in adapted.precise_masks)
    assert max(mask.area_ratio for mask in adapted.precise_masks) < adapted.detections[0].box.area_ratio


def test_missing_word_geometry_does_not_create_destructive_masks_by_default():
    result = FakeRapidOutput(
        boxes=[[[10, 30], [90, 30], [90, 40], [10, 40]]],
        txts=("subtitle",),
        scores=(0.90,),
        word_results=(None,),
    )

    adapted = adapt_rapidocr_output(
        result,
        frame_index=0,
        frame_width=100,
        frame_height=50,
    )

    assert len(adapted.detections) == 1
    assert adapted.precise_masks == ()


def test_line_mask_fallback_requires_explicit_opt_in():
    result = FakeRapidOutput(
        boxes=[[[10, 30], [90, 30], [90, 40], [10, 40]]],
        txts=("subtitle",),
        scores=(0.90,),
        word_results=(),
    )

    adapted = adapt_rapidocr_output(
        result,
        frame_index=0,
        frame_width=100,
        frame_height=50,
        allow_line_masks=True,
    )

    assert len(adapted.precise_masks) == 1


def test_low_confidence_words_are_not_destructive():
    result = FakeRapidOutput(
        boxes=[[[10, 30], [90, 30], [90, 40], [10, 40]]],
        txts=("subtitle",),
        scores=(0.90,),
        word_results=((
            ("weak", 0.20, [[10, 30], [35, 30], [35, 40], [10, 40]]),
        ),),
    )

    adapted = adapt_rapidocr_output(
        result,
        frame_index=0,
        frame_width=100,
        frame_height=50,
        min_mask_confidence=0.45,
    )

    assert len(adapted.detections) == 1
    assert adapted.precise_masks == ()


def test_malformed_line_result_fails_closed_on_parallel_array_mismatch():
    result = FakeRapidOutput(
        boxes=[[[10, 30], [90, 30], [90, 40], [10, 40]]],
        txts=(),
        scores=(0.90,),
    )

    with pytest.raises(ValueError, match="matching lengths"):
        adapt_rapidocr_output(
            result,
            frame_index=0,
            frame_width=100,
            frame_height=50,
        )


def test_mapping_output_is_supported():
    result = {
        "boxes": [[[0, 0], [9, 0], [9, 9], [0, 9]]],
        "txts": ("x",),
        "scores": (0.8,),
        "word_results": ((("x", 0.8, [[0, 0], [9, 0], [9, 9], [0, 9]]),),),
    }

    adapted = adapt_rapidocr_output(
        result,
        frame_index=3,
        frame_width=10,
        frame_height=10,
    )

    assert adapted.detections[0].box.x == pytest.approx(0.0)
    assert adapted.detections[0].box.y == pytest.approx(0.0)
    assert adapted.detections[0].box.width == pytest.approx(1.0)
    assert adapted.detections[0].box.height == pytest.approx(1.0)
    assert adapted.precise_masks[0].area_ratio == pytest.approx(1.0)


def test_invalid_optional_word_polygon_is_ignored_without_falling_back_to_line_mask():
    result = FakeRapidOutput(
        boxes=[[[10, 30], [90, 30], [90, 40], [10, 40]]],
        txts=("subtitle",),
        scores=(0.90,),
        word_results=((
            ("bad", 0.99, [[1, 1], [1, 1], [1, 1], [1, 1]]),
        ),),
    )

    adapted = adapt_rapidocr_output(
        result,
        frame_index=0,
        frame_width=100,
        frame_height=50,
    )

    assert len(adapted.detections) == 1
    assert adapted.precise_masks == ()


def test_run_rapidocr_frame_requests_word_boxes_and_infers_frame_shape():
    result = FakeRapidOutput(
        boxes=[[[10, 30], [90, 30], [90, 40], [10, 40]]],
        txts=("subtitle",),
        scores=(0.90,),
        word_results=((
            ("subtitle", 0.90, [[10, 30], [90, 30], [90, 40], [10, 40]]),
        ),),
    )

    class Frame:
        shape = (50, 100, 3)

    class Engine:
        def __init__(self):
            self.calls = []

        def __call__(self, frame, **kwargs):
            self.calls.append((frame, kwargs))
            return result

    engine = Engine()
    frame = Frame()
    adapted = run_rapidocr_frame(engine, frame, frame_index=12)

    assert engine.calls == [(frame, {"return_word_box": True})]
    assert adapted.detections[0].frame_index == 12
    assert len(adapted.precise_masks) == 1


def test_adapter_rejects_invalid_dimensions_and_thresholds():
    result = FakeRapidOutput((), (), ())
    with pytest.raises(ValueError):
        adapt_rapidocr_output(result, frame_index=0, frame_width=1, frame_height=50)
    with pytest.raises(ValueError):
        adapt_rapidocr_output(result, frame_index=0, frame_width=100, frame_height=50, min_mask_confidence=1.1)

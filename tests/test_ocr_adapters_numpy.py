import numpy as np

from shorts_editor.ocr_adapters import adapt_rapidocr_output


def test_numpy_float32_boxes_and_scores_match_rapidocr_output_types():
    result = {
        "boxes": np.array([[[10, 30], [90, 30], [90, 40], [10, 40]]], dtype=np.float32),
        "txts": ("한글 자막",),
        "scores": (np.float32(0.91),),
        "word_results": ((
            (
                "한글",
                np.float32(0.94),
                np.array([[10, 30], [42, 30], [42, 40], [10, 40]], dtype=np.float32),
            ),
        ),),
    }

    adapted = adapt_rapidocr_output(
        result,
        frame_index=8,
        frame_width=100,
        frame_height=50,
    )

    assert len(adapted.detections) == 1
    assert adapted.detections[0].text == "한글 자막"
    assert len(adapted.precise_masks) == 1
    assert adapted.precise_masks[0].confidence > 0.9

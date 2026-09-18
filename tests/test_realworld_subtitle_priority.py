from shorts_editor.subtitles import OCRDetection, best_subtitle_track
from shorts_editor.tracks import BoundingBox


def det(frame, x, y, w, h, confidence=0.9, text=""):
    return OCRDetection(frame, BoundingBox(x, y, w, h), confidence, text)


def test_changing_bottom_subtitle_beats_static_centered_product_label():
    """Regression derived from a private real-world vertical shopping clip.

    The source fixture contains changing burned-in captions plus readable text on
    product packaging. The private clip itself is deliberately not committed.
    Subtitle selection should prefer the screen-overlay caption track instead of
    persistent scene/product text when both are repeatedly detected.
    """
    detections = []
    for frame, caption in [
        (0, "caption one"),
        (5, "caption two"),
        (10, "caption three"),
        (15, "caption four"),
        (20, "caption five"),
    ]:
        detections.append(det(frame, 0.24, 0.84, 0.52, 0.05, 0.90, caption))
        detections.append(det(frame, 0.18, 0.53, 0.64, 0.10, 0.97, "PRODUCT LABEL"))

    best = best_subtitle_track(detections)

    assert best is not None
    assert best.text_change_ratio == 1.0
    assert best.track.samples[0].box.center[1] > 0.80

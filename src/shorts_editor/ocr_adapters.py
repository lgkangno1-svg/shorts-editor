from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from math import isfinite
from numbers import Real
from typing import Mapping

from .precision_masks import PreciseMaskPolygon, dedupe_precise_masks
from .subtitles import OCRDetection
from .tracks import BoundingBox


@dataclass(frozen=True)
class OCRFrameAdapterResult:
    """Normalized OCR observations plus safe, fine-grained removal masks."""

    detections: tuple[OCRDetection, ...]
    precise_masks: tuple[PreciseMaskPolygon, ...]


def _positive_int(value: object, name: str, *, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _unit_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result) or not 0.0 <= result <= 1.0:
        raise ValueError(f"{name} must be finite and in [0, 1]")
    return result


def _field(value: object, name: str) -> object | None:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _tuple_or_empty(value: object | None, name: str) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        raise TypeError(f"{name} must be an iterable of values")
    try:
        return tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise TypeError(f"{name} must be iterable") from exc


def _pixel_polygon_to_normalized(
    polygon: object,
    *,
    frame_width: int,
    frame_height: int,
) -> tuple[tuple[float, float], ...]:
    points = _tuple_or_empty(polygon, "polygon")
    if len(points) < 3:
        raise ValueError("polygon must contain at least three points")
    normalized: list[tuple[float, float]] = []
    x_den = float(frame_width - 1)
    y_den = float(frame_height - 1)
    for point in points:
        coords = _tuple_or_empty(point, "polygon point")
        if len(coords) != 2:
            raise ValueError("polygon points must have two coordinates")
        x, y = coords
        if isinstance(x, bool) or not isinstance(x, Real):
            raise TypeError("polygon x coordinate must be a real number")
        if isinstance(y, bool) or not isinstance(y, Real):
            raise TypeError("polygon y coordinate must be a real number")
        x = float(x)
        y = float(y)
        if not isfinite(x) or not isfinite(y):
            raise ValueError("polygon coordinates must be finite")
        normalized.append((max(0.0, min(1.0, x / x_den)), max(0.0, min(1.0, y / y_den))))
    return tuple(normalized)


def _normalized_box(points: tuple[tuple[float, float], ...]) -> BoundingBox:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x1, y1 = min(xs), min(ys)
    x2, y2 = max(xs), max(ys)
    if x2 <= x1 or y2 <= y1:
        raise ValueError("OCR polygon collapses to an empty box")
    return BoundingBox(x1, y1, x2 - x1, y2 - y1)


def _looks_like_word_item(value: object) -> bool:
    try:
        parts = tuple(value)  # type: ignore[arg-type]
    except TypeError:
        return False
    return len(parts) == 3 and isinstance(parts[0], str) and isinstance(parts[1], Real) and not isinstance(parts[1], bool)


def _iter_word_items(word_results: object | None) -> tuple[tuple[object, object, object], ...]:
    lines = _tuple_or_empty(word_results, "word_results")
    output: list[tuple[object, object, object]] = []
    for line in lines:
        if line is None:
            continue
        if _looks_like_word_item(line):
            parts = tuple(line)  # type: ignore[arg-type]
            output.append((parts[0], parts[1], parts[2]))
            continue
        for item in _tuple_or_empty(line, "word result line"):
            if not _looks_like_word_item(item):
                continue
            parts = tuple(item)  # type: ignore[arg-type]
            output.append((parts[0], parts[1], parts[2]))
    return tuple(output)


def adapt_rapidocr_output(
    result: object,
    *,
    frame_index: int,
    frame_width: int,
    frame_height: int,
    min_detection_confidence: float = 0.30,
    min_mask_confidence: float = 0.45,
    allow_line_masks: bool = False,
) -> OCRFrameAdapterResult:
    """Convert RapidOCR 3.x output into engine-neutral detections and masks.

    Line boxes are always treated as OCR observations. Destructive masks are
    created from ``word_results`` only, unless ``allow_line_masks`` is explicitly
    enabled. This keeps broad subtitle rectangles from becoming destructive by
    accident when word-level geometry is unavailable.
    """

    frame_index = _positive_int(frame_index, "frame_index", minimum=0)
    frame_width = _positive_int(frame_width, "frame_width", minimum=2)
    frame_height = _positive_int(frame_height, "frame_height", minimum=2)
    min_detection_confidence = _unit_real(min_detection_confidence, "min_detection_confidence")
    min_mask_confidence = _unit_real(min_mask_confidence, "min_mask_confidence")
    if type(allow_line_masks) is not bool:
        raise TypeError("allow_line_masks must be a boolean")

    boxes = _tuple_or_empty(_field(result, "boxes"), "boxes")
    txts = _tuple_or_empty(_field(result, "txts"), "txts")
    scores = _tuple_or_empty(_field(result, "scores"), "scores")
    if not boxes and not txts and not scores:
        return OCRFrameAdapterResult((), ())
    if not (len(boxes) == len(txts) == len(scores)):
        raise ValueError("RapidOCR boxes, txts and scores must have matching lengths")

    detections: list[OCRDetection] = []
    line_masks: list[PreciseMaskPolygon] = []
    for box, text, score in zip(boxes, txts, scores):
        confidence = _unit_real(score, "RapidOCR score")
        if not isinstance(text, str):
            raise TypeError("RapidOCR text values must be strings")
        try:
            points = _pixel_polygon_to_normalized(
                box,
                frame_width=frame_width,
                frame_height=frame_height,
            )
            bbox = _normalized_box(points)
        except (TypeError, ValueError):
            continue
        if confidence >= min_detection_confidence:
            detections.append(OCRDetection(frame_index, bbox, confidence, text))
        if allow_line_masks and confidence >= min_mask_confidence:
            try:
                line_masks.append(PreciseMaskPolygon(frame_index, points, confidence))
            except ValueError:
                pass

    word_masks: list[PreciseMaskPolygon] = []
    for _text, score, polygon in _iter_word_items(_field(result, "word_results")):
        confidence = _unit_real(score, "RapidOCR word score")
        if confidence < min_mask_confidence or polygon is None:
            continue
        try:
            points = _pixel_polygon_to_normalized(
                polygon,
                frame_width=frame_width,
                frame_height=frame_height,
            )
            word_masks.append(PreciseMaskPolygon(frame_index, points, confidence))
        except (TypeError, ValueError):
            continue

    masks = word_masks if word_masks else line_masks
    return OCRFrameAdapterResult(tuple(detections), dedupe_precise_masks(masks))


def _frame_dimensions(frame: object) -> tuple[int, int]:
    shape = getattr(frame, "shape", None)
    if shape is None:
        raise ValueError("frame_width and frame_height are required when frame.shape is unavailable")
    try:
        values = tuple(shape)
    except TypeError as exc:
        raise TypeError("frame.shape must be iterable") from exc
    if len(values) < 2:
        raise ValueError("frame.shape must contain height and width")
    height = _positive_int(int(values[0]), "frame height", minimum=2)
    width = _positive_int(int(values[1]), "frame width", minimum=2)
    return width, height


def run_rapidocr_frame(
    engine: object,
    frame: object,
    *,
    frame_index: int,
    frame_width: int | None = None,
    frame_height: int | None = None,
    min_detection_confidence: float = 0.30,
    min_mask_confidence: float = 0.45,
) -> OCRFrameAdapterResult:
    """Run an injected RapidOCR-compatible engine on one frame, fully locally."""

    if not callable(engine):
        raise TypeError("engine must be callable")
    if frame_width is None or frame_height is None:
        inferred_width, inferred_height = _frame_dimensions(frame)
        frame_width = inferred_width if frame_width is None else frame_width
        frame_height = inferred_height if frame_height is None else frame_height
    result = engine(frame, return_word_box=True)
    return adapt_rapidocr_output(
        result,
        frame_index=frame_index,
        frame_width=frame_width,
        frame_height=frame_height,
        min_detection_confidence=min_detection_confidence,
        min_mask_confidence=min_mask_confidence,
        allow_line_masks=False,
    )


def create_rapidocr_engine(
    *,
    language: str = "korean",
    text_score: float = 0.30,
) -> object:
    """Create the optional RapidOCR 3.x runtime without making it a hard dependency."""

    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a non-empty string")
    text_score = _unit_real(text_score, "text_score")
    try:
        module = import_module("rapidocr")
        rapidocr_cls = getattr(module, "RapidOCR")
    except (ImportError, AttributeError) as exc:
        raise RuntimeError("RapidOCR is not installed; install shorts-editor-cleanup[ocr]") from exc
    return rapidocr_cls(
        params={
            "Global.return_word_box": True,
            "Global.text_score": text_score,
            "Rec.lang_type": language,
        }
    )

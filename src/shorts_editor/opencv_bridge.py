from __future__ import annotations

import argparse
import json
from math import ceil, floor, isfinite
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Mapping, Sequence

from .local_vsr import VSR_RUNNER_PROTOCOL, VSRRunnerConfig
from .media import probe_media


_BACKEND_LICENSE = "Apache-2.0 (opencv-python-headless)"
_BACKEND_NAME = "shorts-editor-opencv-inpaint"
_MAX_MASK_AREA_RATIO = 0.10
_DEFAULT_INPAINT_RADIUS = 3.0


def create_builtin_opencv_runner_config(
    *,
    language: str = "korean",
    crf: int = 18,
) -> VSRRunnerConfig:
    """Return an explicitly approved config for the built-in CPU bridge."""

    return VSRRunnerConfig(
        (sys.executable, "-m", "shorts_editor.opencv_bridge"),
        gpu_device=-1,
        language=language,
        crf=crf,
        commercial_use_approved=True,
        backend_license=_BACKEND_LICENSE,
    )


def capability_payload() -> dict[str, object]:
    return {
        "protocol": VSR_RUNNER_PROTOCOL,
        "backend": _BACKEND_NAME,
        "backend_license": _BACKEND_LICENSE,
        "modes": ["lama"],
        "config_overlay": True,
        "json_output": True,
        "gpu_required": False,
        "precise_masks_only": True,
        "max_mask_area_ratio": _MAX_MASK_AREA_RATIO,
    }


def _opencv_modules():
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError(
            "built-in OpenCV bridge requires shorts-editor-cleanup[opencv]"
        ) from exc
    return cv2, np


def _positive_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")
    return result


def _unit_real(value: object, name: str) -> float:
    result = _positive_real(value, name)
    if result > 1.0:
        raise ValueError(f"{name} must be <= 1")
    return result


def _polygon_points(
    flat: object,
    *,
    width: int,
    height: int,
):
    cv2, np = _opencv_modules()
    if isinstance(flat, (str, bytes)) or not isinstance(flat, Sequence):
        raise TypeError("mask polygon must be a coordinate sequence")
    values = tuple(flat)
    if len(values) < 6 or len(values) % 2:
        raise ValueError("mask polygon must contain at least three x/y pairs")
    points: list[tuple[int, int]] = []
    for index in range(0, len(values), 2):
        x, y = values[index], values[index + 1]
        if isinstance(x, bool) or not isinstance(x, (int, float)):
            raise TypeError("mask polygon x must be numeric")
        if isinstance(y, bool) or not isinstance(y, (int, float)):
            raise TypeError("mask polygon y must be numeric")
        xf, yf = float(x), float(y)
        if not isfinite(xf) or not isfinite(yf):
            raise ValueError("mask polygon coordinates must be finite")
        xi, yi = round(xf), round(yf)
        if not 0 <= xi < width or not 0 <= yi < height:
            raise ValueError("mask polygon coordinates must stay inside the frame")
        points.append((xi, yi))
    return np.asarray(points, dtype=np.int32).reshape((-1, 1, 2))


def polygon_mask(
    *,
    width: int,
    height: int,
    polygons: Iterable[object],
    dilation_pixels: int = 1,
):
    """Rasterize reviewed pixel polygons into one uint8 inpaint mask."""

    cv2, np = _opencv_modules()
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError("width must be a positive integer")
    if isinstance(height, bool) or not isinstance(height, int) or height <= 0:
        raise ValueError("height must be a positive integer")
    if isinstance(dilation_pixels, bool) or not isinstance(dilation_pixels, int):
        raise TypeError("dilation_pixels must be an integer")
    if not 0 <= dilation_pixels <= 8:
        raise ValueError("dilation_pixels must be in [0, 8]")

    mask = np.zeros((height, width), dtype=np.uint8)
    count = 0
    for polygon in polygons:
        points = _polygon_points(polygon, width=width, height=height)
        cv2.fillPoly(mask, [points], 255)
        count += 1
    if count and dilation_pixels:
        kernel_size = (2 * dilation_pixels) + 1
        kernel = np.ones((kernel_size, kernel_size), dtype=np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)
    return mask


def inpaint_frame(
    frame,
    polygons: Iterable[object],
    *,
    radius: float = _DEFAULT_INPAINT_RADIUS,
    max_mask_area_ratio: float = _MAX_MASK_AREA_RATIO,
    dilation_pixels: int = 1,
):
    """Inpaint only reviewed precise polygons and reject broad destructive masks."""

    cv2, np = _opencv_modules()
    if not isinstance(frame, np.ndarray) or frame.ndim != 3 or frame.shape[2] != 3:
        raise TypeError("frame must be an HxWx3 NumPy array")
    if frame.dtype != np.uint8:
        raise TypeError("frame must use uint8 pixels")
    radius = _positive_real(radius, "radius")
    max_mask_area_ratio = _unit_real(max_mask_area_ratio, "max_mask_area_ratio")

    height, width = frame.shape[:2]
    mask = polygon_mask(
        width=width,
        height=height,
        polygons=polygons,
        dilation_pixels=dilation_pixels,
    )
    masked_pixels = int(np.count_nonzero(mask))
    if masked_pixels == 0:
        return frame.copy(), 0.0
    area_ratio = masked_pixels / float(width * height)
    if area_ratio > max_mask_area_ratio:
        raise RuntimeError(
            f"precise mask area ratio {area_ratio:.6f} exceeds safety limit "
            f"{max_mask_area_ratio:.6f}"
        )
    result = cv2.inpaint(frame, mask, radius, cv2.INPAINT_TELEA)
    return result, area_ratio


def _load_overlay(path: str | Path) -> Mapping[str, object]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("config overlay must be a JSON object")
    if value.get("subtitle_region_keyframes"):
        raise RuntimeError(
            "built-in OpenCV bridge rejects coarse subtitle-region masks; "
            "provide precise manual_mask_corrections"
        )
    corrections = value.get("manual_mask_corrections")
    if not isinstance(corrections, list) or not corrections:
        raise RuntimeError("built-in OpenCV bridge requires precise manual_mask_corrections")
    return value


def _correction_frame_map(
    corrections: object,
    *,
    fps: float,
) -> dict[int, list[object]]:
    if not isinstance(corrections, list):
        raise TypeError("manual_mask_corrections must be a list")
    fps = _positive_real(fps, "fps")
    result: dict[int, list[object]] = {}
    for correction in corrections:
        if not isinstance(correction, Mapping):
            raise TypeError("mask correction must be an object")
        start = correction.get("start")
        end = correction.get("end")
        if isinstance(start, bool) or not isinstance(start, (int, float)):
            raise TypeError("mask correction start must be numeric")
        if isinstance(end, bool) or not isinstance(end, (int, float)):
            raise TypeError("mask correction end must be numeric")
        start_f, end_f = float(start), float(end)
        if not isfinite(start_f) or not isfinite(end_f) or start_f < 0 or end_f <= start_f:
            raise ValueError("mask correction interval is invalid")
        polygons = correction.get("polygons")
        if not isinstance(polygons, list) or not polygons:
            raise ValueError("mask correction requires polygons")

        first = max(0, floor((start_f * fps) + 1e-6))
        last_exclusive = max(first + 1, ceil((end_f * fps) - 1e-6))
        for frame_index in range(first, last_exclusive):
            result.setdefault(frame_index, []).extend(polygons)
    return result


def _read_exact(stream, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def render_video(
    *,
    input_path: str,
    output_path: str,
    config_path: str,
    crf: int = 18,
    ffmpeg: str = "ffmpeg",
    max_mask_area_ratio: float = _MAX_MASK_AREA_RATIO,
) -> dict[str, object]:
    """CPU-render precise masks while decoding through FFmpeg and preserving audio."""

    cv2, np = _opencv_modules()
    input_resolved = str(Path(input_path).resolve())
    output_resolved = str(Path(output_path).resolve())
    if input_resolved == output_resolved:
        raise ValueError("input and output paths must differ")
    metadata = probe_media(input_resolved)
    overlay = _load_overlay(config_path)
    by_frame = _correction_frame_map(
        overlay["manual_mask_corrections"],
        fps=metadata.fps,
    )

    frame_size = metadata.width * metadata.height * 3
    decoder_cmd = [
        ffmpeg,
        "-v",
        "error",
        "-i",
        input_resolved,
        "-map",
        "0:v:0",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "pipe:1",
    ]
    encoder_cmd = [
        ffmpeg,
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s:v",
        f"{metadata.width}x{metadata.height}",
        "-r",
        f"{metadata.fps:.12g}",
        "-i",
        "pipe:0",
        "-i",
        input_resolved,
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        str(crf),
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        "-y",
        output_resolved,
    ]

    decoder = subprocess.Popen(
        decoder_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    encoder = subprocess.Popen(
        encoder_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if decoder.stdout is None or decoder.stderr is None or encoder.stdin is None or encoder.stderr is None:
        raise RuntimeError("failed to open FFmpeg pipes")

    frames = 0
    masked_frames = 0
    max_area = 0.0
    try:
        while True:
            raw = _read_exact(decoder.stdout, frame_size)
            if not raw:
                break
            if len(raw) != frame_size:
                raise RuntimeError(
                    f"decoder returned partial frame: {len(raw)} of {frame_size} bytes"
                )
            frame = np.frombuffer(raw, dtype=np.uint8).reshape(
                metadata.height,
                metadata.width,
                3,
            )
            polygons = by_frame.get(frames, ())
            if polygons:
                frame, area_ratio = inpaint_frame(
                    frame,
                    polygons,
                    max_mask_area_ratio=max_mask_area_ratio,
                )
                masked_frames += 1
                max_area = max(max_area, area_ratio)
            encoder.stdin.write(frame.tobytes())
            frames += 1
    except BaseException:
        decoder.kill()
        encoder.kill()
        raise
    finally:
        try:
            decoder.stdout.close()
        except Exception:
            pass
        try:
            encoder.stdin.close()
        except Exception:
            pass

    decoder_code = decoder.wait()
    encoder_code = encoder.wait()
    decoder_error = decoder.stderr.read().decode("utf-8", errors="replace").strip()
    encoder_error = encoder.stderr.read().decode("utf-8", errors="replace").strip()
    decoder.stderr.close()
    encoder.stderr.close()
    if decoder_code != 0:
        raise RuntimeError(f"FFmpeg decode failed: {decoder_error[:1000] or decoder_code}")
    if encoder_code != 0:
        raise RuntimeError(f"FFmpeg encode failed: {encoder_error[:1000] or encoder_code}")
    if frames == 0:
        raise RuntimeError("no video frames were decoded")
    if metadata.frame_count is not None and frames != metadata.frame_count:
        raise RuntimeError(
            f"decoded frame count {frames} differs from probed input count {metadata.frame_count}"
        )
    if masked_frames == 0:
        raise RuntimeError("no precise mask correction matched a decoded frame")

    output_probe = probe_media(output_resolved)
    if (output_probe.width, output_probe.height) != (metadata.width, metadata.height):
        raise RuntimeError("rendered output dimensions differ from input")
    if abs(output_probe.fps - metadata.fps) > 0.01:
        raise RuntimeError("rendered output frame rate differs from input")
    if output_probe.frame_count is not None and output_probe.frame_count != frames:
        raise RuntimeError(
            f"rendered frame count {output_probe.frame_count} differs from decoded input count {frames}"
        )
    expected_duration = frames / metadata.fps
    if abs(output_probe.duration_seconds - expected_duration) > (1.5 / metadata.fps):
        raise RuntimeError("rendered video duration differs from decoded input duration")

    return {
        "ok": True,
        "backend": _BACKEND_NAME,
        "backend_license": _BACKEND_LICENSE,
        "frames": frames,
        "masked_frames": masked_frames,
        "max_mask_area_ratio": round(max_area, 6),
        "input_codec": metadata.video_codec,
        "output_codec": output_probe.video_codec,
        "width": metadata.width,
        "height": metadata.height,
        "fps": metadata.fps,
        "quality_report": bool(overlay.get("quality_report", False)),
        "verify_removal_requested": bool(overlay.get("verify_removal", False)),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="shorts-editor built-in CPU inpaint bridge")
    parser.add_argument("-i", "--input")
    parser.add_argument("-o", "--output")
    parser.add_argument("-m", "--mode")
    parser.add_argument("--gpu", type=int, default=-1)
    parser.add_argument("--lang", default="korean")
    parser.add_argument("--crf", type=int, default=18)
    parser.add_argument("--config")
    parser.add_argument("--capabilities", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.capabilities:
        print(json.dumps(capability_payload(), ensure_ascii=False, separators=(",", ":")))
        return 0
    if args.mode != "lama":
        raise RuntimeError("built-in OpenCV bridge supports only the local-fast/lama mode")
    if args.gpu != -1:
        raise RuntimeError("built-in OpenCV bridge is CPU-only; use --gpu -1")
    if not args.input or not args.output or not args.config:
        raise ValueError("input, output and config are required")
    payload = render_video(
        input_path=args.input,
        output_path=args.output,
        config_path=args.config,
        crf=args.crf,
    )
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

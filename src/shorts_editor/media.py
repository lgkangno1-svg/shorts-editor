from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from math import isfinite
from pathlib import Path
import subprocess


_FFMPEG_PREFERRED_CODECS = frozenset({"av1", "hevc", "h265", "vp9"})


@dataclass(frozen=True)
class MediaProbe:
    """Normalized media metadata from ffprobe."""

    path: str
    video_codec: str
    width: int
    height: int
    fps: float
    duration_seconds: float
    frame_count: int | None
    audio_codec: str | None

    @property
    def has_audio(self) -> bool:
        return self.audio_codec is not None

    @property
    def portable_decode_recommended(self) -> bool:
        """Whether FFmpeg should be preferred over backend-specific decoders."""

        return self.video_codec.casefold() in _FFMPEG_PREFERRED_CODECS


@dataclass(frozen=True)
class DecodedFrame:
    """One RGB24 frame decoded by FFmpeg."""

    width: int
    height: int
    timestamp_seconds: float
    rgb24: bytes

    def as_numpy(self):
        """Return HxWx3 uint8 pixels when NumPy is installed."""

        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError("DecodedFrame.as_numpy() requires NumPy") from exc
        return np.frombuffer(self.rgb24, dtype=np.uint8).reshape(self.height, self.width, 3)


def _tool_name(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _timeout(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("timeout_seconds must be a real number")
    result = float(value)
    if not isfinite(result) or result <= 0.0:
        raise ValueError("timeout_seconds must be finite and > 0")
    return result


def _media_path(value: object) -> str:
    if isinstance(value, Path):
        path = value
    elif isinstance(value, str) and value.strip():
        path = Path(value)
    else:
        raise ValueError("path must be a non-empty filesystem path")
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return str(path.resolve())


def _fraction(value: object, name: str) -> float:
    if not isinstance(value, str) or not value or value in {"0/0", "N/A"}:
        raise ValueError(f"{name} is unavailable")
    try:
        result = float(Fraction(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{name} is invalid: {value!r}") from exc
    if not isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be finite and > 0")
    return result


def _positive_int(value: object, name: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if result <= 0:
        raise ValueError(f"{name} must be > 0")
    return result


def _duration(video: dict[str, object], container: dict[str, object]) -> float:
    raw = video.get("duration")
    if raw in (None, "N/A"):
        raw = container.get("duration")
    try:
        result = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("media duration is unavailable") from exc
    if not isfinite(result) or result <= 0.0:
        raise ValueError("media duration must be finite and > 0")
    return result


def _run(command: list[str], *, timeout_seconds: float, binary: bool) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            command,
            capture_output=True,
            text=not binary,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"required media tool is not installed: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"media tool timed out after {timeout_seconds:g}s: {command[0]}") from exc


def probe_media(
    path: str | Path,
    *,
    ffprobe: str = "ffprobe",
    timeout_seconds: float = 30.0,
) -> MediaProbe:
    """Probe one video using FFprobe without relying on OpenCV codec support."""

    resolved = _media_path(path)
    ffprobe = _tool_name(ffprobe, "ffprobe")
    timeout_seconds = _timeout(timeout_seconds)
    completed = _run(
        [
            ffprobe,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            resolved,
        ],
        timeout_seconds=timeout_seconds,
        binary=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise RuntimeError(f"ffprobe failed: {detail[:1000] or f'exit {completed.returncode}'}")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned invalid JSON") from exc

    streams = payload.get("streams")
    container = payload.get("format")
    if not isinstance(streams, list) or not isinstance(container, dict):
        raise RuntimeError("ffprobe JSON is missing streams/format")
    video = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("media has no video stream")

    codec = video.get("codec_name")
    if not isinstance(codec, str) or not codec.strip():
        raise ValueError("video codec is unavailable")
    width = _positive_int(video.get("width"), "video width")
    height = _positive_int(video.get("height"), "video height")

    fps = None
    for field in ("avg_frame_rate", "r_frame_rate"):
        try:
            fps = _fraction(video.get(field), field)
            break
        except ValueError:
            continue
    if fps is None:
        raise ValueError("video frame rate is unavailable")

    duration = _duration(video, container)
    frame_count = None
    raw_frames = video.get("nb_frames")
    if raw_frames not in (None, "N/A"):
        try:
            frame_count = _positive_int(raw_frames, "video frame count")
        except ValueError:
            frame_count = None

    audio_codec = None
    audio = next((item for item in streams if isinstance(item, dict) and item.get("codec_type") == "audio"), None)
    if audio is not None:
        raw_audio = audio.get("codec_name")
        if isinstance(raw_audio, str) and raw_audio.strip():
            audio_codec = raw_audio.strip()

    return MediaProbe(
        path=resolved,
        video_codec=codec.strip(),
        width=width,
        height=height,
        fps=fps,
        duration_seconds=duration,
        frame_count=frame_count,
        audio_codec=audio_codec,
    )


def decode_frame_rgb(
    path: str | Path,
    *,
    timestamp_seconds: float,
    ffprobe: str = "ffprobe",
    ffmpeg: str = "ffmpeg",
    timeout_seconds: float = 30.0,
) -> DecodedFrame:
    """Decode one frame through FFmpeg as deterministic RGB24 bytes."""

    if isinstance(timestamp_seconds, bool) or not isinstance(timestamp_seconds, (int, float)):
        raise TypeError("timestamp_seconds must be a real number")
    timestamp = float(timestamp_seconds)
    if not isfinite(timestamp) or timestamp < 0.0:
        raise ValueError("timestamp_seconds must be finite and >= 0")

    timeout_seconds = _timeout(timeout_seconds)
    metadata = probe_media(path, ffprobe=ffprobe, timeout_seconds=timeout_seconds)
    if timestamp >= metadata.duration_seconds:
        raise ValueError("timestamp_seconds must be before media duration")

    ffmpeg = _tool_name(ffmpeg, "ffmpeg")
    completed = _run(
        [
            ffmpeg,
            "-v",
            "error",
            "-ss",
            f"{timestamp:.6f}",
            "-i",
            metadata.path,
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
        timeout_seconds=timeout_seconds,
        binary=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace") if isinstance(completed.stderr, bytes) else str(completed.stderr or "")
        raise RuntimeError(f"ffmpeg frame decode failed: {stderr.strip()[:1000] or f'exit {completed.returncode}'}")

    expected = metadata.width * metadata.height * 3
    if len(completed.stdout) != expected:
        raise RuntimeError(f"ffmpeg returned {len(completed.stdout)} RGB bytes; expected {expected}")

    return DecodedFrame(
        width=metadata.width,
        height=metadata.height,
        timestamp_seconds=timestamp,
        rgb24=bytes(completed.stdout),
    )

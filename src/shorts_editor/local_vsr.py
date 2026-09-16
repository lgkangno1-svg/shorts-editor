from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Mapping

from .routing import Engine
from .tracks import RemovalTrack, TargetKind


class LocalVSRMode(str):
    LAMA = "lama"
    STTN = "sttn"
    AUTO = "auto"


@dataclass(frozen=True)
class VSRRunnerConfig:
    """Configuration for the MIT-licensed VideoSubtitleRemover local CLI.

    The runner is deliberately external: this project does not vendor VSR or
    its optional model stack. A reviewed local VSR checkout/runtime can be
    upgraded independently while this core owns routing, tracks and QC.
    """

    argv_prefix: tuple[str, ...]
    cwd: str | None = None
    gpu_device: int = -1
    language: str = "en"
    crf: int = 18
    detection_engine: str = "rapidocr"
    quality_report: bool = True
    verify_removal: bool = True

    def __post_init__(self) -> None:
        if not self.argv_prefix or any(not isinstance(arg, str) or not arg.strip() for arg in self.argv_prefix):
            raise ValueError("argv_prefix must contain non-empty command arguments")
        if self.cwd is not None and (not isinstance(self.cwd, str) or not self.cwd.strip()):
            raise ValueError("cwd must be a non-empty path when provided")
        if isinstance(self.gpu_device, bool) or not isinstance(self.gpu_device, int) or self.gpu_device < -1:
            raise ValueError("gpu_device must be -1 for CPU or a non-negative device index")
        if not isinstance(self.language, str) or not self.language.strip():
            raise ValueError("language must be a non-empty string")
        if isinstance(self.crf, bool) or not isinstance(self.crf, int) or not 0 <= self.crf <= 51:
            raise ValueError("crf must be an integer in [0, 51]")
        if not isinstance(self.detection_engine, str) or not self.detection_engine.strip():
            raise ValueError("detection_engine must be a non-empty string")
        if type(self.quality_report) is not bool or type(self.verify_removal) is not bool:
            raise TypeError("quality_report and verify_removal must be booleans")


@dataclass(frozen=True)
class VSRExecutionResult:
    payload: Mapping[str, object]
    stdout: str
    stderr: str


def vsr_mode_for_engine(engine: Engine) -> str:
    if not isinstance(engine, Engine):
        raise TypeError("engine must be an Engine")
    if engine is Engine.LOCAL_FAST:
        return LocalVSRMode.LAMA
    if engine is Engine.LOCAL_TEMPORAL:
        return LocalVSRMode.STTN
    return LocalVSRMode.AUTO


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
    return value


def _positive_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and > 0")
    return result


def _pixel_rect(sample_box, frame_width: int, frame_height: int) -> list[int]:
    x1 = max(0, min(frame_width - 1, round(sample_box.x * frame_width)))
    y1 = max(0, min(frame_height - 1, round(sample_box.y * frame_height)))
    x2 = max(x1 + 1, min(frame_width, round((sample_box.x + sample_box.width) * frame_width)))
    y2 = max(y1 + 1, min(frame_height, round((sample_box.y + sample_box.height) * frame_height)))
    return [x1, y1, x2, y2]


def track_to_vsr_keyframes(
    track: RemovalTrack,
    *,
    frame_width: int,
    frame_height: int,
    fps: float,
    max_keyframes: int = 240,
) -> list[dict[str, object]]:
    """Convert a normalized overlay track to VSR's moving-region schema."""
    if not isinstance(track, RemovalTrack):
        raise TypeError("track must be a RemovalTrack")
    if track.kind not in (TargetKind.SUBTITLE, TargetKind.TEXT, TargetKind.WATERMARK, TargetKind.LOGO):
        raise ValueError("only overlay-like tracks can be exported as VSR text regions")
    frame_width = _positive_int(frame_width, "frame_width")
    frame_height = _positive_int(frame_height, "frame_height")
    fps = _positive_real(fps, "fps")
    max_keyframes = _positive_int(max_keyframes, "max_keyframes")

    samples = track.samples
    if len(samples) > 1 and max_keyframes < 2:
        raise ValueError("max_keyframes must be >= 2 for a moving/multi-sample track")
    if len(samples) > max_keyframes:
        step = (len(samples) - 1) / (max_keyframes - 1)
        indices = sorted({round(i * step) for i in range(max_keyframes)})
        indices[0] = 0
        indices[-1] = len(samples) - 1
        samples = tuple(samples[index] for index in indices)

    return [
        {
            "time": round(sample.frame_index / fps, 6),
            "rect": _pixel_rect(sample.box, frame_width, frame_height),
        }
        for sample in samples
    ]


def build_vsr_config_overlay(
    config: VSRRunnerConfig,
    *,
    track: RemovalTrack | None = None,
    frame_width: int | None = None,
    frame_height: int | None = None,
    fps: float | None = None,
) -> dict[str, object]:
    if not isinstance(config, VSRRunnerConfig):
        raise TypeError("config must be VSRRunnerConfig")
    overlay: dict[str, object] = {
        "detection_engine": config.detection_engine,
        "quality_report": config.quality_report,
        "verify_removal": config.verify_removal,
    }
    if track is not None:
        if frame_width is None or frame_height is None or fps is None:
            raise ValueError("frame_width, frame_height and fps are required with a track")
        keyframes = track_to_vsr_keyframes(
            track,
            frame_width=frame_width,
            frame_height=frame_height,
            fps=fps,
        )
        overlay["subtitle_region_keyframes"] = [{"keyframes": keyframes}]
        overlay["sttn_skip_detection"] = True
    return overlay


def build_vsr_command(
    config: VSRRunnerConfig,
    *,
    input_path: str,
    output_path: str,
    engine: Engine,
    config_path: str | None = None,
) -> tuple[str, ...]:
    if not isinstance(config, VSRRunnerConfig):
        raise TypeError("config must be VSRRunnerConfig")
    if not isinstance(input_path, str) or not input_path.strip():
        raise ValueError("input_path must be non-empty")
    if not isinstance(output_path, str) or not output_path.strip():
        raise ValueError("output_path must be non-empty")
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        raise ValueError("input and output paths must differ")
    mode = vsr_mode_for_engine(engine)
    command = [
        *config.argv_prefix,
        "-i",
        input_path,
        "-o",
        output_path,
        "-m",
        mode,
        "--gpu",
        str(config.gpu_device),
        "--lang",
        config.language,
        "--crf",
        str(config.crf),
        "--json",
    ]
    if config_path is not None:
        if not isinstance(config_path, str) or not config_path.strip():
            raise ValueError("config_path must be a non-empty path")
        command.extend(("--config", config_path))
    return tuple(command)


def offline_environment(base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return environment flags that tell common model hubs to stay offline."""
    env = dict(os.environ if base is None else base)
    env.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "HF_DATASETS_OFFLINE": "1",
            "DO_NOT_TRACK": "1",
        }
    )
    return env


def _parse_json_stdout(stdout: str) -> Mapping[str, object]:
    if not isinstance(stdout, str):
        raise TypeError("stdout must be a string")
    stripped = stdout.strip()
    if not stripped:
        raise ValueError("VSR produced no JSON output")
    try:
        value = json.loads(stripped)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    for line in reversed(stripped.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("VSR stdout did not contain a JSON object")


def run_vsr_local(
    config: VSRRunnerConfig,
    *,
    input_path: str,
    output_path: str,
    engine: Engine,
    track: RemovalTrack | None = None,
    frame_width: int | None = None,
    frame_height: int | None = None,
    fps: float | None = None,
    timeout_seconds: float | None = None,
) -> VSRExecutionResult:
    """Execute the reviewed local VSR CLI with a temporary JSON overlay."""
    if timeout_seconds is not None:
        timeout_seconds = _positive_real(timeout_seconds, "timeout_seconds")
    overlay = build_vsr_config_overlay(
        config,
        track=track,
        frame_width=frame_width,
        frame_height=frame_height,
        fps=fps,
    )
    with TemporaryDirectory(prefix="shorts-editor-vsr-") as tmp:
        config_path = Path(tmp) / "config.json"
        config_path.write_text(json.dumps(overlay, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        command = build_vsr_command(
            config,
            input_path=input_path,
            output_path=output_path,
            engine=engine,
            config_path=str(config_path),
        )
        completed = subprocess.run(
            command,
            cwd=config.cwd,
            env=offline_environment(),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            check=False,
        )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}"
        raise RuntimeError(f"local VSR failed: {detail[:1000]}")
    payload = _parse_json_stdout(completed.stdout)
    return VSRExecutionResult(payload=payload, stdout=completed.stdout, stderr=completed.stderr)

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from shorts_editor.media import DecodedFrame, MediaProbe, decode_frame_rgb, probe_media


def _touch(tmp_path: Path) -> Path:
    path = tmp_path / "fixture.mp4"
    path.write_bytes(b"fixture")
    return path


def _probe_payload(*, codec="hevc", fps="30/1", frames="205", audio=True):
    streams = [
        {
            "codec_type": "video",
            "codec_name": codec,
            "width": 1080,
            "height": 1920,
            "avg_frame_rate": fps,
            "r_frame_rate": fps,
            "nb_frames": frames,
        }
    ]
    if audio:
        streams.append({"codec_type": "audio", "codec_name": "aac"})
    return {"streams": streams, "format": {"duration": "6.849887"}}


def test_probe_media_normalizes_real_fixture_style_hevc_metadata(tmp_path, monkeypatch):
    path = _touch(tmp_path)
    payload = _probe_payload()

    def fake_run(command, **kwargs):
        assert command[0] == "ffprobe"
        assert "-show_streams" in command
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = probe_media(path)

    assert result.video_codec == "hevc"
    assert result.width == 1080
    assert result.height == 1920
    assert result.fps == pytest.approx(30.0)
    assert result.duration_seconds == pytest.approx(6.849887)
    assert result.frame_count == 205
    assert result.audio_codec == "aac"
    assert result.has_audio is True
    assert result.portable_decode_recommended is True


@pytest.mark.parametrize("codec", ["hevc", "h265", "av1", "vp9"])
def test_portable_decode_is_recommended_for_codec_sensitive_inputs(codec):
    result = MediaProbe("x.mp4", codec, 1080, 1920, 30.0, 1.0, 30, None)
    assert result.portable_decode_recommended is True


def test_h264_does_not_force_portable_decode():
    result = MediaProbe("x.mp4", "h264", 1080, 1920, 30.0, 1.0, 30, None)
    assert result.portable_decode_recommended is False


def test_probe_falls_back_to_r_frame_rate_and_container_duration(tmp_path, monkeypatch):
    path = _touch(tmp_path)
    payload = _probe_payload(fps="0/0", frames="N/A", audio=False)
    payload["streams"][0]["r_frame_rate"] = "30000/1001"

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = probe_media(path)

    assert result.fps == pytest.approx(30000 / 1001)
    assert result.frame_count is None
    assert result.audio_codec is None
    assert result.has_audio is False


def test_probe_rejects_missing_video_stream(tmp_path, monkeypatch):
    path = _touch(tmp_path)
    payload = {"streams": [{"codec_type": "audio", "codec_name": "aac"}], "format": {"duration": "1.0"}}

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, json.dumps(payload), ""),
    )
    with pytest.raises(ValueError, match="no video stream"):
        probe_media(path)


def test_probe_surfaces_missing_ffprobe(tmp_path, monkeypatch):
    path = _touch(tmp_path)

    def fake_run(command, **kwargs):
        raise FileNotFoundError(command[0])

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="required media tool is not installed"):
        probe_media(path)


def test_decode_frame_rgb_uses_ffmpeg_and_validates_byte_count(tmp_path, monkeypatch):
    path = _touch(tmp_path)
    metadata = MediaProbe(str(path.resolve()), "hevc", 4, 3, 30.0, 2.0, 60, None)
    monkeypatch.setattr("shorts_editor.media.probe_media", lambda *args, **kwargs: metadata)

    expected = bytes(range(36))

    def fake_run(command, **kwargs):
        assert command[0] == "ffmpeg"
        assert command[command.index("-ss") + 1] == "0.500000"
        assert command[-1] == "pipe:1"
        assert kwargs["text"] is False
        return subprocess.CompletedProcess(command, 0, expected, b"")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = decode_frame_rgb(path, timestamp_seconds=0.5)

    assert isinstance(result, DecodedFrame)
    assert result.width == 4
    assert result.height == 3
    assert result.timestamp_seconds == 0.5
    assert result.rgb24 == expected


def test_decode_frame_rejects_short_ffmpeg_output(tmp_path, monkeypatch):
    path = _touch(tmp_path)
    metadata = MediaProbe(str(path.resolve()), "hevc", 4, 3, 30.0, 2.0, 60, None)
    monkeypatch.setattr("shorts_editor.media.probe_media", lambda *args, **kwargs: metadata)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, b"too-short", b""),
    )

    with pytest.raises(RuntimeError, match="expected 36"):
        decode_frame_rgb(path, timestamp_seconds=0.5)


@pytest.mark.parametrize("timestamp", [-1, float("nan"), float("inf")])
def test_decode_frame_rejects_invalid_timestamps(tmp_path, timestamp):
    path = _touch(tmp_path)
    with pytest.raises(ValueError):
        decode_frame_rgb(path, timestamp_seconds=timestamp)


def test_decode_frame_rejects_timestamp_at_duration(tmp_path, monkeypatch):
    path = _touch(tmp_path)
    metadata = MediaProbe(str(path.resolve()), "hevc", 4, 3, 30.0, 2.0, 60, None)
    monkeypatch.setattr("shorts_editor.media.probe_media", lambda *args, **kwargs: metadata)

    with pytest.raises(ValueError, match="before media duration"):
        decode_frame_rgb(path, timestamp_seconds=2.0)

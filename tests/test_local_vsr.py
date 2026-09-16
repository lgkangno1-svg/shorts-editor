import json
import os
import sys
from pathlib import Path

import pytest

from shorts_editor.local_vsr import (
    VSRRunnerConfig,
    build_vsr_command,
    build_vsr_config_overlay,
    offline_environment,
    run_vsr_local,
    track_to_vsr_keyframes,
    vsr_mode_for_engine,
)
from shorts_editor.routing import Engine
from shorts_editor.tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


def subtitle_track():
    return RemovalTrack(
        "sub",
        TargetKind.SUBTITLE,
        (
            TrackSample(0, BoundingBox(0.10, 0.75, 0.80, 0.10), 0.9),
            TrackSample(30, BoundingBox(0.12, 0.74, 0.76, 0.11), 0.9),
        ),
    )


def test_engine_mapping_keeps_all_tiers_local():
    assert vsr_mode_for_engine(Engine.LOCAL_FAST) == "lama"
    assert vsr_mode_for_engine(Engine.LOCAL_TEMPORAL) == "sttn"
    assert vsr_mode_for_engine(Engine.SMART_PRO) == "auto"


def test_track_exports_pixel_keyframes_in_vsr_x1_y1_x2_y2_schema():
    keys = track_to_vsr_keyframes(subtitle_track(), frame_width=1000, frame_height=500, fps=30)
    assert keys == [
        {"time": 0.0, "rect": [100, 375, 900, 425]},
        {"time": 1.0, "rect": [120, 370, 880, 425]},
    ]


def test_keyframe_downsampling_keeps_first_and_last():
    samples = tuple(
        TrackSample(i, BoundingBox(0.10 + i * 0.005, 0.75, 0.50, 0.08), 0.9)
        for i in range(10)
    )
    track = RemovalTrack("long", TargetKind.SUBTITLE, samples)
    keys = track_to_vsr_keyframes(track, frame_width=1000, frame_height=500, fps=10, max_keyframes=2)
    assert len(keys) == 2
    assert keys[0]["time"] == 0.0
    assert keys[-1]["time"] == 0.9


def test_multi_sample_track_rejects_single_keyframe_budget():
    with pytest.raises(ValueError):
        track_to_vsr_keyframes(subtitle_track(), frame_width=1000, frame_height=500, fps=30, max_keyframes=1)


def test_track_overlay_skips_second_detection_and_enables_quality_verification():
    cfg = VSRRunnerConfig((sys.executable, "-m", "backend.processor"))
    overlay = build_vsr_config_overlay(cfg, track=subtitle_track(), frame_width=1000, frame_height=500, fps=30)
    assert overlay["detection_engine"] == "rapidocr"
    assert overlay["quality_report"] is True
    assert overlay["verify_removal"] is True
    assert overlay["sttn_skip_detection"] is True
    assert len(overlay["subtitle_region_keyframes"][0]["keyframes"]) == 2


def test_command_is_shell_free_argument_vector():
    cfg = VSRRunnerConfig(("python", "-m", "backend.processor"), gpu_device=-1, language="ko", crf=18)
    cmd = build_vsr_command(cfg, input_path="in.mp4", output_path="out.mp4", engine=Engine.LOCAL_TEMPORAL, config_path="cfg.json")
    assert cmd[:3] == ("python", "-m", "backend.processor")
    assert ("-m", "sttn") == (cmd[7], cmd[8])
    assert "--config" in cmd
    assert ";" not in cmd


def test_same_input_output_is_rejected():
    cfg = VSRRunnerConfig(("python", "-m", "backend.processor"))
    with pytest.raises(ValueError):
        build_vsr_command(cfg, input_path="same.mp4", output_path="same.mp4", engine=Engine.LOCAL_FAST)


def test_offline_environment_sets_common_hub_guards():
    env = offline_environment({"PATH": "x"})
    assert env["PATH"] == "x"
    assert env["HF_HUB_OFFLINE"] == "1"
    assert env["TRANSFORMERS_OFFLINE"] == "1"


def test_local_runner_passes_config_to_fake_process(tmp_path):
    fake = tmp_path / "fake_vsr.py"
    fake.write_text(
        "import json, pathlib, sys\n"
        "args=sys.argv[1:]\n"
        "cfg=pathlib.Path(args[args.index('--config')+1])\n"
        "payload=json.loads(cfg.read_text(encoding='utf-8'))\n"
        "print(json.dumps({'ok': True, 'mode': args[args.index('-m')+1], 'quality': payload['quality_report'], 'skip': payload.get('sttn_skip_detection', False)}))\n",
        encoding="utf-8",
    )
    input_path = tmp_path / "input.mp4"
    input_path.write_bytes(b"fixture")
    output_path = tmp_path / "output.mp4"
    cfg = VSRRunnerConfig((sys.executable, str(fake)))
    result = run_vsr_local(
        cfg,
        input_path=str(input_path),
        output_path=str(output_path),
        engine=Engine.LOCAL_TEMPORAL,
        track=subtitle_track(),
        frame_width=1000,
        frame_height=500,
        fps=30,
        timeout_seconds=5,
    )
    assert result.payload == {"ok": True, "mode": "sttn", "quality": True, "skip": True}

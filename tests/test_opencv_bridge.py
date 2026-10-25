from __future__ import annotations

import json
import sys

import numpy as np
import pytest

pytest.importorskip("cv2")

from shorts_editor.local_vsr import VSR_RUNNER_PROTOCOL, probe_vsr_runner
from shorts_editor.opencv_bridge import (
    _correction_frame_map,
    _load_overlay,
    capability_payload,
    create_builtin_opencv_runner_config,
    inpaint_frame,
    polygon_mask,
)


def test_builtin_runner_is_explicitly_approved_and_cpu_only():
    cfg = create_builtin_opencv_runner_config(language="korean", crf=19)
    assert cfg.argv_prefix == (sys.executable, "-m", "shorts_editor.opencv_bridge")
    assert cfg.gpu_device == -1
    assert cfg.crf == 19
    assert cfg.commercial_use_approved is True
    assert "Apache-2.0" in cfg.backend_license


def test_builtin_runner_capability_handshake_is_real_subprocess():
    cfg = create_builtin_opencv_runner_config()
    caps = probe_vsr_runner(cfg, timeout_seconds=10)
    assert caps.protocol == VSR_RUNNER_PROTOCOL
    assert caps.modes == ("lama",)
    assert caps.config_overlay is True
    assert caps.json_output is True


def test_capability_payload_declares_precise_mask_cpu_contract():
    payload = capability_payload()
    assert payload["protocol"] == VSR_RUNNER_PROTOCOL
    assert payload["modes"] == ["lama"]
    assert payload["gpu_required"] is False
    assert payload["precise_masks_only"] is True
    assert payload["max_mask_area_ratio"] == pytest.approx(0.10)


def test_polygon_mask_rasterizes_and_dilates_reviewed_polygon():
    mask = polygon_mask(
        width=20,
        height=10,
        polygons=[(5, 3, 10, 3, 10, 6, 5, 6)],
        dilation_pixels=1,
    )
    assert mask.shape == (10, 20)
    assert mask.dtype == np.uint8
    assert mask[4, 7] == 255
    assert np.count_nonzero(mask) > 5 * 3


def test_polygon_mask_rejects_out_of_frame_coordinates():
    with pytest.raises(ValueError, match="inside the frame"):
        polygon_mask(
            width=20,
            height=10,
            polygons=[(-1, 1, 2, 1, 2, 2, 0, 2)],
        )


def test_inpaint_changes_only_small_neighborhood_and_keeps_protected_pixels():
    frame = np.zeros((80, 120, 3), dtype=np.uint8)
    frame[:] = (120, 70, 30)
    frame[30:40, 45:75] = (255, 255, 255)
    original = frame.copy()

    result, area = inpaint_frame(
        frame,
        [(45, 30, 74, 30, 74, 39, 45, 39)],
        dilation_pixels=1,
    )

    assert 0 < area < 0.10
    assert np.mean(np.abs(result[32:38, 50:70].astype(int) - original[32:38, 50:70].astype(int))) > 20
    assert np.array_equal(result[0:20, 0:20], original[0:20, 0:20])


def test_inpaint_rejects_broad_destructive_mask():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(RuntimeError, match="exceeds safety limit"):
        inpaint_frame(
            frame,
            [(0, 0, 99, 0, 99, 30, 0, 30)],
            dilation_pixels=0,
            max_mask_area_ratio=0.10,
        )


def test_correction_intervals_map_to_expected_frames():
    corrections = [
        {
            "start": 10 / 30,
            "end": 12 / 30,
            "polygons": [[1, 1, 2, 1, 2, 2, 1, 2]],
        }
    ]
    result = _correction_frame_map(corrections, fps=30.0)
    assert sorted(result) == [10, 11]


def test_overlay_rejects_coarse_track_masks(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "subtitle_region_keyframes": [{"keyframes": []}],
                "manual_mask_corrections": [
                    {"start": 0.0, "end": 0.1, "polygons": [[1, 1, 2, 1, 2, 2]]}
                ],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(RuntimeError, match="rejects coarse subtitle-region masks"):
        _load_overlay(path)


def test_overlay_requires_precise_corrections(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"quality_report": True}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="requires precise manual_mask_corrections"):
        _load_overlay(path)

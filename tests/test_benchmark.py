import numpy as np
import pytest

from shorts_editor.benchmark import evaluate_paired_video


def fixture_frames():
    clean = np.zeros((3, 8, 8, 3), dtype=np.uint8)
    overlay = clean.copy()
    mask = np.zeros((3, 8, 8), dtype=bool)
    mask[:, 3:5, 2:6] = True
    overlay[mask] = 255
    return overlay, clean, mask


def test_perfect_cleanup_scores_zero_penalties_and_passes():
    overlay, clean, mask = fixture_frames()
    result = evaluate_paired_video(overlay, clean.copy(), clean, mask)
    assert result.metrics.residual_score == 0.0
    assert result.metrics.flicker_score == 0.0
    assert result.metrics.boundary_score == 0.0
    assert result.metrics.protected_damage_score == 0.0
    assert result.decision.passed is True
    assert result.frame_count == 3
    assert result.mask_coverage > 0.0


def test_unchanged_overlay_fails_as_visible_residual():
    overlay, clean, mask = fixture_frames()
    result = evaluate_paired_video(overlay, overlay.copy(), clean, mask)
    assert result.metrics.residual_score == pytest.approx(1.0)
    assert result.decision.passed is False
    assert result.decision.reason == "visible removal residual"


def test_damage_far_outside_mask_trips_protected_region_gate():
    overlay, clean, mask = fixture_frames()
    candidate = clean.copy()
    candidate[:, 0:2, 0:2] = 255
    result = evaluate_paired_video(overlay, candidate, clean, mask)
    assert result.metrics.protected_damage_score > 0.30
    assert result.decision.passed is False
    assert result.decision.reason == "protected-region damage"


def test_boundary_spill_is_measured_without_counting_as_residual():
    overlay, clean, mask = fixture_frames()
    candidate = clean.copy()
    candidate[:, 2, 2:6] = 255
    result = evaluate_paired_video(overlay, candidate, clean, mask, protected_margin=2)
    assert result.metrics.residual_score == 0.0
    assert result.metrics.boundary_score > 0.0
    assert result.metrics.protected_damage_score == 0.0


def test_temporal_instability_is_measured_against_clean_motion():
    overlay, clean, mask = fixture_frames()
    candidate = clean.copy()
    candidate[1][mask[1]] = 255
    result = evaluate_paired_video(overlay, candidate, clean, mask)
    assert result.metrics.flicker_score > 0.5
    assert result.decision.passed is False


def test_mismatched_video_shapes_are_rejected():
    overlay, clean, mask = fixture_frames()
    with pytest.raises(ValueError, match="identical shapes"):
        evaluate_paired_video(overlay[:, :, :-1], clean, clean, mask)


def test_empty_mask_is_rejected():
    overlay, clean, _mask = fixture_frames()
    empty = np.zeros((3, 8, 8), dtype=bool)
    with pytest.raises(ValueError, match="at least one target pixel"):
        evaluate_paired_video(overlay, clean.copy(), clean, empty)


def test_nonfinite_mask_is_rejected_instead_of_becoming_true():
    overlay, clean, mask = fixture_frames()
    invalid = mask.astype(np.float32)
    invalid[0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="finite values"):
        evaluate_paired_video(overlay, clean.copy(), clean, invalid)


def test_numpy_integer_radii_are_accepted():
    overlay, clean, mask = fixture_frames()
    result = evaluate_paired_video(overlay, clean.copy(), clean, mask, boundary_radius=np.int64(2), protected_margin=np.int32(2))
    assert result.decision.passed is True


def test_fixture_without_overlay_signal_is_rejected():
    clean = np.zeros((2, 4, 4, 3), dtype=np.uint8)
    mask = np.zeros((2, 4, 4), dtype=bool)
    mask[:, 1:3, 1:3] = True
    with pytest.raises(ValueError, match="insufficient overlay signal"):
        evaluate_paired_video(clean, clean.copy(), clean, mask)

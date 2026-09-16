import pytest

from shorts_editor.chunking import FrameChunk
from shorts_editor.windows import ProcessingWindow, plan_processing_windows


def test_emit_regions_partition_chunk_without_duplicates():
    windows = plan_processing_windows(FrameChunk(0, 20), max_frames=10, overlap_frames=2)
    emitted = [frame for window in windows for frame in range(window.emit.start, window.emit.end)]
    assert emitted == list(range(20))
    assert all(window.context.length <= 10 for window in windows)


def test_overlap_stays_inside_scene_bounded_chunk():
    windows = plan_processing_windows(FrameChunk(10, 25), max_frames=9, overlap_frames=2)
    assert windows[0].context.start == 10
    assert windows[-1].context.end == 25
    assert all(10 <= window.context.start < window.context.end <= 25 for window in windows)


def test_context_contains_emit():
    window = ProcessingWindow(FrameChunk(2, 8), FrameChunk(4, 7))
    assert window.context.start <= window.emit.start
    assert window.context.end >= window.emit.end


def test_excessive_overlap_fails_closed():
    with pytest.raises(ValueError):
        plan_processing_windows(FrameChunk(0, 10), max_frames=8, overlap_frames=4)


def test_window_frame_counts_reject_fractional_and_boolean_values():
    chunk = FrameChunk(0, 10)
    with pytest.raises(TypeError):
        plan_processing_windows(chunk, max_frames=8.5, overlap_frames=2)
    with pytest.raises(TypeError):
        plan_processing_windows(chunk, max_frames=True, overlap_frames=0)
    with pytest.raises(TypeError):
        plan_processing_windows(chunk, max_frames=8, overlap_frames=1.5)
    with pytest.raises(TypeError):
        plan_processing_windows(chunk, max_frames=8, overlap_frames=False)

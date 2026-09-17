import numpy as np
import pytest

from shorts_editor.chunking import FrameChunk, plan_chunks


def test_chunks_are_bounded():
    assert plan_chunks(10, 4) == (
        FrameChunk(0, 4), FrameChunk(4, 8), FrameChunk(8, 10)
    )


def test_chunks_never_cross_scene_cut():
    chunks = plan_chunks(12, 5, (3, 9))
    assert chunks == (
        FrameChunk(0, 3), FrameChunk(3, 8), FrameChunk(8, 9), FrameChunk(9, 12)
    )
    assert all(not (chunk.start < 3 < chunk.end) for chunk in chunks)
    assert all(not (chunk.start < 9 < chunk.end) for chunk in chunks)


def test_numpy_integer_inputs_are_normalized_to_python_ints():
    chunks = plan_chunks(np.int64(10), np.int32(4), (np.int64(3), np.int32(9)))
    assert chunks == (FrameChunk(0, 3), FrameChunk(3, 7), FrameChunk(7, 9), FrameChunk(9, 10))
    assert all(type(chunk.start) is int and type(chunk.end) is int for chunk in chunks)


def test_frame_chunk_normalizes_numpy_integer_boundaries():
    chunk = FrameChunk(np.int64(2), np.int32(5))
    assert chunk == FrameChunk(2, 5)
    assert type(chunk.start) is int
    assert type(chunk.end) is int


def test_invalid_scene_cut_fails_closed():
    with pytest.raises(ValueError):
        plan_chunks(10, 5, (10,))


@pytest.mark.parametrize(
    ("frame_count", "max_frames", "scene_cuts"),
    [
        (10.5, 5, ()),
        (True, 5, ()),
        (10, 2.5, ()),
        (10, False, ()),
        (10, 5, (3.5,)),
        (10, 5, (True,)),
    ],
)
def test_chunk_planner_rejects_non_integer_frame_values(frame_count, max_frames, scene_cuts):
    with pytest.raises(ValueError):
        plan_chunks(frame_count, max_frames, scene_cuts)


@pytest.mark.parametrize("start,end", [(0.5, 2), (False, 2), (0, 2.5), (0, True)])
def test_frame_chunk_rejects_non_integer_boundaries(start, end):
    with pytest.raises(ValueError):
        FrameChunk(start, end)

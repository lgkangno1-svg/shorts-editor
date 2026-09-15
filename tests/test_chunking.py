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


def test_invalid_scene_cut_fails_closed():
    with pytest.raises(ValueError):
        plan_chunks(10, 5, (10,))

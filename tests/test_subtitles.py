import math
import numpy as np
import pytest

from shorts_editor.subtitles import OCRDetection, SubtitleConsensusConfig, best_subtitle_track, densify_track, detect_subtitle_tracks, refine_subtitle_track, temporal_union_track
from shorts_editor.tracks import BoundingBox, RemovalTrack, TargetKind, TrackSample


def det(frame,x,y,w,h,confidence=.9,text="hello"): return OCRDetection(frame,BoundingBox(x,y,w,h),confidence,text)

def test_temporal_consensus_prefers_centered_changing_subtitle_over_corner_label():
    detections=[]
    for frame,text in [(0,"hello"),(5,"world"),(10,"again"),(15,"bye")]: detections += [det(frame,.22,.79,.56,.07,.92,text),det(frame,.83,.73,.12,.05,.96,"SALE")]
    best=best_subtitle_track(detections); assert best is not None; assert best.track.samples[0].box.width>.5; assert best.text_change_ratio==1.0

def test_word_boxes_and_two_lines_fuse_into_one_caption_block():
    detections=[det(0,.25,.78,.18,.035,text="one"),det(0,.45,.78,.20,.035,text="two"),det(0,.30,.825,.40,.035,text="line two"),det(6,.24,.78,.42,.035,text="next"),det(6,.31,.825,.38,.035,text="caption")]
    best=best_subtitle_track(detections); assert best is not None; box=best.track.samples[0].box; assert box.y<.78 and box.height>.08 and box.width>.44

def test_persistent_same_text_subtitle_is_still_accepted():
    best=best_subtitle_track([det(0,.2,.8,.6,.06,text="same caption"),det(5,.2,.8,.6,.06,text="same caption"),det(10,.2,.8,.6,.06,text="same caption")]); assert best is not None and best.text_change_ratio==0

def test_single_frame_scene_text_is_rejected_by_support_gate(): assert detect_subtitle_tracks([det(0,.25,.7,.5,.08,text="sign")])==()

def test_default_supports_top_captions_and_config_can_exclude_them():
    ds=[det(0,.2,.055,.6,.05,text="a"),det(5,.2,.055,.6,.05,text="b")]; assert best_subtitle_track(ds) is not None; assert best_subtitle_track(ds,SubtitleConsensusConfig(min_center_y=.10)) is None

def test_real_fixture_style_top_title_and_changing_line_are_detectable():
    ds=[]
    for frame,text in [(0,"내 자리 보고 감격함"),(5,"자리에서 눈치 엄청 봄"),(10,"대답 거의 로봇임")]: ds += [det(frame,.13,.045,.30,.04,.94,"첫 출근 특징"),det(frame,.17,.095,.66,.05,.91,text)]
    best=best_subtitle_track(ds); assert best is not None; assert best.track.samples[0].box.y<.05 and best.track.samples[0].box.height>.08

def test_densify_fills_only_short_gaps():
    track=RemovalTrack("s",TargetKind.SUBTITLE,(TrackSample(0,BoundingBox(.2,.8,.5,.05),.9),TrackSample(3,BoundingBox(.22,.8,.5,.05),.8),TrackSample(10,BoundingBox(.3,.8,.5,.05),.9)))
    dense=densify_track(track,max_gap_frames=2); assert [s.frame_index for s in dense.samples]==[0,1,2,3,10]; assert dense.samples[1].confidence<.8

def test_temporal_union_expands_neighbour_jitter_but_stays_in_frame():
    track=RemovalTrack("s",TargetKind.SUBTITLE,(TrackSample(0,BoundingBox(.01,.8,.4,.05),.9),TrackSample(1,BoundingBox(.03,.79,.45,.06),.9)))
    refined=temporal_union_track(track,radius_frames=1,padding_x=.02,padding_y=.01); assert refined.samples[0].box.x==0 and refined.samples[0].box.width>=.49 and refined.samples[0].box.y>=0 and refined.samples[0].box.y+refined.samples[0].box.height<=1

def test_refine_densifies_then_unions_to_prevent_mask_flicker():
    track=RemovalTrack("s",TargetKind.SUBTITLE,(TrackSample(0,BoundingBox(.2,.8,.4,.05),.9),TrackSample(2,BoundingBox(.25,.79,.5,.06),.9)))
    refined=refine_subtitle_track(track,max_gap_frames=2,union_radius_frames=1,padding_x=0,padding_y=0); assert [s.frame_index for s in refined.samples]==[0,1,2]; assert refined.samples[1].box.x<=.2 and refined.samples[1].box.x+refined.samples[1].box.width>=.75

@pytest.mark.parametrize("value",[True,1.2,"3"])
def test_frame_index_type_safety(value):
    with pytest.raises((TypeError,ValueError)): OCRDetection(value,BoundingBox(.2,.8,.4,.05),.9)

@pytest.mark.parametrize("value",[math.nan,math.inf,-math.inf])
def test_confidence_non_finite_is_rejected(value):
    with pytest.raises(ValueError): OCRDetection(0,BoundingBox(.2,.8,.4,.05),value)

def test_numpy_scalar_ocr_values_are_accepted():
    detection=OCRDetection(np.int64(3),BoundingBox(.2,.8,.4,.05),np.float32(.9),"caption")
    assert detection.frame_index == 3
    assert float(detection.confidence) == pytest.approx(.9)

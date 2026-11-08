"""Unit tests for Video Deepfake and Temporal Consistency Forensics."""

import io
import pytest
import numpy as np
from PIL import Image
import imageio.v3 as iio
from aegistruth.core.video_forensics import extract_video_frames, compute_temporal_consistency, analyze_video

def _create_mock_video_bytes(num_frames=6, is_synthetic=False):
    frames = []
    for i in range(num_frames):
        arr = np.full((64, 64, 3), 50 + (i * 10), dtype=np.uint8)
        if is_synthetic and i % 2 == 1:
            arr[20:40, 20:40] = [255, 0, 0]  # Erratic flashing patch
        frames.append(arr)
            
    buf = io.BytesIO()
    iio.imwrite(buf, np.array(frames), extension=".gif", duration=100)
    return buf.getvalue()

def test_extract_video_frames():
    raw = _create_mock_video_bytes(num_frames=5)
    frames = extract_video_frames(raw)
    assert len(frames) == 5
    assert frames[0].shape == (64, 64, 3)

def test_compute_temporal_consistency():
    raw = _create_mock_video_bytes(num_frames=8, is_synthetic=True)
    frames = extract_video_frames(raw)
    metrics = compute_temporal_consistency(frames)
    assert "total_frames_analyzed" in metrics
    assert metrics["total_frames_analyzed"] == 8
    assert "temporal_flicker_score" in metrics
    assert "timeline_diffs" in metrics
    assert len(metrics["timeline_diffs"]) == 7

def test_analyze_video_pipeline():
    raw = _create_mock_video_bytes(num_frames=6, is_synthetic=False)
    results = analyze_video(raw)
    assert "verdict" in results
    assert results["verdict"] in ["AUTHENTIC_RECORDING", "SUSPICIOUS_TEMPORAL_ANOMALY", "LIKELY_DEEPFAKE_VIDEO"]
    assert "visualizations" in results
    assert "keyframe_thumbnail" in results["visualizations"]
    assert "metrics" in results

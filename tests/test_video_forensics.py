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

def test_analyze_video_empty_and_corrupt():
    # Empty bytes
    res_empty = analyze_video(b"")
    assert res_empty["verdict"] == "EMPTY_MEDIA_ASSET"
    assert res_empty["metrics"]["frames_analyzed"] == 0

    # Corrupt / random bytes
    res_corrupt = analyze_video(b"not a real video file random bytes 1234567890", filename="broken.mp4")
    assert res_corrupt["verdict"] == "UNRECOGNIZED_MEDIA_STREAM"
    assert res_corrupt["metrics"]["frames_analyzed"] == 0
    assert len(res_corrupt["forensic_reasons"]) > 0

def test_analyze_video_static_image_upload():
    # Single static PNG image dragged into video analyzer
    img = Image.new("RGB", (64, 64), color=(200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    res = analyze_video(png_bytes, filename="dragged_image.png")
    assert res["verdict"] in ["AUTHENTIC_RECORDING", "SUSPICIOUS_TEMPORAL_ANOMALY", "LIKELY_DEEPFAKE_VIDEO"]
    assert res["metrics"]["frames_analyzed"] == 1
    assert "Single static frame" in res["forensic_reasons"][0]


def test_analyze_video_camera_recording_authentic():
    # Simulate real camera video with continuous optical flow and CMOS sensor noise
    np.random.seed(42)
    scene = np.random.randint(60, 200, (128, 160, 3), dtype=np.uint8)
    sensor = np.random.normal(0, 3.0, (128, 160, 3))
    real_frames = []
    for i in range(10):
        f = np.roll(scene, i * 2, axis=1).astype(np.float64) + sensor + np.random.normal(0, 0.8, (128, 160, 3))
        real_frames.append(np.clip(f, 0, 255).astype(np.uint8))

    buf = io.BytesIO()
    iio.imwrite(buf, np.array(real_frames), extension=".mp4", fps=24)
    raw_video = buf.getvalue()

    res = analyze_video(raw_video, filename="VID_20261108_camera.mp4")
    assert res["verdict"] == "AUTHENTIC_RECORDING"
    assert res["synthetic_probability"] < 25.0
    assert any("continuous" in r.lower() or "camera" in r.lower() or "optical" in r.lower() for r in res["forensic_reasons"])


def test_analyze_video_samples_classification():
    from pathlib import Path
    samples_dir = Path("aegistruth/static/samples")
    real_gif = samples_dir / "sample_video_real.gif"
    fake_gif = samples_dir / "sample_video_deepfake.gif"

    if real_gif.exists():
        with open(real_gif, "rb") as f:
            res_real = analyze_video(f.read(), filename="sample_video_real.gif")
        assert res_real["verdict"] == "AUTHENTIC_RECORDING"
        assert res_real["synthetic_probability"] < 35.0

    if fake_gif.exists():
        with open(fake_gif, "rb") as f:
            res_fake = analyze_video(f.read(), filename="sample_video_deepfake.gif")
        assert res_fake["verdict"] == "LIKELY_DEEPFAKE_VIDEO"
        assert res_fake["synthetic_probability"] > 65.0

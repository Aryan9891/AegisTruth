"""
Tests for Universal Multi-Format Ingestion across Image, Video, Audio, and Documents.
"""
import io
import numpy as np
from PIL import Image
import soundfile as sf
import pytest

from aegistruth.core.image_forensics import analyze_image
from aegistruth.core.audio_forensics import decode_audio_bytes, analyze_audio
from aegistruth.core.video_forensics import extract_video_frames, analyze_video


def test_universal_image_formats():
    """Verify PNG, JPEG, CMYK JPEG, WEBP, BMP, and GIF are all ingested cleanly."""
    formats = [
        ("PNG", "RGB"),
        ("JPEG", "RGB"),
        ("JPEG", "CMYK"),
        ("WEBP", "RGB"),
        ("BMP", "RGB"),
        ("GIF", "P"),
    ]

    for fmt, mode in formats:
        img = Image.new(mode, (120, 120), color=(100, 150, 200) if mode != "CMYK" else (10, 20, 30, 0))
        buf = io.BytesIO()
        img.save(buf, format=fmt)
        img_bytes = buf.getvalue()

        result = analyze_image(img_bytes)
        assert "verdict" in result
        assert result["verdict"] in ["AUTHENTIC", "SUSPICIOUS_TAMPERED", "LIKELY_SYNTHETIC"]
        assert "visualizations" in result
        assert "ela" in result["visualizations"]


def test_universal_audio_formats():
    """Verify WAV, FLAC, and OGG formats are decoded and analyzed properly."""
    sample_rate = 16000
    duration = 0.5  # 0.5 seconds
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    # Sine wave tone
    audio_signal = 0.5 * np.sin(2 * np.pi * 440.0 * t).astype(np.float32)

    formats = ["WAV", "FLAC", "OGG"]
    for fmt in formats:
        buf = io.BytesIO()
        sf.write(buf, audio_signal, sample_rate, format=fmt)
        audio_bytes = buf.getvalue()

        decoded_signal, sr = decode_audio_bytes(audio_bytes)
        assert sr == sample_rate
        assert len(decoded_signal) > 0

        report = analyze_audio(audio_bytes)
        assert "verdict" in report
        assert report["verdict"] in ["AUTHENTIC_HUMAN", "SUSPICIOUS_PROCESSED", "LIKELY_VOICE_CLONE"]
        assert "visualizations" in report
        assert "spectrogram" in report["visualizations"]


def test_universal_animated_video_formats():
    """Verify multi-frame animated sequences (e.g. GIF/WebP) are parsed into video frames."""
    frames = [
        Image.new("RGB", (64, 64), color=(i * 20, 100, 200))
        for i in range(5)
    ]
    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0
    )
    video_bytes = buf.getvalue()

    extracted = extract_video_frames(video_bytes)
    assert len(extracted) >= 2

    report = analyze_video(video_bytes)
    assert "verdict" in report
    assert report["verdict"] in ["AUTHENTIC_RECORDING", "SUSPICIOUS_TEMPORAL_ANOMALY", "LIKELY_DEEPFAKE_VIDEO"]
    assert "metrics" in report
    assert report["metrics"]["frames_analyzed"] >= 2

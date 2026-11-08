"""Unit tests for Audio & Voice Clone Forensics."""

import wave
import pytest
import numpy as np
from aegistruth.core.audio_forensics import analyze_audio, decode_audio_bytes, compute_spectral_features, compute_pitch_jitter

def _generate_test_wav_bytes(duration=1.0, sr=22050, freq=220.0):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    wave_data = 0.5 * np.sin(2 * np.pi * freq * t)
    pcm = (wave_data * 32767).astype(np.int16)
    
    import io
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()

def test_decode_audio_bytes():
    raw_wav = _generate_test_wav_bytes(duration=0.5, sr=16000, freq=300.0)
    samples, sr = decode_audio_bytes(raw_wav)
    assert sr == 16000
    assert len(samples) == 8000
    assert np.max(np.abs(samples)) <= 1.0

def test_compute_spectral_features():
    samples = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 22050))
    res = compute_spectral_features(samples, 22050)
    assert "spectrogram_b64" in res
    assert res["spectrogram_b64"].startswith("data:image/png;base64,")
    assert res["centroid_mean"] > 0
    assert "high_band_ratio" in res

def test_compute_pitch_jitter():
    samples = np.sin(2 * np.pi * 150 * np.linspace(0, 1, 22050))
    jitter, shimmer, contour = compute_pitch_jitter(samples, 22050)
    assert jitter >= 0.0
    assert shimmer >= 0.0
    assert isinstance(contour, list)

def test_analyze_audio_pipeline():
    raw_wav = _generate_test_wav_bytes(duration=1.2, sr=22050, freq=180.0)
    results = analyze_audio(raw_wav)
    assert "verdict" in results
    assert results["verdict"] in ["AUTHENTIC_HUMAN", "SUSPICIOUS_PROCESSED", "LIKELY_VOICE_CLONE"]
    assert 0.0 <= results["synthetic_probability"] <= 100.0
    assert "visualizations" in results
    assert "spectrogram" in results["visualizations"]
    assert "waveform" in results["visualizations"]
    assert "metrics" in results


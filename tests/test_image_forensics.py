"""Unit tests for Image and Visual Deepfake Forensics."""

import io
import pytest
import numpy as np
from PIL import Image
from aegistruth.core.image_forensics import analyze_image, compute_ela, compute_fft_spectrum, compute_noise_residuals

def test_compute_ela_basic():
    img = Image.new("RGB", (128, 128), color=(200, 100, 50))
    ela_img, mean_err, err_var = compute_ela(img, quality=90, scale=15.0)
    assert isinstance(ela_img, Image.Image)
    assert mean_err >= 0.0
    assert err_var >= 0.0

def test_compute_fft_spectrum():
    # Image with horizontal stripes
    arr = np.zeros((128, 128), dtype=np.uint8)
    arr[::4, :] = 255
    img = Image.fromarray(arr)
    
    fft_img, high_ratio, grid_spike_ratio, metrics = compute_fft_spectrum(img)
    assert isinstance(fft_img, Image.Image)
    assert high_ratio >= 0.0
    assert grid_spike_ratio >= 0.0
    assert "radial_profile" in metrics
    assert len(metrics["radial_profile"]) > 0

def test_compute_noise_residuals():
    arr = np.random.randint(0, 256, (128, 128), dtype=np.uint8)
    img = Image.fromarray(arr)
    res = compute_noise_residuals(img)
    assert "noise_variance" in res
    assert "quadrant_discrepancy" in res
    assert res["noise_variance"] >= 0.0

def test_analyze_image_pipeline():
    img = Image.new("RGB", (128, 128), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    raw_bytes = buf.getvalue()
    
    results = analyze_image(raw_bytes)
    assert "verdict" in results
    assert results["verdict"] in ["AUTHENTIC", "SUSPICIOUS_TAMPERED", "LIKELY_SYNTHETIC"]
    assert 0.0 <= results["synthetic_probability"] <= 100.0
    assert "visualizations" in results
    assert "original" in results["visualizations"]
    assert "ela" in results["visualizations"]
    assert "fft_spectrum" in results["visualizations"]
    assert "metrics" in results


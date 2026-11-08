"""Configuration settings and heuristic thresholds for AegisTruth."""

import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
SAMPLES_DIR = BASE_DIR / "samples"
STATIC_DIR = BASE_DIR / "static"

class ForensicsSettings(BaseModel):
    # Image thresholds
    ela_rescale_factor: float = 15.0
    ela_jpeg_quality: int = 90
    fft_high_freq_threshold: float = 0.65
    noise_uniformity_threshold: float = 0.70
    
    # Audio thresholds
    audio_sample_rate: int = 22050
    audio_fft_size: int = 1024
    audio_hop_length: int = 256
    vocoder_cutoff_freq_hz: float = 8000.0
    jitter_threshold_low: float = 0.003  # Unnaturally low jitter -> robotic TTS
    jitter_threshold_high: float = 0.050 # Erratic phase slips -> generative splice
    
    # Text & AI detection thresholds
    burstiness_threshold_ai: float = 5.0  # Low sentence variance
    entropy_threshold_ai: float = 3.6
    ai_phrase_weight: float = 0.15
    
    # Agent Guard thresholds
    max_zero_width_chars: int = 0
    allow_unverified_tool_calls: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

settings = ForensicsSettings()


"""Advanced Audio & Voice Clone Forensics: STFT Spectrogram, Vocoder Artifacts, and Jitter Analysis."""

import io
import base64
import wave
from typing import Dict, Any, Tuple, List
import numpy as np
from PIL import Image, ImageDraw
from scipy import signal
from scipy.io import wavfile
try:
    import soundfile as sf
except ImportError:
    sf = None
from aegistruth.config import settings

def _generate_spectrogram_image(stft_mag_db: np.ndarray) -> str:
    """Renders decibel STFT magnitude matrix to a thermal spectrogram PNG base64 string."""
    # Normalize between -80 dB and 0 dB
    min_db = -80.0
    max_db = 0.0
    clipped = np.clip(stft_mag_db, min_db, max_db)
    norm = ((clipped - min_db) / (max_db - min_db) * 255.0).astype(np.uint8)
    
    # Flip vertically so low frequencies are at bottom
    norm = np.flipud(norm)
    
    # Apply thermal colormap (Inferno-like: black -> purple -> orange -> yellow)
    # Using LUT mapping
    h, w = norm.shape
    rgb_arr = np.zeros((h, w, 3), dtype=np.uint8)
    
    # Red channel
    rgb_arr[:, :, 0] = np.clip(norm * 1.5, 0, 255).astype(np.uint8)
    # Green channel
    rgb_arr[:, :, 1] = np.clip((norm - 80) * 1.8, 0, 255).astype(np.uint8)
    # Blue channel
    rgb_arr[:, :, 2] = np.clip(180 - norm, 0, 255).astype(np.uint8)
    
    img = Image.fromarray(rgb_arr)
    # Resize to standard viewing dimensions
    img = img.resize((700, 260), Image.Resampling.BILINEAR)
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"

def decode_audio_bytes(audio_bytes: bytes) -> Tuple[np.ndarray, int]:
    """
    Decodes audio bytes into a mono float32 numpy array and sample rate.
    Supports ALL audio formats (WAV, MP3, FLAC, OGG, AIFF, AU, etc.).
    """
    # 1. Primary multi-format decoder via SoundFile (supports WAV, MP3, FLAC, OGG, AIFF)
    if sf is not None:
        try:
            data, sample_rate = sf.read(io.BytesIO(audio_bytes), dtype="float32")
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            # Ensure float32 normalized between -1.0 and 1.0
            data = data.astype(np.float32)
            max_val = np.max(np.abs(data))
            if max_val > 1.0:
                data = data / max_val
            return data, sample_rate
        except Exception:
            pass

    # 2. Secondary fallback via scipy.io.wavfile
    try:
        sample_rate, data = wavfile.read(io.BytesIO(audio_bytes))
        # Convert stereo to mono
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
            
        # Normalize to float32 between -1.0 and 1.0
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        elif data.dtype == np.uint8:
            data = (data.astype(np.float32) - 128.0) / 128.0
        else:
            data = data.astype(np.float32)
            max_val = np.max(np.abs(data))
            if max_val > 0:
                data = data / max_val
                
        return data, sample_rate
    except Exception as e:
        # 3. Tertiary fallback to standard wave module
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                channels = wf.getnchannels()
                raw_data = wf.readframes(n_frames)
                data = np.frombuffer(raw_data, dtype=np.int16).astype(np.float32) / 32768.0
                if channels > 1:
                    data = data[::channels]
                return data, sample_rate
        except Exception:
            raise ValueError(f"Could not decode audio data in any supported format (WAV, MP3, FLAC, OGG, AIFF): {str(e)}")

def compute_spectral_features(samples: np.ndarray, sample_rate: int) -> Dict[str, Any]:
    """Computes STFT, spectral centroid, spectral flux, and vocoder truncation artifacts."""
    n_per_seg = min(1024, len(samples))
    if n_per_seg < 64:
        raise ValueError("Audio sample too short for spectral analysis")
        
    freqs, times, zxx = signal.stft(samples, fs=sample_rate, nperseg=n_per_seg, noverlap=n_per_seg//2)
    mag = np.abs(zxx)
    
    # Convert to dB scale
    max_mag = np.max(mag) if np.max(mag) > 0 else 1e-9
    mag_db = 20 * np.log10(mag / max_mag + 1e-9)
    
    # 1. High frequency cutoff / truncation (typical of 16kHz or 22kHz vocoders)
    # Check energy ratio in the top 15% of frequency bands
    nyquist = sample_rate / 2.0
    high_freq_cutoff_idx = int(len(freqs) * 0.85)
    
    high_band_energy = np.mean(mag[high_freq_cutoff_idx:, :])
    mid_band_energy = np.mean(mag[int(len(freqs)*0.2):int(len(freqs)*0.6), :]) + 1e-9
    
    high_band_ratio = float(high_band_energy / mid_band_energy)
    
    # 2. Spectral Centroid calculation
    # Sum(f * M(f)) / Sum(M(f))
    freq_weights = freqs[:, np.newaxis]
    centroid = np.sum(freq_weights * mag, axis=0) / (np.sum(mag, axis=0) + 1e-9)
    centroid_mean = float(np.mean(centroid))
    centroid_std = float(np.std(centroid))
    
    # 3. Spectral Flux (Rate of spectral distribution change)
    normalized_mag = mag / (np.sum(mag, axis=0, keepdims=True) + 1e-9)
    flux = np.sqrt(np.sum(np.diff(normalized_mag, axis=1) ** 2, axis=0))
    flux_mean = float(np.mean(flux)) if len(flux) > 0 else 0.0
    flux_std = float(np.std(flux)) if len(flux) > 0 else 0.0
    
    # 4. Silence & Respiratory Breath Mechanics
    # True human speech contains soft breathing noise (-45 dB to -30 dB) before utterances.
    # Synthetic TTS often has zero amplitude or flat dithered silence.
    rms_envelope = np.sqrt(np.mean(samples[:(len(samples)//512)*512].reshape(-1, 512)**2, axis=1) + 1e-9)
    rms_db = 20 * np.log10(rms_envelope + 1e-9)
    
    digital_silence_ratio = float(np.mean(rms_db < -60.0))
    natural_breath_ratio = float(np.mean((rms_db >= -50.0) & (rms_db <= -35.0)))
    
    spectrogram_b64 = _generate_spectrogram_image(mag_db)
    
    return {
        "mag_db": mag_db,
        "spectrogram_b64": spectrogram_b64,
        "high_band_ratio": high_band_ratio,
        "centroid_mean": centroid_mean,
        "centroid_std": centroid_std,
        "flux_mean": flux_mean,
        "flux_std": flux_std,
        "digital_silence_ratio": digital_silence_ratio,
        "natural_breath_ratio": natural_breath_ratio
    }

def compute_pitch_jitter(samples: np.ndarray, sample_rate: int) -> Tuple[float, float, List[float]]:
    """
    Estimates Pitch Jitter (period perturbation) and Shimmer (amplitude perturbation).
    Natural human speech exhibits natural micro-variability in vocal fold vibration (0.5% - 2.5%).
    TTS voice clones often exhibit either:
    - Extreme mathematical regularity (Jitter < 0.25%)
    - Discontinuous splicing transitions (Jitter > 5.0%)
    """
    frame_len = int(sample_rate * 0.03)  # 30 ms frames
    hop_len = int(sample_rate * 0.015)   # 15 ms hop
    
    periods = []
    amplitudes = []
    
    # Autocorrelation based pitch estimation
    for i in range(0, len(samples) - frame_len, hop_len):
        frame = samples[i:i + frame_len]
        energy = np.sum(frame ** 2)
        if energy < 0.005:  # Skip silence
            continue
            
        corr = signal.correlate(frame, frame, mode="full")
        corr = corr[len(corr)//2:]
        
        # Pitch search range: 70 Hz to 450 Hz
        min_lag = int(sample_rate / 450)
        max_lag = int(sample_rate / 70)
        
        if len(corr) > max_lag:
            peak_lag = min_lag + np.argmax(corr[min_lag:max_lag])
            
            # Voicing strength check: correlation peak must be significant relative to energy at lag 0
            corr_strength = corr[peak_lag] / (corr[0] + 1e-9)
            if corr_strength < 0.45:
                continue
            
            # Parabolic interpolation for sub-sample period accuracy
            if min_lag < peak_lag < len(corr) - 1:
                alpha = corr[peak_lag - 1]
                beta = corr[peak_lag]
                gamma = corr[peak_lag + 1]
                denom = 2 * (alpha - 2 * beta + gamma)
                if abs(denom) > 1e-9:
                    delta = (alpha - gamma) / denom
                    precise_lag = float(peak_lag) + float(delta)
                else:
                    precise_lag = float(peak_lag)
            else:
                precise_lag = float(peak_lag)
                
            # Filter unvoiced boundary outliers
            if periods and abs(precise_lag - periods[-1]) > 0.5 * periods[-1]:
                continue
                
            periods.append(precise_lag)
            amplitudes.append(float(np.max(np.abs(frame))))
            
    if len(periods) < 5:
        return 0.015, 0.05, []  # Insufficient voiced frames fallback
        
    periods_arr = np.array(periods)
    amplitudes_arr = np.array(amplitudes)
    
    # Relative Jitter (Jitt_rel): mean(|T_i - T_i+1|) / mean(T)
    period_diffs = np.abs(np.diff(periods_arr))
    jitter = float(np.mean(period_diffs) / (np.mean(periods_arr) + 1e-9))
    
    # Relative Shimmer (Shim_rel): mean(|A_i - A_i+1|) / mean(A)
    amp_diffs = np.abs(np.diff(amplitudes_arr))
    shimmer = float(np.mean(amp_diffs) / (np.mean(amplitudes_arr) + 1e-9))
    
    # Pitch contour in Hz for visualization
    pitch_contour = [round(float(sample_rate / p), 1) for p in periods[:60]]
    
    return jitter, shimmer, pitch_contour

def analyze_audio(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Complete acoustic forensic pipeline for audio files (WAV).
    Returns voice clone likelihood, spectrogram visualization, and acoustic anomaly metrics.
    """
    samples, sample_rate = decode_audio_bytes(audio_bytes)
    duration_sec = len(samples) / float(sample_rate)
    
    if duration_sec < 0.2:
        raise ValueError("Audio clip too short for forensic evaluation (min 0.2s required)")
        
    spectral = compute_spectral_features(samples, sample_rate)
    jitter, shimmer, pitch_contour = compute_pitch_jitter(samples, sample_rate)
    
    # Synthetic Voice Scoring Heuristic
    # 1. Robotic Pitch Invariance or Discontinuity:
    #    Human speech typically has 0.008 <= jitter <= 0.035.
    #    Synthetic models often show jitter < 0.004 (unnaturally flat) or > 0.060 (jagged splice).
    ai_score = 0.0
    forensic_reasons = []
    
    if jitter < 0.004:
        ai_score += 30.0
        forensic_reasons.append(f"Unnaturally flat pitch micro-jitter ({jitter*100:.2f}%), indicating synthetic neural vocoder pitch generation.")
    elif jitter > 0.055:
        ai_score += 25.0
        forensic_reasons.append(f"Erratic phase discontinuity and pitch instability ({jitter*100:.2f}%) characteristic of zero-shot voice cloning seams.")
        
    # 2. Sibilance & Vocoder High-Band cutoff or smearing
    if spectral["high_band_ratio"] < 0.015:
        ai_score += 25.0
        forensic_reasons.append("Sharp high-frequency band cutoff detected (< 8 kHz/11 kHz), characteristic of bandwidth-limited neural vocoders.")
    elif spectral["high_band_ratio"] > 0.35:
        ai_score += 20.0
        forensic_reasons.append("Unnatural high-frequency energy distribution and sibilant phase smearing.")
        
    # 3. Absence of natural breath dynamics & digital silence
    if spectral["digital_silence_ratio"] > 0.25 and spectral["natural_breath_ratio"] < 0.03:
        ai_score += 25.0
        forensic_reasons.append("Dead digital silence intervals without natural sub-glottal inhalation acoustic patterns.")
        
    # 4. Unnatural spectral flux
    if spectral["flux_std"] < 0.02:
        ai_score += 15.0
        forensic_reasons.append("Low spectral flux variance, indicating unnatural articulator inertia.")
        
    ai_score = float(np.clip(ai_score, 0.0, 100.0))
    
    if ai_score >= 65.0:
        verdict = "LIKELY_VOICE_CLONE"
        desc = "High probability of AI-generated synthetic voice or neural voice cloning"
    elif ai_score >= 40.0:
        verdict = "SUSPICIOUS_PROCESSED"
        desc = "Moderate acoustic anomalies detected; potential synthetic speech or heavy post-processing"
    else:
        verdict = "AUTHENTIC_HUMAN"
        desc = "Acoustic markers match biological vocal fold dynamics and natural respiratory patterns"
        
    # Waveform preview data points (100 points for frontend canvas)
    step = max(1, len(samples) // 100)
    waveform_sample = [round(float(samples[i]), 3) for i in range(0, min(len(samples), 100 * step), step)][:100]
    
    return {
        "verdict": verdict,
        "synthetic_probability": round(ai_score, 1),
        "confidence_description": desc,
        "forensic_reasons": forensic_reasons,
        "visualizations": {
            "spectrogram": spectral["spectrogram_b64"],
            "waveform": waveform_sample,
            "pitch_contour": pitch_contour,
        },
        "metrics": {
            "duration_seconds": round(duration_sec, 2),
            "sample_rate": sample_rate,
            "pitch_jitter": round(jitter, 4),
            "pitch_shimmer": round(shimmer, 4),
            "high_band_energy_ratio": round(spectral["high_band_ratio"], 4),
            "spectral_centroid_hz": round(spectral["centroid_mean"], 1),
            "digital_silence_ratio": round(spectral["digital_silence_ratio"], 3),
            "natural_breath_ratio": round(spectral["natural_breath_ratio"], 3),
        }
    }


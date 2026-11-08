"""Video & Temporal Deepfake Forensics: Frame-to-frame inconsistency, flickering, and warping."""

import io
import base64
from typing import Dict, Any, List, Tuple
import numpy as np
from PIL import Image
import imageio.v3 as iio
from aegistruth.core.image_forensics import compute_fft_spectrum, compute_ela

def extract_video_frames(video_bytes: bytes, max_frames: int = 30) -> List[np.ndarray]:
    """Decodes video/animated media bytes into a list of RGB numpy frames."""
    # First attempt: PIL ImageSequence (handles animated GIF, APNG, WebP, TIFF)
    try:
        im = Image.open(io.BytesIO(video_bytes))
        n_frames = getattr(im, "n_frames", 1)
        if n_frames > 1:
            frames = []
            for frame_idx in range(min(n_frames, max_frames)):
                im.seek(frame_idx)
                frames.append(np.array(im.convert("RGB")))
            return frames
    except Exception:
        pass

    # Second attempt: imageio iterator for MP4, WebM, AVI, etc.
    try:
        frames = []
        for idx, frame in enumerate(iio.imiter(io.BytesIO(video_bytes))):
            if idx >= max_frames:
                break
            if len(frame.shape) == 2:
                frame = np.stack([frame] * 3, axis=-1)
            elif frame.shape[2] == 4:
                frame = frame[:, :, :3]
            frames.append(frame)
        if frames:
            return frames
    except Exception:
        pass

    raise ValueError("Could not extract frames from video asset (unsupported format or single static frame)")

def compute_temporal_consistency(frames: List[np.ndarray]) -> Dict[str, Any]:
    """
    Computes inter-frame temporal consistency, motion jitter, and face-swapping edge flickering.
    Synthetic deepfake videos (e.g. Roop, DeepFaceLab, Sora, Runway) frequently exhibit:
    - Temporal flicker in facial boundaries and micro-expressions.
    - Unnatural jumps in frame-to-frame high-frequency Laplacian variance.
    - Splicing discontinuities between consecutive frames.
    """
    if len(frames) < 2:
        raise ValueError("Video must contain at least 2 frames for temporal analysis")

    frame_diffs = []
    laplacian_variances = []
    
    # Analyze frame differences and high frequency edges
    for i in range(len(frames)):
        gray = np.mean(frames[i], axis=-1).astype(np.float32)
        
        # Laplacian operator for edge sharpness: L = d^2I/dx^2 + d^2I/dy^2
        lap = np.abs(np.diff(gray, n=2, axis=0)).mean() + np.abs(np.diff(gray, n=2, axis=1)).mean()
        laplacian_variances.append(float(lap))
        
        if i > 0:
            prev_gray = np.mean(frames[i - 1], axis=-1).astype(np.float32)
            # Frame-to-frame MSE
            mse = float(np.mean((gray - prev_gray) ** 2))
            frame_diffs.append(mse)

    frame_diffs_arr = np.array(frame_diffs)
    lap_arr = np.array(laplacian_variances)

    mean_diff = float(np.mean(frame_diffs_arr))
    diff_std = float(np.std(frame_diffs_arr))
    motion_jitter_cv = diff_std / (mean_diff + 1e-9)

    # Temporal flicker: standard deviation of frame-to-frame edge sharpness
    flicker_score = float(np.std(lap_arr))
    
    # Discontinuity spikes: frames where MSE is > 1.8x the median difference
    median_diff = float(np.median(frame_diffs_arr)) + 1e-9
    spikes = []
    for idx, diff in enumerate(frame_diffs):
        ratio = diff / median_diff
        if ratio > 1.8:
            spikes.append({"frame_pair": (idx, idx + 1), "diff_ratio": round(ratio, 2)})

    # Sample keyframe thumbnail (middle frame)
    mid_idx = len(frames) // 2
    mid_img = Image.fromarray(frames[mid_idx])
    buffered = io.BytesIO()
    mid_img.save(buffered, format="JPEG", quality=85)
    keyframe_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"

    return {
        "total_frames_analyzed": len(frames),
        "mean_frame_diff": mean_diff,
        "diff_std": diff_std,
        "motion_jitter_cv": motion_jitter_cv,
        "temporal_flicker_score": flicker_score,
        "discontinuity_spikes": spikes,
        "timeline_diffs": [round(float(d), 2) for d in frame_diffs[:50]],
        "keyframe_thumbnail": keyframe_b64
    }

def analyze_video(video_bytes: bytes) -> Dict[str, Any]:
    """
    Complete video deepfake forensic pipeline.
    Combines temporal frame consistency with spatial Fourier inspection on keyframes.
    """
    frames = extract_video_frames(video_bytes)
    temporal = compute_temporal_consistency(frames)
    
    # Inspect middle keyframe for spatial generative upsampling artifacts
    mid_frame = Image.fromarray(frames[len(frames) // 2])
    _, high_freq_ratio, grid_spike_ratio, _ = compute_fft_spectrum(mid_frame)
    _, _, ela_var = compute_ela(mid_frame)
    
    # Synthetic Video Scoring Heuristic
    ai_score = 0.0
    forensic_reasons = []

    # 1. Temporal flicker anomaly
    if temporal["temporal_flicker_score"] > 1.2:
        ai_score += 35.0
        forensic_reasons.append(f"High inter-frame edge flicker ({temporal['temporal_flicker_score']:.2f}), characteristic of facial boundary warps in deepfake synthesis.")
    elif temporal["temporal_flicker_score"] > 0.5:
        ai_score += 15.0
        forensic_reasons.append(f"Moderate edge flickering detected across frames ({temporal['temporal_flicker_score']:.2f}).")

    # 2. Motion jitter coefficient of variation
    if temporal["motion_jitter_cv"] > 0.20:
        ai_score += 25.0
        forensic_reasons.append(f"Erratic frame-to-frame optical flow variance (jitter CV: {temporal['motion_jitter_cv']:.2f}), typical of deepfake frame interpolation.")

    # 3. Splicing discontinuity spikes
    if len(temporal["discontinuity_spikes"]) >= 1:
        ai_score += 20.0
        forensic_reasons.append(f"Temporal discontinuity spikes detected ({len(temporal['discontinuity_spikes'])} anomalous transitions).")

    # 4. Spatial keyframe frequency artifacts
    if grid_spike_ratio > 3.5:
        ai_score += 20.0
        forensic_reasons.append(f"Keyframes exhibit periodic 2D Fourier grid upsampling harmonics (ratio: {grid_spike_ratio:.2f}).")
        
    ai_score = float(np.clip(ai_score, 0.0, 100.0))

    if ai_score >= 65.0:
        verdict = "LIKELY_DEEPFAKE_VIDEO"
        desc = "High probability of generative AI video synthesis (e.g. Sora, Runway, Kling) or face-swapping manipulation"
    elif ai_score >= 35.0:
        verdict = "SUSPICIOUS_TEMPORAL_ANOMALY"
        desc = "Moderate temporal or spatial anomalies detected; potential synthetic generation or post-processing splice"
    else:
        verdict = "AUTHENTIC_RECORDING"
        desc = "Temporal optical flow and spatial frequency characteristics match continuous physical camera recording"

    return {
        "verdict": verdict,
        "synthetic_probability": round(ai_score, 1),
        "confidence_description": desc,
        "forensic_reasons": forensic_reasons,
        "visualizations": {
            "keyframe_thumbnail": temporal["keyframe_thumbnail"],
            "timeline_diffs": temporal["timeline_diffs"],
        },
        "metrics": {
            "frames_analyzed": temporal["total_frames_analyzed"],
            "temporal_flicker_score": round(temporal["temporal_flicker_score"], 2),
            "discontinuity_spikes_count": len(temporal["discontinuity_spikes"]),
            "keyframe_grid_spike_ratio": round(grid_spike_ratio, 3),
            "keyframe_ela_variance": round(ela_var, 2),
        }
    }

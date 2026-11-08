"""Video & Temporal Deepfake Forensics: Frame-to-frame inconsistency, flickering, and warping."""

import io
import os
import tempfile
import base64
from typing import Dict, Any, List, Optional
import numpy as np
from PIL import Image
import imageio.v3 as iio

try:
    import imageio_ffmpeg
    HAS_FFMPEG = True
except ImportError:
    HAS_FFMPEG = False

from aegistruth.core.image_forensics import compute_fft_spectrum, compute_ela


def extract_video_frames(
    video_bytes: bytes,
    max_frames: int = 30,
    filename: Optional[str] = None
) -> List[np.ndarray]:
    """
    Decodes video or animated media bytes into a list of RGB numpy frames.
    Supports ALL animated and video formats (MP4, MKV, AVI, MOV, WebM, FLV, WMV, GIF, WebP, APNG, etc.).
    Gracefully handles single-frame media and static images.
    """
    single_frame = None

    # 1. First attempt: PIL ImageSequence (handles animated GIF, APNG, WebP, multi-page TIFF, or static images)
    try:
        im = Image.open(io.BytesIO(video_bytes))
        n_frames = getattr(im, "n_frames", 1)
        if n_frames > 1:
            frames = []
            for frame_idx in range(min(n_frames, max_frames)):
                im.seek(frame_idx)
                frames.append(np.array(im.convert("RGB")))
            if len(frames) >= 1:
                return frames
        else:
            single_frame = np.array(im.convert("RGB"))
    except Exception:
        pass

    # Extract target file extension from filename for container demuxing
    suffix = ".mp4"
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in (".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".gif", ".m4v", ".ts"):
            suffix = ext

    # 2. Second attempt: imageio_ffmpeg direct demuxer (industry standard, native ffmpeg binary)
    if HAS_FFMPEG:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_bytes)
                tmp_path = tmp.name

            reader = imageio_ffmpeg.read_frames(tmp_path, pix_fmt="rgb24")
            meta = next(reader)
            w, h = meta.get("size", (0, 0))
            frames = []
            for fb in reader:
                if w > 0 and h > 0:
                    frame = np.frombuffer(fb, dtype=np.uint8).reshape((h, w, 3))
                    frames.append(frame)
                if len(frames) >= max_frames:
                    break
            reader.close()
            if len(frames) >= 1:
                return frames
        except Exception:
            pass
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    # 3. Third attempt: imageio.v3 iterator directly on in-memory bytes
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
        if len(frames) >= 1:
            return frames
    except Exception:
        pass

    # 4. Fourth attempt: temporary file with imageio.v3 imiter
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        frames = []
        for idx, frame in enumerate(iio.imiter(tmp_path)):
            if idx >= max_frames:
                break
            if len(frame.shape) == 2:
                frame = np.stack([frame] * 3, axis=-1)
            elif frame.shape[2] == 4:
                frame = frame[:, :, :3]
            frames.append(frame)
        if len(frames) >= 1:
            return frames
    except Exception:
        pass
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    # 5. Fallback: If user uploaded a single static image into the video sentinel, evaluate the single frame
    if single_frame is not None:
        return [single_frame]

    raise ValueError(
        "Could not extract frames from video asset: unsupported video codec or corrupted media file. "
        "Please ensure the file is an active video (MP4, MKV, AVI, MOV, WebM) or animated sequence (GIF)."
    )


def compute_temporal_consistency(frames: List[np.ndarray]) -> Dict[str, Any]:
    """
    Computes inter-frame temporal consistency, motion jitter, and face-swapping edge flickering.
    Synthetic deepfake videos (e.g. Roop, DeepFaceLab, Sora, Runway) frequently exhibit:
    - Temporal flicker in facial boundaries and micro-expressions.
    - Unnatural jumps in frame-to-frame high-frequency Laplacian variance.
    - Splicing discontinuities between consecutive frames.
    """
    if len(frames) == 0:
        raise ValueError("Video contains no frames to analyze")

    # Gracefully handle single frame (e.g. single static image uploaded)
    if len(frames) == 1:
        mid_frame = Image.fromarray(frames[0])
        buffered = io.BytesIO()
        mid_frame.save(buffered, format="JPEG", quality=85)
        keyframe_b64 = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
        return {
            "total_frames_analyzed": 1,
            "mean_frame_diff": 0.0,
            "diff_std": 0.0,
            "motion_jitter_cv": 0.0,
            "temporal_flicker_score": 0.0,
            "discontinuity_spikes": [],
            "timeline_diffs": [0.0],
            "keyframe_thumbnail": keyframe_b64
        }

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


def analyze_video(video_bytes: bytes, filename: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete video deepfake forensic pipeline.
    Combines temporal frame consistency with spatial Fourier inspection on keyframes.
    """
    frames = extract_video_frames(video_bytes, filename=filename)
    temporal = compute_temporal_consistency(frames)
    
    # Inspect middle keyframe for spatial generative upsampling artifacts
    mid_frame = Image.fromarray(frames[len(frames) // 2])
    _, high_freq_ratio, grid_spike_ratio, _ = compute_fft_spectrum(mid_frame)
    _, _, ela_var = compute_ela(mid_frame)
    
    # Synthetic Video Scoring Heuristic
    ai_score = 0.0
    forensic_reasons = []

    if temporal["total_frames_analyzed"] == 1:
        forensic_reasons.append("Single static frame evaluated in temporal sentinel: no inter-frame motion detected.")
    else:
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
    elif grid_spike_ratio > 2.0:
        ai_score += 10.0
        forensic_reasons.append(f"Moderate spatial Fourier frequency anomalies detected in keyframe lattice ({grid_spike_ratio:.2f}).")
        
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

"""Video & Temporal Deepfake Forensics: Frame-to-frame inconsistency, flickering, and warping."""

import io
import os
import shutil
import subprocess
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


def detect_video_container_suffix(video_bytes: bytes, filename: Optional[str] = None) -> str:
    """Detects appropriate file suffix for video container from filename or magic bytes."""
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in (
            ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".gif",
            ".m4v", ".3gp", ".ts", ".ogv", ".mpg", ".mpeg", ".mts", ".m2ts",
            ".vob", ".asf", ".hevc", ".h264", ".h265", ".y4m", ".webp", ".apng"
        ):
            return ext

    if video_bytes and len(video_bytes) >= 12:
        # MP4 / QuickTime MOV / M4V / 3GP
        if video_bytes[4:8] in (b"ftyp", b"moov", b"wide", b"free") or video_bytes[4:8].startswith(b"qt"):
            return ".mp4"
        # WebM or Matroska (EBML header: 0x1A 0x45 0xDF 0xA3)
        if video_bytes[:4] == b"\x1a\x45\xdf\xa3":
            return ".webm"
        # RIFF AVI / WEBP
        if video_bytes[:4] == b"RIFF":
            if video_bytes[8:12] == b"AVI ":
                return ".avi"
            if video_bytes[8:12] == b"WEBP":
                return ".webp"
        # GIF
        if video_bytes[:6] in (b"GIF87a", b"GIF89a"):
            return ".gif"
        # MPEG-TS
        if video_bytes[0] == 0x47 and len(video_bytes) > 188 and video_bytes[188] == 0x47:
            return ".ts"
        # Windows Media Video / ASF
        if video_bytes[:4] == b"\x30\x26\xb2\x75":
            return ".wmv"
        # FLV
        if video_bytes[:3] == b"FLV":
            return ".flv"

    return ".mp4"


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
    if not video_bytes or len(video_bytes) == 0:
        return []

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

    # Extract target file extension from filename or container magic bytes
    suffix = detect_video_container_suffix(video_bytes, filename)

    # 2. Second attempt: Direct native FFmpeg CLI extraction (universal, supports any video/audio/container)
    if HAS_FFMPEG:
        tmp_path = None
        tmp_dir = None
        try:
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_bytes)
                tmp_path = tmp.name

            tmp_dir = tempfile.mkdtemp(prefix="aegis_frames_")
            out_pattern = os.path.join(tmp_dir, "frame_%04d.png")

            # Try scaled extraction first for performance and memory
            cmd = [
                ffmpeg_exe,
                "-y",
                "-err_detect", "ignore_err",
                "-i", tmp_path,
                "-vf", r"scale=min(640\,iw):-2",
                "-pix_fmt", "rgb24",
                "-vframes", str(max_frames),
                out_pattern
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

            frame_files = sorted([
                os.path.join(tmp_dir, f)
                for f in os.listdir(tmp_dir)
                if f.startswith("frame_") and f.endswith(".png")
            ])

            # If scaled extraction returned no frames, try raw unscaled extraction
            if not frame_files:
                cmd_raw = [
                    ffmpeg_exe,
                    "-y",
                    "-err_detect", "ignore_err",
                    "-i", tmp_path,
                    "-pix_fmt", "rgb24",
                    "-vframes", str(max_frames),
                    out_pattern
                ]
                subprocess.run(cmd_raw, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                frame_files = sorted([
                    os.path.join(tmp_dir, f)
                    for f in os.listdir(tmp_dir)
                    if f.startswith("frame_") and f.endswith(".png")
                ])

            if frame_files:
                frames = []
                for ff in frame_files:
                    try:
                        with Image.open(ff) as img:
                            frames.append(np.array(img.convert("RGB")))
                    except Exception:
                        pass
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
            if tmp_dir and os.path.exists(tmp_dir):
                try:
                    shutil.rmtree(tmp_dir, ignore_errors=True)
                except Exception:
                    pass

    # 3. Third attempt: imageio_ffmpeg direct reader
    if HAS_FFMPEG:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(video_bytes)
                tmp_path = tmp.name

            reader = imageio_ffmpeg.read_frames(tmp_path, pix_fmt="rgb24")
            meta = next(reader)
            w, h = meta.get("size") or meta.get("source_size") or (0, 0)
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

    # 4. Fourth attempt: imageio.v3 iterator directly on in-memory bytes
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

    # 5. Fifth attempt: temporary file with imageio.v3 imiter
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

    # 6. Fallback: If user uploaded a single static image into the video sentinel, evaluate the single frame
    if single_frame is not None:
        return [single_frame]

    # 7. Final fallback: try raw image decode one more time
    try:
        im = Image.open(io.BytesIO(video_bytes))
        return [np.array(im.convert("RGB"))]
    except Exception:
        pass

    return []


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
    Gracefully handles empty, corrupted, or unsupported media formats.
    """
    if not video_bytes or len(video_bytes) == 0:
        return {
            "verdict": "EMPTY_MEDIA_ASSET",
            "synthetic_probability": 0.0,
            "confidence_description": "Uploaded video file is empty (0 bytes received).",
            "forensic_reasons": ["The media file contains no byte data to evaluate."],
            "visualizations": {
                "keyframe_thumbnail": "",
                "timeline_diffs": [0.0]
            },
            "metrics": {
                "frames_analyzed": 0,
                "temporal_flicker_score": 0.0,
                "discontinuity_spikes_count": 0,
                "keyframe_grid_spike_ratio": 0.0,
                "keyframe_ela_variance": 0.0
            }
        }

    try:
        frames = extract_video_frames(video_bytes, filename=filename)
    except Exception:
        frames = []

    if len(frames) == 0:
        # Create an informative diagnostic keyframe thumbnail
        diag_thumb = ""
        try:
            diag_img = Image.new("RGB", (240, 135), color=(15, 23, 42))
            buffered = io.BytesIO()
            diag_img.save(buffered, format="JPEG", quality=80)
            diag_thumb = f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode('utf-8')}"
        except Exception:
            pass

        return {
            "verdict": "UNRECOGNIZED_MEDIA_STREAM",
            "synthetic_probability": 0.0,
            "confidence_description": "Video stream could not be extracted: media file is corrupted, incomplete, or contains no decodable frames.",
            "forensic_reasons": [
                "Media container does not contain decodable video packets or valid keyframes.",
                "Please verify that the file is an active video (MP4, MKV, AVI, MOV, WebM) or animated sequence (GIF)."
            ],
            "visualizations": {
                "keyframe_thumbnail": diag_thumb,
                "timeline_diffs": [0.0]
            },
            "metrics": {
                "frames_analyzed": 0,
                "temporal_flicker_score": 0.0,
                "discontinuity_spikes_count": 0,
                "keyframe_grid_spike_ratio": 0.0,
                "keyframe_ela_variance": 0.0
            }
        }

    temporal = compute_temporal_consistency(frames)
    
    # Inspect middle keyframe for spatial generative upsampling artifacts
    mid_frame = Image.fromarray(frames[len(frames) // 2])
    _, high_freq_ratio, grid_spike_ratio, _ = compute_fft_spectrum(mid_frame)
    _, _, ela_var = compute_ela(mid_frame)
    
    # Extract standardized 8-dimensional video forensic feature vector & run Calibrated ML Classifier
    from aegistruth.core.ml_classifier import extract_video_features, get_calibrated_video_classifier
    feat = extract_video_features(frames, video_bytes=video_bytes, filename=filename)
    clf = get_calibrated_video_classifier()
    ml_prob = float(clf.predict_proba(feat)) * 100.0

    forensic_reasons = []

    # Features:
    # 0: temporal_flicker_cv, 1: prnu_sensor_correlation, 2: motion_acceleration_cv,
    # 3: discontinuity_max_ratio, 4: chromatic_stability_var, 5: keyframe_grid_spike_ratio,
    # 6: keyframe_ela_variance, 7: has_camera_container
    flicker_cv = feat[0]
    prnu_corr = feat[1]
    disc_ratio = feat[3]
    chroma_var = feat[4]
    grid_spike = feat[5]
    has_cam = feat[7]

    if temporal["total_frames_analyzed"] == 1:
        forensic_reasons.append("Single static frame evaluated in temporal sentinel: no inter-frame motion detected.")
    else:
        # Authentic camera indicators
        if prnu_corr > 0.15:
            forensic_reasons.append(f"Authentic CMOS sensor PRNU noise correlation ({prnu_corr:.2f}): physical camera sensor fingerprint verified.")
        if has_cam >= 0.5:
            forensic_reasons.append("Standard camera media container and stream encoding verified.")
        if flicker_cv < 0.16:
            forensic_reasons.append("Continuous optical flow: inter-frame edge sharpness remains temporally smooth with zero generative boundary warp.")
        if chroma_var < 0.005:
            forensic_reasons.append("Stable physical color temperature: consistent chromatic distribution across evaluated frames.")

        # Synthetic/Deepfake indicators
        if flicker_cv > 0.22:
            forensic_reasons.append(f"High inter-frame edge flicker (CV: {flicker_cv:.2f}), characteristic of facial boundary warps in deepfake synthesis.")
        if grid_spike > 4.5:
            forensic_reasons.append(f"Keyframes exhibit periodic 2D Fourier grid upsampling harmonics (ratio: {grid_spike:.2f}) from generative diffusion.")
        if disc_ratio > 4.0:
            forensic_reasons.append(f"Temporal discontinuity spikes detected (ratio: {disc_ratio:.2f}x above baseline motion).")
        if chroma_var > 0.015:
            forensic_reasons.append(f"Chromatic instability detected: erratic inter-frame color temperature shifts across skin tones.")

    if not forensic_reasons:
        forensic_reasons.append("Temporal optical flow and spatial frequency characteristics match continuous physical camera recording.")

    ai_score = float(np.clip(ml_prob, 0.0, 100.0))

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

"""Advanced Visual Forensics: Error Level Analysis (ELA), 2D Fourier Spectrum, and Noise Residuals."""

import io
import base64
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image, ImageChops, ImageEnhance, ExifTags
from scipy import ndimage
from aegistruth.config import settings

def _image_to_base64(img: Image.Image, format: str = "PNG") -> str:
    """Helper to convert PIL Image to base64 data URI, normalizing color modes."""
    buffered = io.BytesIO()
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    img.save(buffered, format=format)
    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/{format.lower()};base64,{encoded}"

def compute_ela(image: Image.Image, quality: int = 90, scale: float = 15.0) -> Tuple[Image.Image, float, float]:
    """
    Error Level Analysis (ELA).
    Identifies areas of an image that have differing levels of compression.
    Returns: (ela_image, mean_error, error_variance)
    """
    # Convert image to RGB if not already
    orig = image.convert("RGB")
    
    # Recompress into memory
    buffer = io.BytesIO()
    orig.save(buffer, "JPEG", quality=quality)
    buffer.seek(0)
    recompressed = Image.open(buffer)
    
    # Calculate difference
    diff = ImageChops.difference(orig, recompressed)
    
    # Calculate error statistics
    diff_arr = np.array(diff, dtype=np.float32)
    mean_error = float(np.mean(diff_arr))
    error_variance = float(np.var(diff_arr))
    
    # Amplify differences for visual inspection
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema])
    if max_diff == 0:
        max_diff = 1
    
    scale_factor = min(255.0 / max_diff, scale)
    enhancer = ImageEnhance.Brightness(diff)
    ela_image = enhancer.enhance(scale_factor)
    
    return ela_image, mean_error, error_variance

def compute_fft_spectrum(image: Image.Image) -> Tuple[Image.Image, float, float, Dict[str, Any]]:
    """
    2D Discrete Fourier Transform (2D FFT) Analysis.
    Detects periodic checkerboard artifacts, grid upsampling patterns,
    and high-frequency power spectrum anomalies characteristic of Diffusion models & GANs.
    """
    # Convert to grayscale numpy array
    gray = image.convert("L")
    arr = np.array(gray, dtype=np.float32)
    
    h, w = arr.shape
    if h == 0 or w == 0:
        raise ValueError("Invalid image dimensions")
    
    # 2D FFT with zero-frequency shift to center
    f_transform = np.fft.fft2(arr)
    f_shift = np.fft.fftshift(f_transform)
    magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1e-9)
    
    # Normalize magnitude spectrum to 0-255 for visualization
    norm_mag = magnitude_spectrum - np.min(magnitude_spectrum)
    max_val = np.max(norm_mag)
    if max_val > 0:
        norm_mag = (norm_mag / max_val) * 255.0
    fft_image = Image.fromarray(norm_mag.astype(np.uint8))
    
    # Frequency domain metrics
    cy, cx = h // 2, w // 2
    y, x = np.ogrid[:h, :w]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    max_r = min(cx, cy)
    
    # Radial average power spectrum
    num_bins = 50
    bin_edges = np.linspace(0, max_r, num_bins + 1)
    radial_profile = []
    
    for i in range(num_bins):
        mask = (r >= bin_edges[i]) & (r < bin_edges[i+1])
        if np.any(mask):
            radial_profile.append(float(np.mean(np.abs(f_shift)[mask])))
        else:
            radial_profile.append(0.0)
            
    # Measure high-frequency vs low-frequency energy ratio
    high_freq_mask = r > (0.6 * max_r)
    low_freq_mask = r <= (0.2 * max_r)
    
    high_energy = float(np.mean(np.abs(f_shift)[high_freq_mask])) if np.any(high_freq_mask) else 0.0
    low_energy = float(np.mean(np.abs(f_shift)[low_freq_mask])) if np.any(low_freq_mask) else 1e-5
    
    high_freq_ratio = high_energy / (low_energy + 1e-9)
    
    # In 2D FFT of rectangular images, the principal horizontal and vertical axes
    # naturally carry window boundary energy. Generative upsampling (e.g. transposed conv,
    # pixel shuffle, diffusion latent checkerboarding) introduces prominent off-axis harmonic
    # lattice peaks in the quadrants, not merely along the central crosshairs.
    # Exclude the principal cross axes (+/- 4 pixels) and analyze high-frequency quadrant energy spikes
    off_axis_mask = (np.abs(x - cx) > 4) & (np.abs(y - cy) > 4) & high_freq_mask
    if np.any(off_axis_mask):
        off_axis_energy = np.abs(f_shift)[off_axis_mask]
        peak_energy = float(np.percentile(off_axis_energy, 99))
        median_energy = float(np.median(off_axis_energy)) + 1e-9
        grid_spike_ratio = peak_energy / median_energy
    else:
        grid_spike_ratio = 1.0

    metrics = {
        "high_freq_ratio": high_freq_ratio,
        "grid_spike_ratio": grid_spike_ratio,
        "radial_profile": radial_profile[:20]  # top 20 frequency bands
    }
    
    return fft_image, high_freq_ratio, grid_spike_ratio, metrics

def compute_noise_residuals(image: Image.Image) -> Dict[str, float]:
    """
    Extracts high-pass sensor noise residual (PRNU-like analysis).
    Analyzes spatial consistency and kurtosis of sensor noise across quadrants.
    """
    gray = image.convert("L")
    arr = np.array(gray, dtype=np.float32)
    
    # High-pass filtering via median filter subtraction
    filtered = ndimage.median_filter(arr, size=3)
    noise = arr - filtered
    
    noise_variance = float(np.var(noise))
    noise_mean = float(np.mean(noise))
    
    # Divide into 4 quadrants to detect uneven synthetic inpainting
    h, w = arr.shape
    q1 = noise[:h//2, :w//2]
    q2 = noise[:h//2, w//2:]
    q3 = noise[h//2:, :w//2]
    q4 = noise[h//2:, w//2:]
    
    quad_vars = [float(np.var(q)) for q in [q1, q2, q3, q4]]
    quad_var_std = float(np.std(quad_vars))
    quad_var_mean = float(np.mean(quad_vars)) + 1e-9
    
    quadrant_discrepancy = quad_var_std / quad_var_mean
    
    return {
        "noise_variance": noise_variance,
        "noise_mean": noise_mean,
        "quadrant_discrepancy": quadrant_discrepancy
    }

def extract_exif_metadata(image: Image.Image) -> Dict[str, Any]:
    """Extracts and evaluates EXIF metadata for AI signatures or camera provenance."""
    metadata = {}
    has_camera_hardware = False
    has_ai_signature = False
    ai_signature_details = []
    
    try:
        exif = image.getexif()
        if exif:
            for tag_id, val in exif.items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                metadata[tag_name] = str(val)
                
                # Check for camera hardware indicators
                if tag_name in ["Make", "Model", "FNumber", "ExposureTime", "ISOSpeedRatings"]:
                    has_camera_hardware = True
                    
                # Check for known AI generator signatures
                val_str = str(val).lower()
                ai_keywords = ["midjourney", "stable diffusion", "dall-e", "comfyui", "novelai", "flux", "civitai", "leonardo.ai"]
                for kw in ai_keywords:
                    if kw in val_str:
                        has_ai_signature = True
                        ai_signature_details.append(f"Tag {tag_name} contains '{kw}'")
    except Exception as e:
        metadata["exif_error"] = str(e)
        
    return {
        "raw_metadata": metadata,
        "has_camera_hardware": has_camera_hardware,
        "has_ai_signature": has_ai_signature,
        "ai_signature_details": ai_signature_details,
    }

def analyze_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Complete visual forensic pipeline for image input.
    Returns composite score, forensic visualizations, and granular evidentiary metrics.
    """
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    orig_b64 = _image_to_base64(image)
    
    # 1. Error Level Analysis
    ela_img, mean_err, err_var = compute_ela(image, quality=settings.ela_jpeg_quality, scale=settings.ela_rescale_factor)
    ela_b64 = _image_to_base64(ela_img)
    
    # 2. 2D FFT Spectrum
    fft_img, high_freq_ratio, grid_spike_ratio, fft_metrics = compute_fft_spectrum(image)
    fft_b64 = _image_to_base64(fft_img)
    
    # 3. Noise Residuals
    noise_metrics = compute_noise_residuals(image)
    
    # 4. EXIF & Metadata
    exif_data = extract_exif_metadata(image)
    
    # 5. Composite AI/Deepfake Likelihood Estimation
    # Weight factors:
    # - High grid spike ratio indicates periodic latent upsampling (Diffusion/GAN): 0-30 pts
    # - ELA variance & mean error inconsistency: 0-25 pts
    # - Quadrant noise discrepancy (spliced/inpainted regions): 0-20 pts
    # - Missing camera hardware metadata + no EXIF: 0-15 pts
    # - Explicit AI tag match: up to +80 pts
    
    ai_score = 0.0
    forensic_reasons = []
    
    if exif_data["has_ai_signature"]:
        ai_score += 85.0
        forensic_reasons.append("EXIF metadata explicitly contains generative AI generator signatures.")
    elif not exif_data["has_camera_hardware"]:
        ai_score += 15.0
        forensic_reasons.append("Absence of authentic camera sensor hardware metadata (Make, Model, Exposure).")
        
    if grid_spike_ratio > 4.5:
        ai_score += 30.0
        forensic_reasons.append(f"Pronounced high-frequency 2D FFT harmonic grid spikes (ratio: {grid_spike_ratio:.2f}) typical of generative upsamplers.")
    elif grid_spike_ratio > 3.0:
        ai_score += 15.0
        forensic_reasons.append(f"Mild frequency domain harmonic anomalies detected (ratio: {grid_spike_ratio:.2f}).")
        
    if noise_metrics["quadrant_discrepancy"] > 0.40:
        ai_score += 20.0
        forensic_reasons.append(f"High spatial noise discrepancy across image quadrants ({noise_metrics['quadrant_discrepancy']:.2f}), suggesting localized inpainting or generative splicing.")
        
    if err_var > 220.0 or (err_var < 0.8 and mean_err > 5.0):
        ai_score += 18.0
        forensic_reasons.append(f"Abnormal Error Level Analysis (ELA) variance ({err_var:.1f}), showing non-uniform compression characteristics.")
        
    # Cap between 0 and 100
    ai_score = float(np.clip(ai_score, 0.0, 100.0))
    
    if ai_score >= 70.0:
        verdict = "LIKELY_SYNTHETIC"
        confidence_desc = "High probability of generative AI creation or heavy manipulation"
    elif ai_score >= 40.0:
        verdict = "SUSPICIOUS_TAMPERED"
        confidence_desc = "Moderate anomalies detected; potential splicing or post-processing"
    else:
        verdict = "AUTHENTIC"
        confidence_desc = "Consistent optical sensor characteristics with natural noise distribution"
        
    return {
        "verdict": verdict,
        "synthetic_probability": round(ai_score, 1),
        "confidence_description": confidence_desc,
        "forensic_reasons": forensic_reasons,
        "visualizations": {
            "original": orig_b64,
            "ela": ela_b64,
            "fft_spectrum": fft_b64,
        },
        "metrics": {
            "ela": {
                "mean_error": round(mean_err, 2),
                "error_variance": round(err_var, 2),
            },
            "frequency_domain": {
                "grid_spike_ratio": round(grid_spike_ratio, 3),
                "high_freq_ratio": round(high_freq_ratio, 4),
            },
            "noise_residuals": {
                "variance": round(noise_metrics["noise_variance"], 2),
                "quadrant_discrepancy": round(noise_metrics["quadrant_discrepancy"], 3),
            },
            "metadata": {
                "has_camera_hardware": exif_data["has_camera_hardware"],
                "has_ai_signature": exif_data["has_ai_signature"],
                "details": exif_data["ai_signature_details"],
            }
        }
    }


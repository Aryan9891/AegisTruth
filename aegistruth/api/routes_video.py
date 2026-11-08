"""API endpoints for Video Deepfake and Temporal Consistency Forensics."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from aegistruth.core.video_forensics import analyze_video
from aegistruth.core.provenance import generate_provenance_manifest

router = APIRouter(prefix="/api/forensics/video", tags=["Video Forensics"])

@router.post("")
async def forensic_video_upload(file: UploadFile = File(...)):
    """
    Uploads a video or animated media file (GIF, MP4, WebM)
    and performs frame-to-frame temporal flicker, optical flow, and keyframe spatial FFT analysis.
    """
    try:
        content = await file.read()
        results = analyze_video(content, filename=file.filename)
        manifest = generate_provenance_manifest("video", content, results)
        results["provenance_manifest"] = manifest
        return results
    except Exception as e:
        results = {
            "verdict": "VIDEO_DIAGNOSTIC_WARNING",
            "synthetic_probability": 0.0,
            "confidence_description": f"Video analysis encountered an issue: {str(e)}",
            "forensic_reasons": [
                f"Video asset processing note: {str(e)}",
                "Please verify the media file is an active video (MP4, MKV, AVI, MOV, WebM) or animated sequence (GIF)."
            ],
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
        manifest = generate_provenance_manifest("video", content if "content" in locals() else b"", results)
        results["provenance_manifest"] = manifest
        return results


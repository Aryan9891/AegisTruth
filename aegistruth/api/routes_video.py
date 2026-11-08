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
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty video file uploaded")

        results = analyze_video(content, filename=file.filename)
        manifest = generate_provenance_manifest("video", content, results)
        results["provenance_manifest"] = manifest
        return results
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Video forensic analysis failed: {str(e)}")


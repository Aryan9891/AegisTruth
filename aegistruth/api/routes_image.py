"""API endpoints for Image and Visual Deepfake Forensics."""

import base64
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from aegistruth.core.image_forensics import analyze_image
from aegistruth.core.provenance import generate_provenance_manifest

router = APIRouter(prefix="/api/forensics/image", tags=["Image Forensics"])

class ImageBase64Request(BaseModel):
    image_base64: str

@router.post("")
async def forensic_image_upload(file: UploadFile = File(...)):
    """Uploads an image file (JPEG, PNG, WebP) and performs ELA, 2D FFT, and noise residual forensics."""
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
            
        results = analyze_image(content)
        manifest = generate_provenance_manifest("image", content, results)
        results["provenance_manifest"] = manifest
        return results
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Visual forensic analysis failed: {str(e)}")

@router.post("/base64")
async def forensic_image_base64(req: ImageBase64Request):
    """Analyzes a base64-encoded image."""
    try:
        raw = req.image_base64
        if "base64," in raw:
            raw = raw.split("base64,")[1]
        content = base64.b64decode(raw)
        results = analyze_image(content)
        manifest = generate_provenance_manifest("image", content, results)
        results["provenance_manifest"] = manifest
        return results
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Visual forensic analysis failed: {str(e)}")


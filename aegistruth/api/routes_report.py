"""API endpoints for C2PA Audit Certificate generation and System Health."""

import io
import zipfile
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, Any
from aegistruth.core.provenance import generate_html_certificate
from aegistruth.config import PROJECT_DIR
import aegistruth

router = APIRouter(prefix="/api/report", tags=["Provenance & Reports"])

class ManifestRequest(BaseModel):
    manifest: Dict[str, Any]

@router.get("/download-extension")
async def download_browser_extension():
    """Generates and serves a packaged zip archive of the AegisTruth Chrome Extension."""
    try:
        ext_dir = PROJECT_DIR / "browser_extension"
        if not ext_dir.exists():
            raise HTTPException(status_code=404, detail="Browser extension folder not found")
        
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in ext_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, arcname=f.relative_to(ext_dir))
        buf.seek(0)
        
        return Response(
            content=buf.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=aegistruth-browser-extension.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to package extension: {str(e)}")

@router.post("/export-html")
async def export_html_certificate(req: ManifestRequest):
    """Generates a downloadable HTML forensic audit certificate."""
    try:
        html = generate_html_certificate(req.manifest)
        return Response(content=html, media_type="text/html")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to generate certificate: {str(e)}")

@router.get("/health")
async def health_check():
    """System health check and forensic capabilities inventory."""
    return {
        "status": "ONLINE",
        "service": "AegisTruth Sentinel Engine",
        "version": aegistruth.__version__,
        "capabilities": [
            "visual_error_level_analysis",
            "2d_fft_spectrum_radial_forensics",
            "sensor_noise_residual_prnu",
            "stft_mel_spectrogram_analysis",
            "pitch_jitter_shimmer_acoustics",
            "sentence_burstiness_and_perplexity",
            "zero_width_unicode_jailbreak_defense",
            "agent_tool_sandbox_firewall",
            "c2pa_cryptographic_manifest_attestation",
        ]
    }


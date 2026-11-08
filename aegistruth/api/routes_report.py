"""API endpoints for C2PA Audit Certificate generation and System Health."""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, Any
from aegistruth.core.provenance import generate_html_certificate
import aegistruth

router = APIRouter(prefix="/api/report", tags=["Provenance & Reports"])

class ManifestRequest(BaseModel):
    manifest: Dict[str, Any]

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


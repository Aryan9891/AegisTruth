"""API endpoints for Textual AI Forensics and Fact Verification."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aegistruth.core.text_forensics import analyze_text
from aegistruth.core.fact_checker import verify_facts
from aegistruth.core.provenance import generate_provenance_manifest

router = APIRouter(prefix="/api/forensics/text", tags=["Text Forensics & Fact Checking"])

class TextPayload(BaseModel):
    text: str

@router.post("")
async def forensic_text_analysis(payload: TextPayload):
    """Analyzes text for synthetic AI patterns, burstiness, perplexity, and linguistic cliches."""
    try:
        content = payload.text
        results = analyze_text(content)
        manifest = generate_provenance_manifest("text", content.encode("utf-8"), results)
        results["provenance_manifest"] = manifest
        return results
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Text forensic analysis failed: {str(e)}")

@router.post("/fact-check")
async def factual_integrity_check(payload: TextPayload):
    """Decomposes text into propositional claims, checks knowledge benchmarks and internal contradictions."""
    try:
        content = payload.text
        results = verify_facts(content)
        return results
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Fact checking analysis failed: {str(e)}")


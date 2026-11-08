"""OpenAI-Compatible Universal Agent Firewall Proxy Endpoints."""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from aegistruth.core.agent_proxy import (
    ChatCompletionRequest,
    process_chat_completion,
    SECURITY_AUDIT_LOGS
)

router = APIRouter(tags=["Universal Agent Proxy"])

@router.get("/v1/models")
async def list_models():
    """Returns available models through the AegisTruth Sentinel Gateway."""
    return {
        "object": "list",
        "data": [
            {
                "id": "aegistruth-sentinel-v1",
                "object": "model",
                "created": 1731000000,
                "owned_by": "aegistruth-security"
            },
            {
                "id": "gpt-4o-shielded",
                "object": "model",
                "created": 1731000000,
                "owned_by": "aegistruth-security"
            }
        ]
    }

@router.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest):
    """
    OpenAI-compatible chat completion endpoint.
    Acts as a zero-trust runtime firewall intercepting prompts and tool calls.
    """
    try:
        response = await process_chat_completion(req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy firewall error: {str(e)}")

@router.get("/api/proxy/audit-logs")
async def get_proxy_audit_logs():
    """Returns recent real-time proxy security inspection logs for dashboard telemetry."""
    return {
        "total_intercepted": len(SECURITY_AUDIT_LOGS),
        "logs": [log.model_dump() for log in SECURITY_AUDIT_LOGS[:50]]
    }

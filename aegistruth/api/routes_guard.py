"""API endpoints for Autonomous Agent Security and Prompt Injection Defense."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aegistruth.core.agent_guard import inspect_prompt, inspect_tool_call

router = APIRouter(prefix="/api/guard", tags=["Agent Security Firewall"])

class PromptGuardRequest(BaseModel):
    prompt: str
    metadata: Optional[Dict[str, Any]] = None

class ToolGuardRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@router.post("/inspect-prompt")
async def guard_prompt_endpoint(req: PromptGuardRequest):
    """
    Scans a prompt or tool-retrieved text for jailbreaks, prompt injection,
    and invisible zero-width unicode token smuggling.
    """
    try:
        report = inspect_prompt(req.prompt)
        return report
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Prompt guard scan failed: {str(e)}")

@router.post("/inspect-tool")
async def guard_tool_endpoint(req: ToolGuardRequest):
    """
    Evaluates prospective agent tool calls and commands against zero-trust policy.
    Blocks destructive filesystem wipes, reverse shells, and database drop commands.
    """
    try:
        report = inspect_tool_call(req.tool_name, req.arguments)
        return report
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Tool guard inspection failed: {str(e)}")


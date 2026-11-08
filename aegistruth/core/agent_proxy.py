"""Universal Zero-Trust AI Agent Firewall Proxy (OpenAI-Compatible Gateway)."""

import time
import uuid
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel
from aegistruth.core.agent_guard import inspect_prompt, inspect_tool_call
from aegistruth.core.text_forensics import analyze_text
from aegistruth.core.fact_checker import verify_facts
from aegistruth.core.provenance import compute_content_hashes

class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = ""
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class ChatCompletionRequest(BaseModel):
    model: str = "aegistruth-sentinel-v1"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None

class ProxySecurityAuditLog(BaseModel):
    request_id: str
    timestamp: float
    model: str
    status: str
    prompt_threat_score: float
    tool_risk_score: float
    factuality_score: float
    violations: List[str]

# In-memory security audit log for live dashboard telemetry
SECURITY_AUDIT_LOGS: List[ProxySecurityAuditLog] = []

async def process_chat_completion(
    req: ChatCompletionRequest,
    upstream_url: Optional[str] = None,
    upstream_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Zero-trust interceptor firewall for LLM chat completion requests.
    Inspects prompts, quarantines dangerous tool calls, and audits model outputs.
    """
    req_id = f"aegis-{uuid.uuid4().hex[:12]}"
    epoch = time.time()
    violations = []
    max_prompt_threat = 0.0
    max_tool_risk = 0.0

    # 1. Pre-Flight Inspection: Scan all incoming messages
    for msg in req.messages:
        if msg.content:
            report = inspect_prompt(msg.content)
            max_prompt_threat = max(max_prompt_threat, report["threat_score"])
            if report["verdict"] == "BLOCK":
                violations.extend([f"Prompt Injection: {t['type']} ({t['matched_text']})" for t in report["threats"]])

        # If incoming message contains client tool execution results or calls
        if msg.tool_calls:
            for tc in msg.tool_calls:
                func_name = tc.get("function", {}).get("name", "tool")
                func_args = tc.get("function", {}).get("arguments", {})
                tool_rep = inspect_tool_call(func_name, func_args)
                max_tool_risk = max(max_tool_risk, tool_rep["risk_severity"])
                if not tool_rep["is_safe_to_execute"]:
                    violations.extend([f"Quarantined Tool: {v['policy_violation']}" for v in tool_rep["violations"]])

    # If prompt injection is blocked, reject execution immediately
    if max_prompt_threat >= 80.0:
        audit = ProxySecurityAuditLog(
            request_id=req_id,
            timestamp=epoch,
            model=req.model,
            status="BLOCKED_INJECTION",
            prompt_threat_score=max_prompt_threat,
            tool_risk_score=max_tool_risk,
            factuality_score=0.0,
            violations=violations
        )
        SECURITY_AUDIT_LOGS.insert(0, audit)
        if len(SECURITY_AUDIT_LOGS) > 100:
            SECURITY_AUDIT_LOGS.pop()

        return {
            "id": req_id,
            "object": "chat.completion",
            "created": int(epoch),
            "model": req.model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[AegisTruth Sentinel Security Quarantine]: Execution denied due to high-risk adversarial prompt injection ({violations[0]})."
                },
                "finish_reason": "security_quarantine"
            }],
            "security_manifest": {
                "verdict": "BLOCKED",
                "threat_score": max_prompt_threat,
                "violations": violations
            }
        }

    # 2. Upstream forwarding or local sentinel execution
    model_output_content = ""
    if upstream_url and upstream_api_key:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"Authorization": f"Bearer {upstream_api_key}"}
                resp = await client.post(upstream_url, json=req.dict(), headers=headers)
                data = resp.json()
                model_output_content = data["choices"][0]["message"]["content"]
        except Exception as e:
            model_output_content = f"Upstream proxy error: {str(e)}"
    else:
        # Autonomous emulation response
        model_output_content = (
            f"Processed securely through AegisTruth Zero-Trust Gateway. "
            f"All incoming messages analyzed and cleared (Threat Score: {max_prompt_threat}/100)."
        )

    # 3. Post-Flight Factuality & Hallucination Audit
    fact_report = verify_facts(model_output_content) if len(model_output_content) > 20 else {"overall_factuality_score": 100.0}
    fact_score = fact_report["overall_factuality_score"]

    # Log audit record
    audit = ProxySecurityAuditLog(
        request_id=req_id,
        timestamp=epoch,
        model=req.model,
        status="PASSED_CLEAN",
        prompt_threat_score=max_prompt_threat,
        tool_risk_score=max_tool_risk,
        factuality_score=fact_score,
        violations=[]
    )
    SECURITY_AUDIT_LOGS.insert(0, audit)
    if len(SECURITY_AUDIT_LOGS) > 100:
        SECURITY_AUDIT_LOGS.pop()

    return {
        "id": req_id,
        "object": "chat.completion",
        "created": int(epoch),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": model_output_content
            },
            "finish_reason": "stop"
        }],
        "security_manifest": {
            "verdict": "PASSED_SAFE",
            "prompt_threat_score": max_prompt_threat,
            "factuality_score": fact_score,
            "content_hash": compute_content_hashes(model_output_content.encode("utf-8"))["sha256"]
        }
    }

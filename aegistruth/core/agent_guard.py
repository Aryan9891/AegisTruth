"""Autonomous Zero-Trust AI Agent Security Sentinel: Prompt Injection, Jailbreak, and Tool Sandbox Firewall."""

import re
import base64
from typing import Dict, Any, List

# Known prompt injection & jailbreak trigger patterns
INJECTION_SIGNATURES = [
    (r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", "INSTRUCTION_OVERRIDE", 90.0),
    (r"disregard\s+(all\s+)?(previous|prior|system)\s+(directives|rules|prompts?)", "INSTRUCTION_OVERRIDE", 90.0),
    (r"system\s*prompt\s*override", "SYSTEM_PROMPT_TAMPERING", 95.0),
    (r"you\s+are\s+now\s+in\s+(developer\s+mode|dan\s+mode|jailbreak\s+mode|unrestricted\s+mode)", "JAILBREAK_ROLEPLAY", 95.0),
    (r"pretend\s+(you\s+have\s+no\s+rules|you\s+are\s+an\s+ai\s+without\s+ethics)", "JAILBREAK_ROLEPLAY", 85.0),
    (r"bypass\s+(safety|content)\s+filters?", "SAFETY_BYPASS_ATTEMPT", 90.0),
    (r"output\s+your\s+(initial|system|original)\s+prompt", "SYSTEM_LEAK_ATTEMPT", 80.0),
    (r"print\s+(the\s+above|all\s+text\s+before\s+this)", "SYSTEM_LEAK_ATTEMPT", 75.0),
    (r"!\[.*?\]\(https?://[^\s]+\?[^\s]*(=|%3D).*?\)", "MARKDOWN_DATA_EXFILTRATION", 95.0),
]

# Destructive tool-call shell/database command patterns
DANGEROUS_TOOL_PATTERNS = [
    (r"\b(rm\s+-rf|del\s+/[fq]|format\s+[a-z]:|mkfs)\b", "DESTRUCTIVE_FILESYSTEM_WIPE", 100.0),
    (r"\b(curl|wget)\s+.*?\|\s*(bash|sh|powershell|cmd)\b", "REMOTE_CODE_EXECUTION_PIPE", 100.0),
    (r"\b(nc|netcat)\s+.*?-e\s+/bin/(ba)?sh\b", "REVERSE_SHELL_EXPLOIT", 100.0),
    (r"\b(drop\s+(table|database|schema)|truncate\s+table)\b", "DESTRUCTIVE_SQL_DROP", 95.0),
    (r"\b(chmod\s+-R\s+777|takeown\s+/f)\b", "UNSAFE_PERMISSION_ESCALATION", 85.0),
    (r"\b(env|printenv|set)\s*\|\s*(curl|wget|nc)\b", "CREDENTIAL_EXFILTRATION", 100.0),
    (r"\b(api_key|secret_key|private_key|token)\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", "PLAINTEXT_SECRET_LEAK", 90.0),
]

# Unicode obfuscation patterns
ZERO_WIDTH_CHARS = {'\u200b', '\u200c', '\u200d', '\ufeff', '\u200e', '\u200f'}
BIDI_OVERRIDE_CHARS = {'\u202a', '\u202b', '\u202c', '\u202d', '\u202e'}

def inspect_unicode_obfuscation(text: str) -> Dict[str, Any]:
    """Detects invisible zero-width characters and bidirectional override attacks."""
    zw_found = [c for c in text if c in ZERO_WIDTH_CHARS]
    bidi_found = [c for c in text if c in BIDI_OVERRIDE_CHARS]
    
    return {
        "has_zero_width": len(zw_found) > 0,
        "zero_width_count": len(zw_found),
        "has_bidi_override": len(bidi_found) > 0,
        "bidi_override_count": len(bidi_found),
        "is_adversarial_obfuscation": len(zw_found) > 2 or len(bidi_found) > 0
    }

def detect_smuggled_base64(text: str) -> List[Dict[str, str]]:
    """Identifies and decodes potential base64 instruction smuggling payloads."""
    # Matches strings that look like base64 blocks of length 20+
    b64_matches = re.findall(r'\b[A-Za-z0-9+/]{24,}={0,2}\b', text)
    decoded_payloads = []
    
    for match in b64_matches:
        try:
            decoded = base64.b64decode(match).decode("utf-8", errors="ignore")
            # If the decoded payload looks like ASCII instructions
            if any(k in decoded.lower() for k in ["system", "ignore", "prompt", "curl", "exec", "eval", "sh", "rm"]):
                decoded_payloads.append({
                    "encoded_snippet": match[:20] + "...",
                    "decoded_content": decoded[:100]
                })
        except Exception:
            continue
            
    return decoded_payloads

def inspect_prompt(prompt_text: str) -> Dict[str, Any]:
    """
    Evaluates an incoming user prompt or retrieved tool context for prompt injection and jailbreak threats.
    """
    threats = []
    max_threat_score = 0.0
    
    # 1. Regex signature scan
    for pattern, threat_type, score in INJECTION_SIGNATURES:
        match = re.search(pattern, prompt_text, re.IGNORECASE)
        if match:
            threats.append({
                "type": threat_type,
                "matched_text": match.group(0),
                "severity_score": score,
                "recommendation": f"Block input matching {threat_type} directive."
            })
            max_threat_score = max(max_threat_score, score)
            
    # 2. Unicode obfuscation scan
    unicode_info = inspect_unicode_obfuscation(prompt_text)
    if unicode_info["is_adversarial_obfuscation"]:
        threats.append({
            "type": "ADVERSARIAL_UNICODE_SMUGGLING",
            "matched_text": f"Found {unicode_info['zero_width_count']} zero-width characters and {unicode_info['bidi_override_count']} Bidi overrides",
            "severity_score": 85.0,
            "recommendation": "Sanitize invisible unicode characters before tokenization."
        })
        max_threat_score = max(max_threat_score, 85.0)
        
    # 3. Base64 payload smuggling
    smuggled = detect_smuggled_base64(prompt_text)
    if smuggled:
        threats.append({
            "type": "SMUGGLED_BASE64_EXECUTION_PAYLOAD",
            "matched_text": f"Decoded suspicious payload: {smuggled[0]['decoded_content']}",
            "severity_score": 90.0,
            "recommendation": "Inspect and reject encoded execution parameters."
        })
        max_threat_score = max(max_threat_score, 90.0)
        
    # Determine security verdict
    if max_threat_score >= 80.0:
        verdict = "BLOCK"
        action = "HALT_EXECUTION_THREAT_DETECTED"
    elif max_threat_score >= 40.0:
        verdict = "WARN_SANDBOX"
        action = "EXECUTE_WITH_STRICT_SANDBOXING"
    else:
        verdict = "ALLOW"
        action = "PASS_SAFE"
        
    return {
        "verdict": verdict,
        "action": action,
        "threat_score": round(max_threat_score, 1),
        "threat_count": len(threats),
        "threats": threats,
        "unicode_metadata": unicode_info
    }

def inspect_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates whether an agent's proposed tool call or terminal command violates security policies.
    """
    arg_string = str(arguments)
    violations = []
    max_severity = 0.0
    
    for pattern, threat_type, severity in DANGEROUS_TOOL_PATTERNS:
        match = re.search(pattern, arg_string, re.IGNORECASE)
        if match:
            violations.append({
                "policy_violation": threat_type,
                "matched_pattern": match.group(0),
                "severity": severity
            })
            max_severity = max(max_severity, severity)
            
    is_safe = (len(violations) == 0) and (max_severity < 75.0)
    
    return {
        "is_safe_to_execute": is_safe,
        "risk_severity": round(max_severity, 1),
        "tool_name": tool_name,
        "violations": violations,
        "action": "PROCEED" if is_safe else "QUARANTINE_DENIED"
    }


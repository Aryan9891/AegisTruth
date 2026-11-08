"""Core forensic, fact-checking, and agent defense engines."""

from aegistruth.core.image_forensics import analyze_image
from aegistruth.core.audio_forensics import analyze_audio
from aegistruth.core.text_forensics import analyze_text
from aegistruth.core.fact_checker import verify_facts
from aegistruth.core.agent_guard import inspect_prompt, inspect_tool_call
from aegistruth.core.provenance import generate_provenance_manifest

__all__ = [
    "analyze_image",
    "analyze_audio",
    "analyze_text",
    "verify_facts",
    "inspect_prompt",
    "inspect_tool_call",
    "generate_provenance_manifest",
]


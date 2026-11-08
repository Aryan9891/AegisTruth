"""AegisTruth Python SDK Client: Programmatic interface for forensic analysis and agent guard."""

from pathlib import Path
from typing import Dict, Any, Union, Optional
import httpx

class AegisClient:
    """Official Python SDK client for AegisTruth Sentinel API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        """Checks API health and capabilities."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.base_url}/api/report/health")
            resp.raise_for_status()
            return resp.json()

    def verify_image(self, file_path_or_bytes: Union[str, Path, bytes]) -> Dict[str, Any]:
        """Performs ELA, 2D Fourier (FFT), and noise residual analysis on an image."""
        if isinstance(file_path_or_bytes, (str, Path)):
            content = Path(file_path_or_bytes).read_bytes()
            filename = Path(file_path_or_bytes).name
        else:
            content = file_path_or_bytes
            filename = "image.png"

        files = {"file": (filename, content, "image/png")}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/forensics/image", files=files)
            resp.raise_for_status()
            return resp.json()

    def verify_video(self, file_path_or_bytes: Union[str, Path, bytes]) -> Dict[str, Any]:
        """Analyzes video media for temporal optical flicker, motion jitter, and face-swapping warping."""
        if isinstance(file_path_or_bytes, (str, Path)):
            content = Path(file_path_or_bytes).read_bytes()
            filename = Path(file_path_or_bytes).name
        else:
            content = file_path_or_bytes
            filename = "video.gif"

        files = {"file": (filename, content, "image/gif")}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/forensics/video", files=files)
            resp.raise_for_status()
            return resp.json()

    def verify_audio(self, file_path_or_bytes: Union[str, Path, bytes]) -> Dict[str, Any]:
        """Analyzes audio for neural vocoder artifacts, flat pitch micro-jitter, and voice cloning."""
        if isinstance(file_path_or_bytes, (str, Path)):
            content = Path(file_path_or_bytes).read_bytes()
            filename = Path(file_path_or_bytes).name
        else:
            content = file_path_or_bytes
            filename = "audio.wav"

        files = {"file": (filename, content, "audio/wav")}
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/forensics/audio", files=files)
            resp.raise_for_status()
            return resp.json()

    def verify_text(self, text: str) -> Dict[str, Any]:
        """Evaluates text for sentence burstiness, Shannon entropy, and generative LLM cliches."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/forensics/text", json={"text": text})
            resp.raise_for_status()
            return resp.json()

    def check_facts(self, text: str) -> Dict[str, Any]:
        """Decomposes text into propositional claims and checks contradictions and anachronisms."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/forensics/text/fact-check", json={"text": text})
            resp.raise_for_status()
            return resp.json()

    def guard_prompt(self, prompt: str) -> Dict[str, Any]:
        """Scans prompt for jailbreaks, prompt injection, and invisible unicode token smuggling."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/guard/inspect-prompt", json={"prompt": prompt})
            resp.raise_for_status()
            return resp.json()

    def guard_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Firewall sandbox for prospective agent tool calls."""
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/api/guard/inspect-tool",
                json={"tool_name": tool_name, "arguments": arguments}
            )
            resp.raise_for_status()
            return resp.json()


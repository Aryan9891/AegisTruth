"""AegisTruth Python SDK Client: Programmatic interface for forensic analysis and agent guard."""

from pathlib import Path
from typing import Dict, Any, Union, Optional
import httpx


class AegisClient:
    """Official Python SDK client for AegisTruth Sentinel API."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout: float = 30.0,
        session: Optional[httpx.Client] = None,
        app: Optional[Any] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        if app is not None and session is None:
            from fastapi.testclient import TestClient
            self._session = TestClient(app)
        else:
            self._session = session

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}" if not path.startswith("http") else path
        if self._session is not None:
            return self._session.request(method, url, **kwargs)
        with httpx.Client(timeout=self.timeout) as client:
            return client.request(method, url, **kwargs)

    def health(self) -> Dict[str, Any]:
        """Checks API health and capabilities."""
        resp = self._request("GET", "/api/report/health")
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
        resp = self._request("POST", "/api/forensics/image", files=files)
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
        resp = self._request("POST", "/api/forensics/video", files=files)
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
        resp = self._request("POST", "/api/forensics/audio", files=files)
        resp.raise_for_status()
        return resp.json()

    def verify_text(self, text: str) -> Dict[str, Any]:
        """Evaluates text for sentence burstiness, Shannon entropy, and generative LLM cliches."""
        resp = self._request("POST", "/api/forensics/text", json={"text": text})
        resp.raise_for_status()
        return resp.json()

    def check_facts(self, text: str) -> Dict[str, Any]:
        """Decomposes text into propositional claims and checks contradictions and anachronisms."""
        resp = self._request("POST", "/api/forensics/text/fact-check", json={"text": text})
        resp.raise_for_status()
        return resp.json()

    def guard_prompt(self, prompt: str) -> Dict[str, Any]:
        """Scans prompt for jailbreaks, prompt injection, and invisible unicode token smuggling."""
        resp = self._request("POST", "/api/guard/inspect-prompt", json={"prompt": prompt})
        resp.raise_for_status()
        return resp.json()

    def guard_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Firewall sandbox for prospective agent tool calls."""
        resp = self._request(
            "POST",
            "/api/guard/inspect-tool",
            json={"tool_name": tool_name, "arguments": arguments}
        )
        resp.raise_for_status()
        return resp.json()

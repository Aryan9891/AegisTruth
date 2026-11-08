"""Convenient launcher for AegisTruth Studio & API."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from aegistruth.config import settings

def main():
    print("=" * 70)
    print("   AEGIS-TRUTH: Autonomous Multi-Modal AI Forensics & Cognitive Sentinel")
    print("=" * 70)
    print(f"[*] Web Studio UI:  http://127.0.0.1:{settings.port}")
    print(f"[*] API Docs:       http://127.0.0.1:{settings.port}/docs")
    print(f"[*] OpenAPI Spec:   http://127.0.0.1:{settings.port}/openapi.json")
    print("=" * 70)
    uvicorn.run("aegistruth.api.app:app", host=settings.host, port=settings.port, reload=False)

if __name__ == "__main__":
    main()


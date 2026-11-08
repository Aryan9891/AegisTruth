"""API endpoints and WebSocket stream for Audio and Voice Clone Forensics."""

import io
import json
from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from aegistruth.core.audio_forensics import analyze_audio
from aegistruth.core.provenance import generate_provenance_manifest

router = APIRouter(prefix="/api/forensics/audio", tags=["Audio Forensics"])

@router.post("")
async def forensic_audio_upload(file: UploadFile = File(...)):
    """Uploads an audio file (WAV) and performs STFT spectrogram, jitter, and vocoder analysis."""
    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file uploaded")
            
        results = analyze_audio(content)
        manifest = generate_provenance_manifest("audio", content, results)
        results["provenance_manifest"] = manifest
        return results
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Audio forensic analysis failed: {str(e)}")

@router.websocket("/stream")
async def forensic_audio_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time live acoustic audio streaming.
    Receives raw audio chunks from client microphone or call stream and returns real-time threat scores.
    """
    await websocket.accept()
    buffer = bytearray()
    
    try:
        while True:
            # Receive binary audio data
            data = await websocket.receive_bytes()
            buffer.extend(data)
            
            # When we have accumulated enough audio (~1-2 seconds of PCM WAV or raw data)
            if len(buffer) >= 32000:
                try:
                    # Analyze current accumulated window
                    results = analyze_audio(bytes(buffer))
                    stream_update = {
                        "status": "STREAMING",
                        "verdict": results["verdict"],
                        "synthetic_probability": results["synthetic_probability"],
                        "jitter": results["metrics"]["pitch_jitter"],
                        "reasons": results["forensic_reasons"][:2]
                    }
                    await websocket.send_text(json.dumps(stream_update))
                except Exception:
                    pass
                # Keep sliding window (last 16000 bytes)
                buffer = buffer[-16000:]
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()


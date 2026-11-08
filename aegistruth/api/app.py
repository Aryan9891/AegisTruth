"""FastAPI application for AegisTruth."""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from aegistruth.config import STATIC_DIR, settings
from aegistruth.api.routes_image import router as image_router
from aegistruth.api.routes_audio import router as audio_router
from aegistruth.api.routes_text import router as text_router
from aegistruth.api.routes_guard import router as guard_router
from aegistruth.api.routes_report import router as report_router

def create_app() -> FastAPI:
    """Factory creating and configuring the AegisTruth FastAPI server."""
    app = FastAPI(
        title="AegisTruth API",
        description="Autonomous Multi-Modal AI Forensics, Deepfake Detection & Fact Verification Sentinel",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API Routers
    app.include_router(image_router)
    app.include_router(audio_router)
    app.include_router(text_router)
    app.include_router(guard_router)
    app.include_router(report_router)

    # Serve static frontend files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        async def root():
            index_path = STATIC_DIR / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"message": "AegisTruth Sentinel API is running. Visit /docs for API documentation."}

    return app

app = create_app()


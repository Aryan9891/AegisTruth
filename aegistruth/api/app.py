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
from aegistruth.api.routes_video import router as video_router
from aegistruth.api.routes_proxy import router as proxy_router

def create_app() -> FastAPI:
    """Factory creating and configuring the AegisTruth FastAPI server."""
    app = FastAPI(
        title="AegisTruth API",
        description="Autonomous Multi-Modal AI Forensics, Deepfake Detection & Fact Verification Sentinel",
        version="1.1.0",
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
    app.include_router(video_router)
    app.include_router(proxy_router)

    # Serve static frontend files
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
        css_dir = STATIC_DIR / "css"
        if css_dir.exists():
            app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
        js_dir = STATIC_DIR / "js"
        if js_dir.exists():
            app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
        samples_dir = STATIC_DIR / "samples"
        if samples_dir.exists():
            app.mount("/samples", StaticFiles(directory=str(samples_dir)), name="samples")
        downloads_dir = STATIC_DIR / "downloads"
        if downloads_dir.exists():
            app.mount("/downloads", StaticFiles(directory=str(downloads_dir)), name="downloads")

        @app.get("/", include_in_schema=False)
        async def root():
            index_path = STATIC_DIR / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"message": "AegisTruth Sentinel API is running. Visit /docs for API documentation."}

        for filename in [
            "manifest.json",
            "sw.js",
            "favicon.svg",
            "demo_thumbnail.jpg",
            "demo_preview.gif",
            "aegistruth_demo_walkthrough.mp4",
        ]:
            file_path = STATIC_DIR / filename
            if file_path.exists():
                def _make_handler(p):
                    async def _handler():
                        return FileResponse(p)
                    return _handler
                app.add_api_route(f"/{filename}", _make_handler(file_path), methods=["GET"], include_in_schema=False)

    return app

app = create_app()


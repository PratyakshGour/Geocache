import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.api.data import router as api_router
from app.core.config import settings
from app.services.data_service import geo_cache_service


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for web UI and third-party access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API endpoints
app.include_router(api_router, prefix="/api/v1")


# Ensure static directory exists for UI dashboard
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", summary="Serve Interactive Web Demo Dashboard")
def serve_dashboard():
    """
    Serve the visual web demo dashboard if present, otherwise return JSON cluster status.
    """
    index_path = os.path.join("static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse(content=geo_cache_service.get_cluster_status().model_dump())


@app.get("/health", summary="Health check endpoint")
def health_check():
    return {
        "project": settings.PROJECT_NAME,
        "status": "healthy",
        "version": settings.VERSION,
        "cluster_nodes": len(settings.REGIONS)
    }
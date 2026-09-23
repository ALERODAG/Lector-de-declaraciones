"""Aplicación FastAPI legacy (capa app/).

Este módulo crea la aplicación FastAPI para el sistema legacy.
Es la segunda implementación de la capa de presentación.

NOTA: El entry point principal es main.py (raíz) que usa
presentation/api.py. Este módulo se mantiene por compatibilidad.

Flujo de inicio:
    app/main.py → FastAPI() → CORS → logging middleware → routes
"""

import os
import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from app.routes import processing

# ── Configuración ──────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv es opcional; las variables pueden definirse en el entorno del SO

# Configurar Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("dim-reader")

app = FastAPI(
    title="Declaración de Importación API", 
    version="1.1.0",
    description="API para la extracción y procesamiento de documentos DIM y facturas"
)

# ── CORS ────────────────────────────────────────────────────────────────
# Cargar orígenes desde env o usar default de desarrollo
origins = os.getenv("CORS_ORIGINS", '["*"]')
try:
    allow_origins = json.loads(origins)
except (json.JSONDecodeError, TypeError):
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Middleware de Logging ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware que loguea cada request HTTP entrante y su status code."""
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

# ── API routes ──────────────────────────────────────────────────────────
app.include_router(processing.router, prefix="/api/v1", tags=["Processing"])

# ── Servir el frontend compilado ─────────────────────────────────────────
_FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

if os.path.isdir(_FRONTEND_DIST):
    logger.info("Serving frontend from dist directory")
    app.mount("/assets", StaticFiles(directory=os.path.join(_FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """Sirve el frontend SPA. Excluye rutas /api/*."""
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"message": "Not Found"})
        return FileResponse(os.path.join(_FRONTEND_DIST, "index.html"))
else:
    logger.warning("Frontend dist directory not found. Running in API-only mode.")
    @app.get("/")
    def read_root():
        return {
            "message": "API Backend is running",
            "frontend_status": "Not built (run npm run build in frontend directory)"
        }

"""Factory de la aplicación FastAPI (Clean Architecture).

Crea y configura la instancia de FastAPI con todos los middlewares,
rutas y manejadores de errores.

Flujo de inicio:
    create_app() → FastAPI → CORS → RequestIdMiddleware → routes → handlers
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from core.logging_config import configure_logging
from infrastructure.config import AppSettings
from presentation.middlewares import (
    RequestIdMiddleware,
    application_error_handler,
    generic_exception_handler,
    validation_error_handler,
)
from presentation.routes.processing import router as processing_router
from core.exceptions import ApplicationError


def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI.

    Returns:
        Instancia de FastAPI configurada con middlewares, rutas
        y manejadores de errores.
    """
    settings = AppSettings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API corporativa para procesamiento de declaraciones de importación y facturas",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIdMiddleware)

    app.include_router(processing_router, prefix="/api/v1", tags=["processing"])

    app.add_exception_handler(ApplicationError, application_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
    if os.path.isdir(frontend_dist):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def serve_spa(full_path: str):
            """Sirve el frontend SPA. Excluye rutas /api/*."""
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404)
            return FileResponse(os.path.join(frontend_dist, "index.html"))

    return app

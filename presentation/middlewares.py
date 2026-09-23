"""Middlewares y manejadores de errores de la API.

Proporciona:
- RequestIdMiddleware: Agrega X-Request-ID a cada request/response.
- application_error_handler: Maneja errores de aplicación (400).
- validation_error_handler: Maneja errores de validación Pydantic (422).
- generic_exception_handler: Maneja errores inesperados (500).
"""

import logging
import uuid
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from core.exceptions import ApplicationError

logger = logging.getLogger("lector_declaraciones.middleware")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware que agrega X-Request-ID a cada request y response.

    Si el client no envía X-Request-ID, genera uno automáticamente (UUID).
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    """Maneja ApplicationError retornando HTTP 400 con detalles."""
    logger.error("Application error: %s", exc, exc_info=exc)
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": str(exc),
            "data": None,
            "request_id": request.state.request_id,
        },
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Maneja errores de validación Pydantic retornando HTTP 422."""
    logger.warning("Validation error: %s", exc)
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "Validation failed",
            "errors": exc.errors(),
            "request_id": request.state.request_id,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Maneja excepciones no capturadas retornando HTTP 500."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "request_id": request.state.request_id,
        },
    )

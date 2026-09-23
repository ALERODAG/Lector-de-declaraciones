"""Jerarquía de excepciones de la aplicación.

Define excepciones personalizadas para diferentes capas del sistema:
- ApplicationError: Excepción base para errores de dominio/orquestación
- ExtractionError: Errores en extracción de documentos
- PDFExtractionError: Errores específicos de extracción PDF
- OCRFallbackError: Errores cuando el OCR fallback falla
- ValidationError: Errores de validación de negocio

Uso:
    from core.exceptions import ExtractionError
    raise ExtractionError("No se pudo extraer el texto del PDF")
"""

from typing import Any


class ApplicationError(Exception):
    """Excepción base para errores de dominio y orquestación.

    Attributes:
        message: Mensaje descriptivo del error.
        payload: Datos adicionales opcionales sobre el error.
    """

    def __init__(self, message: str, payload: Any | None = None) -> None:
        super().__init__(message)
        self.payload = payload


class ExtractionError(ApplicationError):
    """Raised when a document cannot be extracted."""


class PDFExtractionError(ExtractionError):
    """Raised when PDF text extraction fails."""


class OCRFallbackError(PDFExtractionError):
    """Raised when OCR fallback fails after text extraction fails."""


class ValidationError(ApplicationError):
    """Raised when business validation fails."""

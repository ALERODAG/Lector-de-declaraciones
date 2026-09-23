"""Esquemas Pydantic para la API legacy (capa app/).

Define los modelos de datos para la serialización/deserialización
de las respuestas HTTP de la capa legacy.

NOTA: Estos esquemas son más genéricos que los de presentation/schemas.py
que usan tipos más específicos (DeclarationSchema, InvoiceDocumentSchema, etc.)
"""

from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ProcessingData(BaseModel):
    """Esquema de datos procesados para la respuesta legacy.

    Usa Dict[str, Any] para mayor flexibilidad con datos dinámicos.
    """
    declarations: List[Dict[str, Any]]
    products: List[Dict[str, Any]]
    invoices: List[Dict[str, Any]] = []


class StandardResponse(BaseModel):
    """Esquema estándar de respuesta de la API legacy.

    Attributes:
        success: Indica si la operación fue exitosa.
        message: Mensaje descriptivo del resultado.
        data: Datos procesados (opcional).
    """
    success: bool
    message: str
    data: Optional[ProcessingData] = None

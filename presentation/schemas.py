"""Esquemas Pydantic para las respuestas de la API.

Define los modelos de datos para la serialización/deserialización
de las respuestas HTTP de la capa de presentación.

Estos esquemas son independientes de las entidades de dominio
y se usan únicamente para la capa de API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DeclarationSchema(BaseModel):
    """Esquema para una declaración de importación en la respuesta."""
    numero: str
    fecha: str
    proveedor: str


class InvoiceItemSchema(BaseModel):
    """Esquema para un ítem de factura en la respuesta."""
    referencia: str
    descripcion: str
    cantidad: Dict[str, Any]
    unidad: str
    valor_unitario: Dict[str, Any]
    valor_total: Dict[str, Any]


class InvoiceMetadataSchema(BaseModel):
    """Esquema para metadatos de factura en la respuesta."""
    num_factura: str
    fecha_factura: str
    proveedor: str
    pais_origen: str
    incoterm: str
    moneda: str
    tipo_cambio: str
    importador: str
    registro_declaracion: Optional[str] = None
    fecha_declaracion: Optional[str] = None
    aduana: Optional[str] = None
    medio_transporte: Optional[str] = None
    conocimiento_embarque: Optional[str] = None
    total_mercancia: Optional[Dict[str, Any]] = None
    flete: Optional[Dict[str, Any]] = None
    seguro: Optional[Dict[str, Any]] = None
    otros_gastos: Optional[Dict[str, Any]] = None
    total_factura: Optional[Dict[str, Any]] = None


class InvoiceDocumentSchema(BaseModel):
    """Esquema para un documento de factura completo en la respuesta."""
    metadata: InvoiceMetadataSchema
    items: List[InvoiceItemSchema]


class ProcessingDataSchema(BaseModel):
    """Esquema para los datos procesados en la respuesta.

    Usa Dict[str, Any] para declarations y products para soportar
    las columnas dinámicas del DIM y del extractor de productos.
    """
    declarations: List[Dict[str, Any]]
    products: List[Dict[str, Any]]
    invoices: List[InvoiceDocumentSchema]
    comparative: Optional[Dict[str, Any]] = None


class StandardResponse(BaseModel):
    """Esquema estándar de respuesta de la API.

    Attributes:
        success: Indica si la operación fue exitosa.
        message: Mensaje descriptivo del resultado.
        data: Datos procesados (opcional, presente si success=True).
    """
    success: bool
    message: str
    data: Optional[ProcessingDataSchema] = None

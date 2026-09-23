"""Rutas de la API para procesamiento de declaraciones y facturas.

Endpoint principal: POST /api/v1/process-multiple
Recibe archivos PDF de declaración y facturas, los procesa y retorna
el resultado en formato JSON estandarizado.

Flujo de datos:
    HTTP POST (multipart) → process_multiple() → ProcessDocumentsUseCase
    → PDFTextExtractor + DeclarationParser + InvoiceProcessor
    → StandardResponse (JSON)
"""

import logging
import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from application.services.invoice_processor import InvoiceProcessor
from application.use_cases.process_documents import ProcessDocumentsUseCase
from infrastructure.config import AppSettings
from infrastructure.pdf.text_extractor import PDFTextExtractor
from infrastructure.parsers.declaration_parser import DeclarationParser
from presentation.schemas import ProcessingDataSchema, StandardResponse
from domain.entities import Product
from extractors.product_extractor import ProductExtractor

logger = logging.getLogger("lector_declaraciones.routes.processing")
router = APIRouter()

# Inicializar caso de uso con dependencias (Dependency Injection)
settings = AppSettings()
text_extractor = PDFTextExtractor(settings)
declaration_parser = DeclarationParser()
invoice_processor = InvoiceProcessor()
product_extractor = ProductExtractor()
process_documents_use_case = ProcessDocumentsUseCase(
    text_extractor=text_extractor,
    declaration_parser=declaration_parser,
    invoice_processor=invoice_processor,
    product_extractor=product_extractor,
)


def _serialize_quantity(quantity):
    """Serializa un objeto Quantity a diccionario."""
    if quantity is None:
        return None
    if isinstance(quantity, dict):
        return quantity
    return {"value": str(quantity.value)}


def _serialize_money(money):
    """Serializa un objeto Money a diccionario."""
    if money is None:
        return None
    if isinstance(money, dict):
        return money
    return {"amount": str(money.amount), "currency": money.currency}


def _serialize_metadata(metadata):
    """Serializa un objeto InvoiceMetadata a diccionario."""
    return {
        "num_factura": metadata.num_factura,
        "fecha_factura": metadata.fecha_factura,
        "proveedor": metadata.proveedor,
        "pais_origen": metadata.pais_origen,
        "incoterm": metadata.incoterm,
        "moneda": metadata.moneda,
        "tipo_cambio": str(metadata.tipo_cambio),
        "importador": metadata.importador,
        "registro_declaracion": metadata.registro_declaracion,
        "fecha_declaracion": metadata.fecha_declaracion,
        "aduana": metadata.aduana,
        "medio_transporte": metadata.medio_transporte,
        "conocimiento_embarque": metadata.conocimiento_embarque,
        "total_mercancia": _serialize_money(metadata.total_mercancia),
        "flete": _serialize_money(metadata.flete),
        "seguro": _serialize_money(metadata.seguro),
        "otros_gastos": _serialize_money(metadata.otros_gastos),
        "total_factura": _serialize_money(metadata.total_factura),
    }


def _invoice_document_to_dict(invoice_document):
    """Serializa un InvoiceDocument a diccionario para la respuesta JSON."""
    return {
        "metadata": _serialize_metadata(invoice_document.metadata),
        "items": [
            {
                "referencia": item.referencia,
                "descripcion": item.descripcion,
                "cantidad": _serialize_quantity(item.cantidad),
                "unidad": item.unidad,
                "valor_unitario": _serialize_money(item.valor_unitario),
                "valor_total": _serialize_money(item.valor_total),
            }
            for item in invoice_document.items
        ],
    }


def _product_to_dict(product: Product) -> dict:
    """Serializa un objeto Product a diccionario para la respuesta JSON.

    Usa los mismos nombres de campo que el DataFrame del legacy
    (Cantidad, Referencia, etc.) para compatibilidad con el frontend.
    """
    return {
        "Referencia": product.referencia,
        "Producto": product.descripcion,
        "Descripcion": product.descripcion,
        "Cantidad": str(product.cantidad.value),
        "Unidad": product.unidad,
        "Pais_Origen": product.pais_origen or "",
    }


@router.post("/process-multiple", response_model=StandardResponse)
async def process_multiple(declaration: UploadFile = File(...), invoices: list[UploadFile] = File([])):
    """Endpoint principal para procesar declaración y facturas (Clean Architecture).

    Recibe archivos PDF via multipart form data, los guarda temporalmente,
    ejecuta el caso de uso ProcessDocumentsUseCase y retorna la respuesta
    estandarizada.

    Args:
        declaration: Archivo PDF de la declaración de importación.
        invoices: Lista de archivos PDF de facturas (opcional).

    Returns:
        StandardResponse con success, message y data procesada.

    Raises:
        HTTPException: Si ocurre un error durante el procesamiento.
    """
    temp_files: list[str] = []

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as decl_file:
            content = await declaration.read()
            decl_file.write(content)
            temp_files.append(decl_file.name)
            declaration_path = decl_file.name

        invoice_paths: list[str] = []
        for invoice in invoices:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as invoice_file:
                invoice_file.write(await invoice.read())
                invoice_paths.append(invoice_file.name)
                temp_files.append(invoice_file.name)

        result = process_documents_use_case.execute(
            declaration_path, invoice_paths,
            declaration_filename=declaration.filename or "",
            products=[]
        )
        response_data = ProcessingDataSchema(
            declarations=result.declarations_data or [],
            products=result.products_data or [_product_to_dict(p) for p in result.products],
            invoices=[_invoice_document_to_dict(invoice) for invoice in result.invoices],
        )

        return StandardResponse(success=True, message="Archivos procesados correctamente", data=response_data)
    except Exception as exc:
        logger.exception("Error procesando archivos")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    finally:
        for path in temp_files:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except OSError:
                logger.warning("No se pudo eliminar el archivo temporal %s", path)

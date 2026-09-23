"""Endpoint de procesamiento legacy (capa app/).

Este módulo mantiene compatibilidad con el endpoint legacy pero delega
la lógica de negocio a la nueva arquitectura (application/use_cases).

Flujo de datos:
    HTTP POST → process_multiple() → ProcessDocumentsUseCase.execute() → Response

NOTA: Este endpoint es un wrapper delgado. La lógica real está en
application/use_cases/process_documents.py y infrastructure/.
"""

import os
import tempfile
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.schemas.models import StandardResponse, ProcessingData
from services.processing_services import process_files_api

router = APIRouter()
logger = logging.getLogger("dim-reader.processing")


@router.post("/process-multiple", response_model=StandardResponse)
async def process_multiple(
    declaration: UploadFile = File(...),
    invoices: List[UploadFile] = File([])
):
    """Procesa una declaración y múltiples facturas (endpoint legacy).

    Guarda los archivos subidos en archivos temporales, llama al servicio
    de procesamiento y retorna la respuesta estandarizada.

    Args:
        declaration: Archivo PDF de la declaración de importación.
        invoices: Lista de archivos PDF de facturas (opcional).

    Returns:
        StandardResponse con success, message y data (declaraciones,
        productos, invoices procesados).
    """
    decl_path = None
    invoice_paths = []
    
    try:
        logger.info(f"Procesando declaración: {declaration.filename} con {len(invoices)} facturas")
        
        # Save declaration to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_decl:
            tmp_decl.write(await declaration.read())
            decl_path = tmp_decl.name
            
        # Save invoices to temp
        for inv in invoices:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_inv:
                tmp_inv.write(await inv.read())
                invoice_paths.append(tmp_inv.name)
                
        # Process everything
        logger.info("Llamando al servicio de procesamiento...")
        result_dict = process_files_api(decl_path, declaration.filename, invoice_paths)
        
        return StandardResponse(
            success=True,
            message="Archivos procesados correctamente",
            data=ProcessingData(
                declarations=result_dict["declarations"],
                products=result_dict["products"],
                invoices=result_dict["invoices"]
            )
        )
    except Exception as e:
        logger.error(f"Error procesando archivos: {str(e)}")
        return StandardResponse(
            success=False,
            message=f"Error al procesar los archivos: {str(e)}",
            data=None
        )
    finally:
        # Cleanup ensures files are removed even if an error occurs
        if decl_path and os.path.exists(decl_path):
            os.remove(decl_path)
        for p in invoice_paths:
            if os.path.exists(p):
                os.remove(p)
        logger.info("Limpieza de archivos temporales completada")

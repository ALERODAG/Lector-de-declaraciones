"""Servicio legacy de procesamiento de declaraciones y facturas.

Este módulo contiene la lógica de orquestación original del proyecto.
Procesa declaraciones DIM y múltiples facturas usando extractores específicos.

NOTA: Esta funcionalidad está replicada en la nueva arquitectura:
- application/use_cases/process_documents.py (orquestador)
- infrastructure/extractors/ (extractores específicos)

Flujo de datos:
    process_files_api() → extraer_texto_pdf() → extract_declarations()
                       → ProductExtractor() → procesar_factura_general()
                       → dict con declarations, products, invoices
"""

import os
import logging
import pandas as pd
from extractors.declaration_extractor import extract_declarations
from extractors.factura_normalizer import normalizar_items
from extractors.product_extractor import ProductExtractor, extraer_texto_pdf
from extractors.factura_sofabex import procesar_factura_sofabex
from extractors.factura_adk import procesar_factura_adk
from extractors.facturas_gate import procesar_factura_gate
from extractors.factura_universal import procesar_factura_universal

logger = logging.getLogger("dim-reader.services")


def procesar_factura_general(inv_path: str):
    """Intenta procesar una factura usando diferentes extractores en orden.

    Prueba los extractores específicos (Sofabex, ADK, Gate) y si ninguno
    reconoce el formato, usa el extractor universal como último recurso.

    Args:
        inv_path: Ruta al archivo PDF de la factura.

    Returns:
        Diccionario con estructura {"metadata": {...}, "items": [...]}
        o None si ningún extractor pudo procesar la factura.
    """
    # 1. Intentar con extractores específicos
    extractores = [
        ("Sofabex", procesar_factura_sofabex),
        ("ADK", procesar_factura_adk),
        ("Gate", procesar_factura_gate)
    ]
    
    for nombre, extractor_func in extractores:
        try:
            res = extractor_func(inv_path)
            if res is not None:
                # Si ya viene con el formato estandar (Sofabex)
                if isinstance(res, dict) and "metadata" in res and "items" in res:
                    print(f"Factura procesada con éxito usando extractor: {nombre}")
                    res["items"] = normalizar_items(res["items"])
                    return res
                
                # Si es un DataFrame (ADK, Gate)
                df = res if isinstance(res, pd.DataFrame) else pd.DataFrame(res)
                if not df.empty:
                    print(f"Factura procesada con éxito usando extractor: {nombre}")
                    items = normalizar_items(df.to_dict(orient="records"))
                    metadata = {
                        "num_factura": items[0].get("Invoice") or items[0].get("num_factura") or "N/A",
                        "fecha_factura": items[0].get("Date") or items[0].get("fecha_factura") or "N/A",
                        "proveedor": nombre,
                        "pais_origen": items[0].get("pais_origen") or "N/A",
                        "incoterm": items[0].get("incoterm") or "N/A",
                        "moneda": items[0].get("moneda") or "USD",
                        "tipo_cambio": items[0].get("tipo_cambio") or 1.0,
                        "importador": items[0].get("importador") or "N/A",
                        "registro_declaracion": "",
                        "fecha_declaracion": "",
                        "aduana": "",
                        "medio_transporte": "",
                        "conocimiento_embarque": "",
                        "fecha_embarque": "",
                        "total_mercancia": df["Valor_Total"].sum() if "Valor_Total" in df.columns else 0.0,
                        "flete": 0.0,
                        "seguro": 0.0,
                        "otros_gastos": 0.0,
                        "total_factura": df["Valor_Total"].sum() if "Valor_Total" in df.columns else 0.0
                    }
                    return {"metadata": metadata, "items": items}
        except Exception as e:
            print(f"Error con extractor {nombre}: {e}")
            
    # 2. Intentar con extractor Universal como último recurso
    try:
        df = procesar_factura_universal(inv_path)
        if df is not None and not df.empty:
            print("Factura procesada con éxito usando extractor: Universal")
            items = normalizar_items(df.to_dict(orient="records"))
            metadata = {
                "num_factura": "UNIVERSAL-" + os.path.basename(inv_path)[:8],
                "fecha_factura": "N/A",
                "proveedor": "UNIVERSAL",
                "pais_origen": "N/A",
                "incoterm": "N/A",
                "moneda": "N/A",
                "tipo_cambio": 1.0,
                "importador": "N/A",
                "registro_declaracion": "",
                "fecha_declaracion": "",
                "aduana": "",
                "medio_transporte": "",
                "conocimiento_embarque": "",
                "fecha_embarque": "",
                "total_mercancia": df["Valor_Total"].sum() if "Valor_Total" in df.columns else 0.0,
                "flete": 0.0,
                "seguro": 0.0,
                "otros_gastos": 0.0,
                "total_factura": df["Valor_Total"].sum() if "Valor_Total" in df.columns else 0.0
            }
            return {"metadata": metadata, "items": items}
    except Exception as e:
        print(f"Error con extractor Universal: {e}")
        
    return None


def process_files_api(declaration_path: str, declaration_filename: str, invoice_paths: list) -> dict:
    """Procesa una declaración y múltiples facturas (API legacy).

    Orquesta todo el flujo de procesamiento: extrae texto del PDF de
    declaración, extrae declaraciones y productos, y procesa cada factura.

    Args:
        declaration_path: Ruta al archivo PDF de la declaración.
        declaration_filename: Nombre original del archivo de declaración.
        invoice_paths: Lista de rutas a los archivos PDF de facturas.

    Returns:
        Diccionario con tres claves:
            - "declarations": Lista de declaraciones extraídas.
            - "products": Lista de productos extraídos.
            - "invoices": Lista de facturas procesadas.
    """
    texto_decl = extraer_texto_pdf(declaration_path)
    
    # Declaraciones y productos de la declaración
    df_decl = extract_declarations(texto_decl)
    extractor = ProductExtractor()
    df_products = extractor.extract_products_from_text(texto_decl, declaration_filename)
    
    # Procesar facturas
    extracted_invoices = []
    for inv_path in invoice_paths:
        inv_data = procesar_factura_general(inv_path)
        if inv_data:
            extracted_invoices.append(inv_data)
            
    # Limpieza
    df_decl = df_decl.where(pd.notnull(df_decl), None)
    df_products = df_products.where(pd.notnull(df_products), None)
    
    return {
        "declarations": df_decl.to_dict(orient="records"),
        "products": df_products.to_dict(orient="records"),
        "invoices": extracted_invoices
    }

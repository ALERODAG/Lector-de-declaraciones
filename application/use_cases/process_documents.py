"""Caso de uso: Procesamiento de documentos de importación.

Orquesta el flujo completo de procesamiento:
1. Extrae texto del PDF de declaración
2. Parsea las declaraciones DIM
3. Extrae productos de la declaración
4. Extrae texto de cada factura
5. Procesa cada factura con el extractor adecuado
6. Retorna el resultado consolidado

Flujo de datos:
    paths → ProcessDocumentsUseCase.execute() → ProcessingResult
"""

from typing import List

import pandas as pd

from core.exceptions import PDFExtractionError
from domain.contracts import DeclarationParserProtocol, TextExtractorProtocol
from domain.entities import ProcessingResult, Product, InvoiceDocument
from domain.value_objects import Quantity
from application.services.invoice_processor import InvoiceProcessor
from extractors.declaration_extractor import extract_declarations
from extractors.product_extractor import extraer_texto_pdf as legacy_extract_text


class ProcessDocumentsUseCase:
    """Caso de uso que orquesta el procesamiento de documentos DIM + facturas.

    Attributes:
        text_extractor: Servicio de extracción de texto de PDFs.
        declaration_parser: Servicio de parseo de declaraciones DIM.
        invoice_processor: Servicio de procesamiento de facturas.
        product_extractor: Servicio de extracción de productos DIM.
    """

    def __init__(
        self,
        text_extractor: TextExtractorProtocol,
        declaration_parser: DeclarationParserProtocol,
        invoice_processor: InvoiceProcessor,
        product_extractor=None,
    ) -> None:
        """Inicializa el caso de uso con las dependencias necesarias.

        Args:
            text_extractor: Implementación de TextExtractorProtocol.
            declaration_parser: Implementación de DeclarationParserProtocol.
            invoice_processor: Instancia de InvoiceProcessor.
            product_extractor: Instancia de ProductExtractor (opcional).
        """
        self.text_extractor = text_extractor
        self.declaration_parser = declaration_parser
        self.invoice_processor = invoice_processor
        self.product_extractor = product_extractor

    def execute(
        self,
        declaration_path: str,
        invoice_paths: List[str],
        declaration_filename: str = "",
        products: List[Product] | None = None,
    ) -> ProcessingResult:
        """Ejecuta el procesamiento completo de documentos.

        Extrae texto, parsea declaraciones, extrae productos de la
        declaración y procesa cada factura. Genera tanto las entidades
        de dominio como los datos raw completos para el frontend.

        Args:
            declaration_path: Ruta al PDF de la declaración DIM.
            invoice_paths: Lista de rutas a los PDFs de facturas.
            declaration_filename: Nombre del archivo de declaración (para metadatos).
            products: Lista de productos pre-procesados (opcional, se ignoran
                     si se proporciona product_extractor).

        Returns:
            ProcessingResult con declaraciones, productos, facturas y datos raw.

        Raises:
            PDFExtractionError: Si falla la extracción de texto de algún PDF.
        """
        declaration_text = self.text_extractor.extract_text(declaration_path)

        # Entidades de dominio (parseo básico: numero, fecha, proveedor)
        declarations = self.declaration_parser.parse(declaration_text)

        # Datos raw completos de declaraciones (columnas DIM)
        # Usa extraer_texto_pdf (PyMuPDF) porque extract_declarations fue
        # diseñado para el formato de un valor por línea que produce PyMuPDF.
        declarations_data: list[dict] = []
        try:
            legacy_text = legacy_extract_text(declaration_path)
            df_decl = extract_declarations(legacy_text)
            if not df_decl.empty:
                declarations_data = df_decl.where(
                    pd.notnull(df_decl), None
                ).to_dict(orient="records")
        except Exception:
            pass

        # Extraer productos y generar datos raw completos
        extracted_products: list[Product] = list(products or [])
        products_data: list[dict] = []
        if self.product_extractor and declaration_text:
            try:
                df_products = self.product_extractor.extract_products_from_text(
                    declaration_text, declaration_filename
                )
                if not df_products.empty:
                    products_data = df_products.where(
                        pd.notnull(df_products), None
                    ).to_dict(orient="records")
                    for _, row in df_products.iterrows():
                        try:
                            from decimal import Decimal
                            qty_val = row.get('Cantidad', 0) or 0
                            extracted_products.append(Product(
                                referencia=str(row.get('Referencia', '')),
                                descripcion=str(row.get('Producto', row.get('Description', ''))),
                                cantidad=Quantity(value=Decimal(str(int(float(qty_val))))),
                                unidad=str(row.get('Unidad', 'UND')),
                                pais_origen=str(row.get('Pais_Origen', None)),
                            ))
                        except Exception:
                            continue
            except Exception:
                pass

        invoices: list[InvoiceDocument] = []
        for invoice_path in invoice_paths:
            invoice_text = self.text_extractor.extract_text(invoice_path)
            invoices.append(self.invoice_processor.process(invoice_text))

        return ProcessingResult(
            declarations=declarations,
            products=extracted_products,
            invoices=invoices,
            declarations_data=declarations_data,
            products_data=products_data,
        )

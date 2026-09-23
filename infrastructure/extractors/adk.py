"""Extractor de facturas ADK para Clean Architecture.

Implementa BaseExtractor y se registra automáticamente en el
EXTRACTOR_REGISTRY bajo el nombre "adk".

El parsing de bloques de producto se delega a
extractors.factura_adk.procesar_factura_adk_text, que opera sobre el
texto ya extraído por TextExtractor.

Flujo de datos:
    texto crudo → AdkExtractor.extract() → InvoiceDocument
"""

import logging
import re
from decimal import Decimal

from core.exceptions import ExtractionError
from core.registry import register_extractor
from domain.entities import InvoiceDocument, InvoiceItem, InvoiceMetadata
from domain.value_objects import Money, Quantity
from extractors.factura_adk import extraer_metadata_adk, procesar_factura_adk_text
from infrastructure.extractors.base import BaseExtractor

logger = logging.getLogger("lector_declaraciones.extractors.adk")

_STRUCTURE_RE = re.compile(r"^\d{1,4}\s+[A-Z0-9\-/]+", re.MULTILINE)
_BRANDS_RE = re.compile(r"\b(?:GMB|NSK|KOYO|SKF|FAG)\b", re.IGNORECASE)


@register_extractor("adk")
class AdkExtractor(BaseExtractor):
    """Extractor de facturas ADK (rodamientos, marcas GMB/NSK/KOYO...)."""

    def can_process(self, text: str) -> bool:
        """Detecta facturas ADK: estructura LN+código y marca conocida.

        Args:
            text: Texto crudo extraído del PDF de la factura.

        Returns:
            True si el texto presenta la estructura de bloques ADK.
        """
        return bool(_STRUCTURE_RE.search(text) and _BRANDS_RE.search(text))

    def extract(self, text: str) -> InvoiceDocument:
        """Extrae metadata e items de la factura ADK.

        Args:
            text: Texto crudo del PDF de la factura.

        Returns:
            InvoiceDocument con metadata e items de la factura.

        Raises:
            ExtractionError: Si el documento no es procesable.
        """
        if not self.can_process(text):
            raise ExtractionError("Adk extractor cannot process this document")

        df = procesar_factura_adk_text(text)
        if df is None or df.empty:
            raise ExtractionError("No product blocks were recognized for ADK")

        meta = extraer_metadata_adk(text)
        moneda = meta["moneda"]

        items = []
        for _, row in df.iterrows():
            descripcion = str(row.get("Description") or "")
            marca = str(row.get("Brand") or "")
            if marca:
                descripcion = f"{descripcion} ({marca})" if descripcion else marca
            code_2 = str(row.get("Code_2") or "")
            if code_2:
                descripcion = f"{descripcion} [{code_2}]" if descripcion else code_2
            items.append(
                InvoiceItem(
                    referencia=str(row.get("Referencia") or ""),
                    descripcion=descripcion,
                    cantidad=Quantity(
                        value=Decimal(str(int(float(row.get("Cantidad") or 0))))
                    ),
                    unidad="UND",
                    valor_unitario=Money(
                        amount=Decimal(str(row.get("Precio_Unitario") or 0)),
                        currency=moneda,
                    ),
                    valor_total=Money(
                        amount=Decimal(str(row.get("Valor_Total") or 0)),
                        currency=moneda,
                    ),
                )
            )

        total_items = sum(item.valor_total.amount for item in items)
        total_mercancia = Decimal(str(meta["total_mercancia"]))
        total_factura = Decimal(str(meta["total_factura"]))
        metadata = InvoiceMetadata(
            num_factura=str(meta["num_factura"]),
            fecha_factura=str(meta["fecha_factura"]),
            proveedor="ADK",
            pais_origen=str(meta["pais_origen"]),
            incoterm=str(meta["incoterm"]),
            moneda=moneda,
            tipo_cambio=Decimal(str(meta["tipo_cambio"])),
            importador=str(meta["importador"]),
            total_mercancia=Money(amount=total_mercancia or total_items, currency=moneda),
            flete=Money(amount=Decimal(str(meta["flete"])), currency=moneda),
            seguro=Money(amount=Decimal(str(meta["seguro"])), currency=moneda),
            otros_gastos=Money(amount=Decimal(str(meta["otros_gastos"])), currency=moneda),
            total_factura=Money(amount=total_factura or total_items, currency=moneda),
        )

        logger.info("ADK invoice extracted with %d items", len(items))
        return InvoiceDocument(metadata=metadata, items=items)
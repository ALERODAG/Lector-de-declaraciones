"""Extractor de facturas SOFABEX para Clean Architecture.

Implementa BaseExtractor y se registra automáticamente en el
EXTRACTOR_REGISTRY bajo el nombre "sofabex".

Reutiliza íntegramente la lógica de parsing del módulo legacy
(extractors.factura_sofabex.procesar_factura_sofabex_text), de modo
que ninguna funcionalidad del formato original se pierde y el extractor
puede evolucionar de forma independiente.

Flujo de datos:
    texto crudo → procesar_factura_sofabex_text() → dict
    → SofabexExtractor.extract() → InvoiceDocument

Patrón de diseño: Strategy (register_extractor decorator)
"""

import logging
from decimal import Decimal

from core.exceptions import ExtractionError
from core.registry import register_extractor
from domain.entities import InvoiceDocument, InvoiceItem, InvoiceMetadata
from domain.value_objects import Money, Quantity
from extractors.factura_sofabex import procesar_factura_sofabex_text
from infrastructure.extractors.base import BaseExtractor

logger = logging.getLogger("lector_declaraciones.extractors.sofabex")


def _money(meta: dict, key: str, moneda: str, default="0.0") -> Money:
    """Convierte un valor numérico de metadata a Money de forma segura."""
    try:
        amount = Decimal(str(meta.get(key) or default))
    except Exception:
        amount = Decimal(default)
    return Money(amount=amount, currency=moneda)


@register_extractor("sofabex")
class SofabexExtractor(BaseExtractor):
    """Extractor de facturas SOFABEX que implementa ExtractorContract."""

    def can_process(self, text: str) -> bool:
        """Determina si el texto corresponde a una factura SOFABEX.

        Args:
            text: Texto crudo del PDF de la factura.

        Returns:
            True si el texto contiene "SOFABEX" (case-insensitive).
        """
        return "SOFABEX" in text.upper()

    def extract(self, text: str) -> InvoiceDocument:
        """Extrae metadata e items de la factura SOFABEX.

        Args:
            text: Texto crudo del PDF de la factura.

        Returns:
            InvoiceDocument con metadata e items de la factura.

        Raises:
            ExtractionError: Si el documento no es procesable o no se
                             encuentran líneas de factura.
        """
        if not self.can_process(text):
            raise ExtractionError("Sofabex extractor cannot process this document")

        resultado = procesar_factura_sofabex_text(text)
        if not resultado or not resultado["items"]:
            raise ExtractionError("No invoice lines were recognized for Sofabex")

        meta = resultado["metadata"]
        moneda = str(meta.get("moneda") or "EUR")

        items = []
        for prod in resultado["items"]:
            items.append(
                InvoiceItem(
                    referencia=str(prod.get("referencia") or ""),
                    descripcion=str(prod.get("descripcion") or ""),
                    cantidad=Quantity(value=Decimal(str(prod.get("cantidad") or 0))),
                    unidad=str(prod.get("unidad") or "UND"),
                    valor_unitario=Money(
                        amount=Decimal(str(prod.get("valor_unitario") or 0)),
                        currency=moneda,
                    ),
                    valor_total=Money(
                        amount=Decimal(str(prod.get("valor_total") or 0)),
                        currency=moneda,
                    ),
                )
            )

        if not items:
            raise ExtractionError("No invoice lines were recognized for Sofabex")

        total_mercancia = sum(item.valor_total.amount for item in items)
        total_flete = _money(meta, "flete", moneda).amount
        total_seguro = _money(meta, "seguro", moneda).amount
        total_otros = _money(meta, "otros_gastos", moneda).amount
        metadata = InvoiceMetadata(
            num_factura=str(meta.get("num_factura") or "N/A"),
            fecha_factura=str(meta.get("fecha_factura") or "N/A"),
            proveedor="SOFABEX",
            pais_origen=str(meta.get("pais_origen") or "FRANCIA"),
            incoterm=str(meta.get("incoterm") or "FOB"),
            moneda=moneda,
            tipo_cambio=Decimal(str(meta.get("tipo_cambio") or 1.0)),
            importador=str(meta.get("importador") or "N/A"),
            total_mercancia=Money(amount=total_mercancia, currency=moneda),
            flete=Money(amount=total_flete, currency=moneda),
            seguro=Money(amount=total_seguro, currency=moneda),
            otros_gastos=Money(amount=total_otros, currency=moneda),
            total_factura=Money(
                amount=total_mercancia + total_flete + total_seguro + total_otros,
                currency=moneda,
            ),
        )

        logger.info("Sofabex invoice extracted with %d items", len(items))
        return InvoiceDocument(metadata=metadata, items=items)

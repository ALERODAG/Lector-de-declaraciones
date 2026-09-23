"""Extractor de facturas GATE para Clean Architecture.

Implementa BaseExtractor y se registra automáticamente en el
EXTRACTOR_REGISTRY bajo el nombre "gate".

Reutiliza los patrones de parsing del módulo legacy
(extractors.facturas_gate) pero trabaja sobre el texto ya extraído
por TextExtractor, al igual que SofabexExtractor.

Flujo de datos:
    texto crudo → GateExtractor.extract() → InvoiceDocument
"""

import logging
import re
from decimal import Decimal

from core.exceptions import ExtractionError
from core.registry import register_extractor
from domain.entities import InvoiceDocument, InvoiceItem, InvoiceMetadata
from domain.value_objects import Money, Quantity
from extractors.facturas_gate import extract_header_fields, extract_product_lines
from infrastructure.extractors.base import BaseExtractor

logger = logging.getLogger("lector_declaraciones.extractors.gate")

_MARKER_RE = re.compile(
    r"(?:INVOICE\s+NO|SHIPMENT\s+NO|CUSTOMER\s+NO|PURCHASE\s+ORD\s+NO)",
    re.IGNORECASE,
)
_EA_LINE_RE = re.compile(r"^\d+\s+EA\s+[A-Z0-9]", re.MULTILINE)
_NUM_FACTURA_RE = re.compile(r"INVOICE\s+NO\.?\s*:?\s*([A-Z0-9\-]+)", re.IGNORECASE)


@register_extractor("gate")
class GateExtractor(BaseExtractor):
    """Extractor de facturas GATE (líneas con unidad EA)."""

    def can_process(self, text: str) -> bool:
        """Detecta facturas GATE por marcadores de encabezado o líneas EA.

        Args:
            text: Texto crudo extraído del PDF de la factura.

        Returns:
            True si el texto tiene marcadores típicos de una factura GATE.
        """
        return bool(_MARKER_RE.search(text) or _EA_LINE_RE.search(text))

    def extract(self, text: str) -> InvoiceDocument:
        """Extrae metadata e items de la factura GATE.

        Args:
            text: Texto crudo del PDF de la factura.

        Returns:
            InvoiceDocument con metadata e items de la factura.

        Raises:
            ExtractionError: Si el documento no es procesable.
        """
        if not self.can_process(text):
            raise ExtractionError("Gate extractor cannot process this document")

        header = extract_header_fields(text)
        products = extract_product_lines(text)

        if not products:
            raise ExtractionError("No product lines were recognized for Gate")

        items = [
            InvoiceItem(
                referencia=str(prod.get("Referencia") or ""),
                descripcion=str(prod.get("Description") or ""),
                cantidad=Quantity(value=Decimal(str(prod.get("Cantidad") or 0))),
                unidad="EA",
                valor_unitario=Money(
                    amount=Decimal(str(prod.get("Precio_Unitario") or 0)),
                    currency="USD",
                ),
                valor_total=Money(
                    amount=Decimal(str(prod.get("Valor_Total") or 0)),
                    currency="USD",
                ),
            )
            for prod in products
        ]

        num_factura = str(header.get("Invoice") or "")
        if not num_factura or num_factura == "N/A":
            match = _NUM_FACTURA_RE.search(text)
            if match:
                num_factura = match.group(1).strip()

        total = sum(item.valor_total.amount for item in items)
        metadata = InvoiceMetadata(
            num_factura=num_factura or "N/A",
            fecha_factura=str(header.get("Date") or "N/A"),
            proveedor="GATE",
            pais_origen="N/A",
            incoterm="N/A",
            moneda="USD",
            tipo_cambio=Decimal("1.0"),
            importador="N/A",
            total_mercancia=Money(amount=total, currency="USD"),
            flete=Money(amount=Decimal("0.0"), currency="USD"),
            seguro=Money(amount=Decimal("0.0"), currency="USD"),
            otros_gastos=Money(amount=Decimal("0.0"), currency="USD"),
            total_factura=Money(amount=total, currency="USD"),
        )

        logger.info("Gate invoice extracted with %d items", len(items))
        return InvoiceDocument(metadata=metadata, items=items)
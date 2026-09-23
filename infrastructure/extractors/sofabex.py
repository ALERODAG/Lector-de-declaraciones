"""Extractor de facturas SOFABEX para Clean Architecture.

Implementa BaseExtractor y se registra automáticamente en el
EXTRACTOR_REGISTRY bajo el nombre "sofabex".

Flujo de datos:
    texto crudo → SofabexExtractor.extract() → InvoiceDocument

Patrón de diseño: Strategy (register_extractor decorator)
"""

import logging
import re
from decimal import Decimal
from typing import cast

from core.registry import register_extractor
from domain.entities import InvoiceDocument, InvoiceItem, InvoiceMetadata
from domain.value_objects import Money, Quantity
from infrastructure.extractors.base import BaseExtractor, normalize_numeric_value
from core.exceptions import ExtractionError

logger = logging.getLogger("lector_declaraciones.extractors.sofabex")


def _extract_date(text: str) -> str:
    """Extrae la primera fecha en formato DD/MM/AAAA del texto.

    Args:
        text: Texto del PDF de la factura.

    Returns:
        Cadena con la fecha encontrada o "N/A".
    """
    match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    return match.group(1) if match else "N/A"


def _extract_invoice_number(text: str) -> str:
    """Extrae el número de factura (patrón: FACTURE N°/º: XXXXX).

    Args:
        text: Texto del PDF de la factura.

    Returns:
        Cadena con el número de factura o "N/A".
    """
    match = re.search(r"FACTURE\s+N[°º]?\s*[:]?\s*([A-Z0-9\-]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else "N/A"


def _extract_importer(text: str) -> str:
    """Extrae el nombre del importador (sección ADRESSE DE FACTURATION).

    Args:
        text: Texto del PDF de la factura.

    Returns:
        Cadena con el nombre del importador o "N/A".
    """
    match = re.search(r"ADRESSE DE FACTURATION\s*[:\n]+([^\n]+)", text, re.IGNORECASE)
    return match.group(1).strip() if match else "N/A"


def _parse_line(line: str) -> tuple[str, str, float, str, float, float] | None:
    """Parsea una línea de producto de factura SOFABEX.

    Formato esperado: "001 N300501 /N3005 POMPE ... 360,00 O 9,54 3 434,40"

    Args:
        line: Línea de texto del PDF.

    Returns:
        Tupla (referencia, descripcion, cantidad, unidad, valor_unitario, valor_total)
        o None si la línea no coincide con el patrón.
    """
    pattern = re.compile(
        r"^(\d{3})\s+(.+?)\s+([\d\s\.]+(?:[\.,]\d+)?)\s+([A-Z0-9]{1,3})\s+([\d\s\.]+(?:[\.,]\d+)?)\s+([\d\s\.]+(?:[\.,]\d+)?)$"
    )
    match = pattern.match(line)
    if not match:
        return None

    codigo_descripcion = match.group(2).strip()
    cantidad = normalize_numeric_value(match.group(3))
    unidad = match.group(4).strip()
    valor_unitario = normalize_numeric_value(match.group(5))
    valor_total = normalize_numeric_value(match.group(6))

    if " " in codigo_descripcion:
        referencia, descripcion = codigo_descripcion.split(" ", 1)
    else:
        referencia = codigo_descripcion
        descripcion = ""

    return referencia, descripcion, cantidad, unidad, valor_unitario, valor_total


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

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        items = []

        for line in lines:
            parsed = _parse_line(line)
            if parsed is None:
                continue

            referencia, descripcion, cantidad, unidad, valor_unitario, valor_total = parsed
            items.append(
                InvoiceItem(
                    referencia=referencia,
                    descripcion=descripcion,
                    cantidad=Quantity(value=Decimal(str(cantidad))),
                    unidad=unidad,
                    valor_unitario=Money(amount=Decimal(str(valor_unitario)), currency="EUR"),
                    valor_total=Money(amount=Decimal(str(valor_total)), currency="EUR"),
                )
            )

        if not items:
            raise ExtractionError("No invoice lines were recognized for Sofabex")

        metadata = InvoiceMetadata(
            num_factura=_extract_invoice_number(text),
            fecha_factura=_extract_date(text),
            proveedor="SOFABEX",
            pais_origen="FRANCIA",
            incoterm="FOB",
            moneda="EUR",
            tipo_cambio=Decimal("1.0"),
            importador=_extract_importer(text),
            total_mercancia=Money(amount=sum(item.valor_total.amount for item in items), currency="EUR"),
            flete=Money(amount=Decimal("0.0"), currency="EUR"),
            seguro=Money(amount=Decimal("0.0"), currency="EUR"),
            otros_gastos=Money(amount=Decimal("0.0"), currency="EUR"),
            total_factura=Money(amount=sum(item.valor_total.amount for item in items), currency="EUR"),
        )

        logger.info("Sofabex invoice extracted with %d items", len(items))
        return InvoiceDocument(metadata=metadata, items=items)

"""Extractor universal de facturas para Clean Architecture.

Se registra automáticamente en el EXTRACTOR_REGISTRY bajo el nombre
"universal" y actúa como último recurso cuando los extractores
específicos (sofabex, gate, adk) no reconocen el formato.

Procesa texto ya extraído detectando líneas de productos con
patrones genéricos (formato francés y análisis de tokens).

Flujo de datos:
    texto crudo → UniversalExtractor.extract() → InvoiceDocument
"""

import logging
import re
from decimal import Decimal

from core.exceptions import ExtractionError
from core.registry import register_extractor
from domain.entities import InvoiceDocument, InvoiceItem, InvoiceMetadata
from domain.value_objects import Money, Quantity
from extractors.facturas_gate import fallback_extract_line
from infrastructure.extractors.base import BaseExtractor
from utils.numeric_utils import parse_number

logger = logging.getLogger("lector_declaraciones.extractors.universal")

_PATRON_FR = re.compile(
    r"^(\d{1,3})\s+"  # Lg (001, 002, ...)
    r"([A-Z0-9\-]+)\s+"  # Code (N300501)
    r"/?([A-Z0-9\-]*)\s*"  # Article (opcional /N3005)
    r"(.+?)\s+"  # Libellé (descripción)
    r"([\d\s,\.]+?)\s+"  # Qté (cantidad)
    r"([A-Z\d])\s+"  # Unité (O, EA, PC ...)
    r"([\d,\.]+?)\s+"  # Prix unit
    r"([\d\s,\.]+)$"  # Montant HT
)


@register_extractor("universal")
class UniversalExtractor(BaseExtractor):
    """Extractor genérico de facturas para cualquier proveedor."""

    def can_process(self, text: str) -> bool:
        """Acepta cualquier texto que contenga contenido numérico.

        Args:
            text: Texto crudo extraído del PDF de la factura.

        Returns:
            True si el texto tiene algún dato numérico aprovechable.
        """
        return bool(re.search(r"\d", text))

    def _parse_line(self, line: str) -> dict | None:
        """Parsea una línea de producto con los patrones genéricos.

        Args:
            line: Línea de texto del PDF.

        Returns:
            Dict con datos del producto o None si no coincide.
        """
        match = _PATRON_FR.match(line)
        if match:
            cantidad = parse_number(match.group(5))
            precio = parse_number(match.group(7))
            total = parse_number(match.group(8))
            if cantidad is not None and precio is not None and total is not None:
                return {
                    "Referencia": match.group(2),
                    "Description": match.group(4).strip(),
                    "Unidad": match.group(6),
                    "Cantidad": cantidad,
                    "Precio_Unitario": precio,
                    "Valor_Total": total,
                }

        parsed = fallback_extract_line(line)
        return parsed

    def extract(self, text: str) -> InvoiceDocument:
        """Extrae metadata e items de la factura con patrones genéricos.

        Args:
            text: Texto crudo del PDF de la factura.

        Returns:
            InvoiceDocument con metadata e items de la factura.

        Raises:
            ExtractionError: Si no se reconoce ninguna línea de producto.
        """
        if not self.can_process(text):
            raise ExtractionError("Universal extractor cannot process this document")

        products: list[dict] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            parsed = self._parse_line(line)
            if parsed is not None:
                products.append(parsed)

        if not products:
            raise ExtractionError(
                "No product lines were recognized by the universal extractor"
            )

        items = [
            InvoiceItem(
                referencia=str(prod.get("Referencia") or ""),
                descripcion=str(prod.get("Description") or ""),
                cantidad=Quantity(value=Decimal(str(prod.get("Cantidad") or 0))),
                unidad=str(prod.get("Unidad") or "UND"),
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

        total = sum(item.valor_total.amount for item in items)
        metadata = InvoiceMetadata(
            num_factura="N/A",
            fecha_factura="N/A",
            proveedor="UNIVERSAL",
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

        logger.info("Universal invoice extracted with %d items", len(items))
        return InvoiceDocument(metadata=metadata, items=items)
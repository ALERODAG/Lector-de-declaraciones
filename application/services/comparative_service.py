"""Servicio de comparativo entre declaración de importación (DIM) y facturas.

Construye la información para la pestaña "Comparativo" del frontend:

1. Seguros por declaración:
   - Se toma el VALOR_FOB_USD de la DIM.
   - Se calcula el seguro esperado como FOB x FACTOR_SEGUROS.
   - Se compara contra el VALOR_SEGUROS_USD declarado en la DIM.

2. Cantidades por referencia:
   - Se cruzan las referencias de la DIM (products_data) contra las
     referencias de las facturas procesadas.
   - Solo se incluyen las referencias de la DIM que existen en la factura.
   - Cada fila compara la cantidad facturada vs la cantidad declarada.

Los valores se devuelven normalizados como cadenas decimales ("26559.09")
para evitar ambigüedad de formato numérico local en el frontend.
"""

from __future__ import annotations

import logging
from decimal import ROUND_HALF_UP, Decimal

logger = logging.getLogger("lector_declaraciones.comparative_service")

FACTOR_SEGUROS = Decimal("0.00085")
TOLERANCIA_MONEY = Decimal("0.01")


def _parse_decimal(val) -> Decimal | None:
    """Parsea un número en formato es-CO normalizado a Decimal.

    Soporta separadores de miles con '.' y decimales con ',' o '.'.
    Ejemplos: "26.559.09" -> 26559.09, "2.200" -> 2200, "22.58" -> 22.58.
    """
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return Decimal(str(val))
    s = str(val).strip().replace(" ", "").replace("$", "")
    if not s:
        return None
    try:
        if "," in s:
            s = s.replace(",", ".")
        if s.count(".") == 0:
            return Decimal(s)
        partes = s.split(".")
        if len(partes) == 2:
            if len(partes[1]) == 3:
                return Decimal(partes[0] + partes[1])
            return Decimal(partes[0] + "." + partes[1])
        s = "".join(partes[:-1]) + "." + partes[-1]
        return Decimal(s)
    except Exception:
        return None


def _es_decimal(val) -> bool:
    return _parse_decimal(val) is not None


def _normalizar_referencia(ref) -> str:
    """Normaliza una referencia para cruzar DIM vs factura.

    Ejemplos: "N300501/N3005" -> "N300501", "TCK1671/778260199" -> "TCK1671".
    """
    if not ref:
        return ""
    return str(ref).split("/")[0].strip().upper()


class ComparativeService:
    """Construye el comparativo DIM vs facturas."""

    def build(self, declarations_data, products_data, invoices) -> dict:
        """Genera el comparativo completo.

        Args:
            declarations_data: Lista de dicts con columnas DIM
                (VALOR_FOB_USD, VALOR_SEGUROS_USD, DECLARACION).
            products_data: Lista de dicts de productos DIM
                (Referencia, Cantidad).
            invoices: Lista de InvoiceDocument procesados.

        Returns:
            Dict con claves "seguros", "cantidades" y "factor_seguros".
        """
        return {
            "factor_seguros": str(FACTOR_SEGUROS),
            "seguros": self._build_seguros(declarations_data or []),
            "cantidades": self._build_cantidades(products_data or [], invoices or []),
        }

    def _build_seguros(self, declarations_data: list[dict]) -> list[dict]:
        filas: list[dict] = []
        for d in declarations_data:
            fob = _parse_decimal(d.get("VALOR_FOB_USD"))
            seguros = _parse_decimal(d.get("VALOR_SEGUROS_USD"))
            if fob is None:
                continue
            calculado = (fob * FACTOR_SEGUROS).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            declarado = seguros if seguros is not None else Decimal("0")
            diferencia = calculado - declarado
            match = abs(diferencia) <= TOLERANCIA_MONEY
            nombre = str(d.get("DECLARACION") or f"Declaración {len(filas) + 1}")

            filas.append(
                {
                    "declaracion": nombre,
                    "fob_usd": str(fob),
                    "seguros_calculado": str(calculado),
                    "seguros_declarado": f"{declarado:.2f}",
                    "diferencia": f"{diferencia:.2f}",
                    "match": match,
                }
            )
        return filas

    def _build_cantidades(self, products_data: list[dict], invoices) -> list[dict]:
        # Agrupar cantidades de factura por referencia normalizada
        factura_por_ref: dict[str, dict] = {}
        for invoice in invoices:
            for item in invoice.items or []:
                ref = _normalizar_referencia(item.referencia)
                if not ref:
                    continue
                acc = factura_por_ref.setdefault(
                    ref, {"cantidad": Decimal("0"), "referencia": ref}
                )
                qty_val = item.cantidad.value if item.cantidad else Decimal("0")
                acc["cantidad"] += qty_val

        # Agrupar cantidades DIM por referencia normalizada
        dim_por_ref: dict[str, dict] = {}
        for p in products_data or []:
            ref = _normalizar_referencia(p.get("Referencia"))
            if not ref:
                continue
            cant = _parse_decimal(p.get("Cantidad")) or Decimal("0")
            acc = dim_por_ref.setdefault(
                ref, {"cantidad": Decimal("0"), "referencia": ref}
            )
            acc["cantidad"] += cant

        # Cruzar: referencias DIM que existen en la factura
        filas: list[dict] = []
        for ref, dim in dim_por_ref.items():
            factura = factura_por_ref.get(ref)
            if factura is None:
                continue
            cant_dim = dim["cantidad"]
            cant_factura = factura["cantidad"]
            filas.append(
                {
                    "referencia": ref,
                    "cantidad_factura": f"{cant_factura:.4f}".rstrip("0").rstrip("."),
                    "cantidad_dim": f"{cant_dim:.4f}".rstrip("0").rstrip("."),
                    "match": abs(cant_factura - cant_dim) < 1,
                }
            )

        filas.sort(key=lambda r: r["referencia"])
        return filas

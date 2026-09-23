"""Objetos de valor inmutables del dominio.

Definen tipos de datos inmutables que representan conceptos
específicos del negocio con validación implícita.

- Quantity: Cantidad numérica con tipo Decimal para precisión.
- Money: Monto monetario con moneda asociada.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Quantity:
    """Objeto de valor inmutable que representa una cantidad numérica.

    Usa Decimal para evitar errores de precisión con puntos flotantes.

    Attributes:
        value: Valor de la cantidad como Decimal.
    """
    value: Decimal


@dataclass(frozen=True)
class Money:
    """Objeto de valor inmutable que representa un monto monetario.

    Attributes:
        amount: Monto como Decimal.
        currency: Código de moneda ISO 4217 (por defecto "EUR").
    """
    amount: Decimal
    currency: str = "EUR"

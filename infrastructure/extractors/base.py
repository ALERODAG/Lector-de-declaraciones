import re
from abc import ABC, abstractmethod
from typing import Any

from core.registry import register_extractor
from domain.contracts import ExtractorContract
from domain.entities import InvoiceDocument
from utils.numeric_utils import parse_number


class BaseExtractor(ABC, ExtractorContract):
    """Base extractor contract for invoice providers.

    Provides common interface for all invoice extractors following
    the Strategy pattern via the extractor registry.
    """

    @abstractmethod
    def can_process(self, text: str) -> bool:
        """Determina si este extractor puede procesar el texto dado.

        Args:
            text: Texto crudo extraído del PDF de la factura.

        Returns:
            True si este extractor reconoce el formato del documento.
        """
        ...

    @abstractmethod
    def extract(self, text: str) -> InvoiceDocument:
        """Extrae los datos de la factura del texto.

        Args:
            text: Texto crudo extraído del PDF de la factura.

        Returns:
            InvoiceDocument con metadata y items de la factura.

        Raises:
            ExtractionError: Si no se pueden extraer los datos.
        """
        ...


def normalize_numeric_value(raw_value: str) -> float:
    """Convierte un string numérico a float, normalizando separadores.

    Función wrapper que delega a utils.numeric_utils.parse_number().

    Args:
        raw_value: String con valor numérico (ej: "1.234,56", "1,234.56").

    Returns:
        Valor float convertido.

    Raises:
        ValueError: Si el valor no se puede convertir a número.
    """
    result = parse_number(raw_value)
    if result is None:
        raise ValueError(f"Cannot convert to numeric: {raw_value!r}")
    return result

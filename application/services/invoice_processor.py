"""Procesador de facturas que selecciona el extractor adecuado.

Itera sobre los extractores registrados en el EXTRACTOR_REGISTRY,
busca el que pueda procesar el texto dado y retorna el InvoiceDocument.

Flujo de datos:
    text → InvoiceProcessor.process() →ExtractorContract.extract() → InvoiceDocument
"""

import infrastructure.extractors  # noqa: F401
from core.registry import get_registered_extractors
from core.exceptions import ExtractionError
from domain.contracts import ExtractorContract
from domain.entities import InvoiceDocument


class InvoiceProcessor:
    """Procesador de facturas que delega al extractor correcto.

    Attributes:
        _registry: Diccionario de extractores registrados.
    """

    def __init__(self, extractor_registry: dict[str, type[ExtractorContract]] | None = None) -> None:
        """Inicializa el procesador con el registry de extractores.

        Args:
            extractor_registry: Diccionario opcional de extractores.
                Si es None, usa el EXTRACTOR_REGISTRY global.
        """
        self._registry = extractor_registry or get_registered_extractors()

    def process(self, text: str) -> InvoiceDocument:
        """Procesa el texto de una factura usando el extractor adecuado.

        Itera sobre los extractores registrados en orden de registro.
        El primer extractor que retorne True en can_process() se usa
        para extraer los datos.

        Args:
            text: Texto crudo extraído del PDF de la factura.

        Returns:
            InvoiceDocument con metadata e items de la factura.

        Raises:
            ExtractionError: Si ningún extractor puede procesar el documento.
        """
        for provider_name, extractor_cls in self._registry.items():
            extractor = extractor_cls()
            if extractor.can_process(text):
                return extractor.extract(text)

        raise ExtractionError("No extractor could process the invoice document")

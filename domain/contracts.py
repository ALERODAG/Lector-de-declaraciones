"""Contratos (interfaces) de dominio del sistema.

Define los protocolos (interfaces) que deben implementar los
servicios de extracción y parseo de documentos.

Estos contratos permiten el uso de dependency injection y
facilitan el testing con mocks.

Uso:
    class MiExtractor(ExtractorContract):
        def can_process(self, text: str) -> bool: ...
        def extract(self, text: str) -> InvoiceDocument: ...
"""

from __future__ import annotations

from typing import Protocol

from domain.entities import Declaration, InvoiceDocument


class TextExtractorProtocol(Protocol):
    """Protocolo para extractores de texto de PDFs.

    Los implementantes deben poder extraer texto crudo de archivos PDF.
    """

    def extract_text(self, path: str) -> str:
        """Extrae texto de un archivo PDF.

        Args:
            path: Ruta al archivo PDF.

        Returns:
            Cadena con el texto extraído.
        """
        ...


class DeclarationParserProtocol(Protocol):
    """Protocolo para parseadores de declaraciones DIM.

    Los implementantes deben poder convertir texto crudo en
    entidades Declaration.
    """

    def parse(self, text: str) -> list[Declaration]:
        """Parsea texto y extrae declaraciones.

        Args:
            text: Texto crudo del PDF de declaración.

        Returns:
            Lista de Declaration extraídas.
        """
        ...


class ExtractorContract(Protocol):
    """Protocolo para extractores de facturas.

    Los implementantes deben poder determinar si pueden procesar
    un documento y extraer sus datos.
    """

    def can_process(self, text: str) -> bool:
        """Determina si este extractor puede procesar el texto.

        Args:
            text: Texto crudo del PDF de la factura.

        Returns:
            True si el extractor reconoce el formato del documento.
        """
        ...

    def extract(self, text: str) -> InvoiceDocument:
        """Extrae los datos de la factura del texto.

        Args:
            text: Texto crudo del PDF de la factura.

        Returns:
            InvoiceDocument con metadata e items.
        """
        ...

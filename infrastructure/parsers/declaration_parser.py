"""Parser de declaraciones de importación para la capa de Clean Architecture.

Implementa DeclarationParserProtocol para extraer entidades Declaration
desde texto crudo de PDFs de declaraciones DIM.

Flujo de datos:
    texto crudo → DeclarationParser.parse() → list[Declaration]
"""

import re
import logging
from typing import List

from domain.contracts import DeclarationParserProtocol
from domain.entities import Declaration
from core.exceptions import ApplicationError

logger = logging.getLogger("lector_declaraciones.parsers.declaration")


def _normalize_space(text: str) -> str:
    """Normaliza espacios múltiples a uno solo y elimina bordes.

    Args:
        text: Texto a normalizar.

    Returns:
        Texto con espacios múltiples reducidos a uno y sin espacios al inicio/final.
    """
    return re.sub(r"\s+", " ", text).strip()


def _extract_dates(text: str) -> str:
    """Extrae la primera fecha del texto.

    Soporta formatos:
    - DD/MM/AAAA (ej: 16/10/2025)
    - YYYY MM DD (ej: 2025 10 16)
    - YYYY-MM-DD (ej: 2025-10-16)

    Args:
        text: Texto donde buscar la fecha.

    Returns:
        Cadena con la fecha encontrada o "N/A" si no se encuentra ninguna.
    """
    # Formato DD/MM/AAAA
    match = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if match:
        return match.group(1)

    # Formato YYYY MM DD o YYYY-MM-DD
    match = re.search(r"(\d{4})\s*[-/]\s*(\d{2})\s*[-/]\s*(\d{2})", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    # Formato YYYY MM DD con espacios (ej: "2025 10 16")
    match = re.search(r"\b(\d{4})\s+(\d{2})\s+(\d{2})\b", text)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    return "N/A"


class DeclarationParser(DeclarationParserProtocol):
    """Parser que convierte texto de declaraciones DIM en entidades Declaration."""

    def parse(self, text: str) -> List[Declaration]:
        """Parsea el texto y extrae todas las declaraciones de importación.

        Busca todos los patrones "DECLARACION X DE Y" con finditer y
        extrae el contenido entre cada match y el siguiente.

        Args:
            text: Texto completo del PDF de declaración de importación.

        Returns:
            Lista de entidades Declaration extraídas.

        Raises:
            ApplicationError: Si el texto de entrada está vacío.
        """
        if not text or not text.strip():
            raise ApplicationError("Declaration text cannot be empty")

        pattern = re.compile(r"DECLARACION\s+(\d+)\s+DE\s+(\d+)", re.IGNORECASE)
        matches = list(pattern.finditer(text))
        declarations: list[Declaration] = []

        for i, match in enumerate(matches):
            numero = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            block_text = text[start:end].strip()

            declarations.append(
                Declaration(
                    numero=numero,
                    fecha=_extract_dates(block_text),
                    proveedor="DECLARACION",
                    raw=_normalize_space(block_text),
                )
            )

        logger.info("Parsed %d declarations", len(declarations))
        return declarations

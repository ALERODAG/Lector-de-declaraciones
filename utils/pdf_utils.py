"""Utilidades para extracción de texto de PDFs.

Funciones delegadas a infrastructure.pdf.text_extractor para mantener
un único punto de extracción en todo el proyecto.
"""

from infrastructure.pdf.text_extractor import extract_text_from_pdf


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extrae texto completo de un archivo PDF.

    Args:
        ruta_pdf: Ruta absoluta o relativa al archivo PDF.

    Returns:
        Cadena con el texto extraído de todas las páginas del PDF.

    Raises:
        FileNotFoundError: Si el archivo en ruta_pdf no existe.
    """
    return extract_text_from_pdf(ruta_pdf)

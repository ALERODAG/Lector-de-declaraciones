"""Servicio de OCR usando Tesseract.

Proporciona extracción de texto de PDFs escaneados mediante
reconocimiento óptico de caracteres (OCR) usando Tesseract.

Flujo de datos:
    PDF → fitz (convertir a imagen) → pytesseract → texto

Requisitos:
    - pytesseract instalado (pip install pytesseract)
    - Tesseract OCR instalado en el sistema
    - PyMuPDF para conversión de páginas a imágenes
"""

import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger("lector_declaraciones.ocr")

try:
    import pytesseract  # type: ignore
except ImportError:  # pragma: no cover
    pytesseract = None


class TesseractOCRService:
    """Servicio de OCR que extrae texto de PDFs escaneados."""

    def extract_text_from_pdf(self, path: str) -> str:
        """Extrae texto de un PDF usando OCR (Tesseract).

        Convierte cada página del PDF a una imagen y luego aplica
        OCR para extraer el texto.

        Args:
            path: Ruta al archivo PDF a procesar.

        Returns:
            Cadena con el texto extraído de todas las páginas.

        Raises:
            RuntimeError: Si pytesseract o PyMuPDF no están instalados.
            FileNotFoundError: Si el archivo no existe.
        """
        if pytesseract is None:
            raise RuntimeError("pytesseract is not installed")

        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"OCR file not found: {path}")

        try:
            from fitz import open as open_document
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("PyMuPDF is required for OCR image extraction") from exc

        content = []
        with open_document(path) as document:
            for page in document:
                pix = page.get_pixmap(dpi=200)
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(image, lang="spa+eng")
                content.append(text)

        logger.info("OCR extracted text from PDF (%s pages).", len(content))
        return "\n".join(content)

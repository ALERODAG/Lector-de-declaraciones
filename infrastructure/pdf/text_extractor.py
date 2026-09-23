import logging
from pathlib import Path

import pdfplumber

from core.exceptions import OCRFallbackError, PDFExtractionError
from domain.contracts import TextExtractorProtocol
from infrastructure.config import AppSettings
from infrastructure.ocr.tesseract_service import TesseractOCRService

logger = logging.getLogger("lector_declaraciones.pdf")


def extract_text_from_pdf(path: str) -> str:
    """Extrae texto de un PDF usando pdfplumber. Función standalone sin dependencia de AppSettings.

    Args:
        path: Ruta al archivo PDF a extraer.

    Returns:
        Texto completo extraído del PDF concatenando todas las páginas.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    texto = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            texto.append(page_text)

    return "\n".join(texto)


class PDFTextExtractor(TextExtractorProtocol):
    """Extractor de texto de PDF con fallback a OCR.

    Implementa TextExtractorProtocol. Intenta extraer texto con pdfplumber
    y si el resultado está vacío o falla, usa Tesseract OCR como fallback.

    Attributes:
        settings: Configuración de la aplicación.
        ocr_service: Servicio de OCR para fallback.
    """

    def __init__(self, settings: AppSettings, ocr_service: TesseractOCRService | None = None) -> None:
        """Inicializa el extractor con configuración y servicio OCR opcional.

        Args:
            settings: Configuración de la aplicación (AppSettings).
            ocr_service: Servicio OCR opcional. Si es None, crea uno nuevo.
        """
        self.settings = settings
        self.ocr_service = ocr_service or TesseractOCRService()

    def extract_text(self, path: str) -> str:
        """Extrae texto de un PDF con fallback a OCR.

        Args:
            path: Ruta al archivo PDF.

        Returns:
            Texto extraído del PDF.

        Raises:
            PDFExtractionError: Si el path no existe o la extracción falla
                               y OCR está deshabilitado.
        """
        path_obj = Path(path)
        if not path_obj.exists():
            raise PDFExtractionError(f"PDF path does not exist: {path}")

        try:
            texto = self._extract_text_with_pdfplumber(path)
            if texto.strip():
                return texto

            if self.settings.ocr_enabled:
                return self.ocr_service.extract_text_from_pdf(path)

            raise PDFExtractionError("PDF text extraction produced empty output")
        except PDFExtractionError:
            raise
        except Exception as exc:
            logger.warning("PDF extraction failed, attempting OCR fallback: %s", exc)
            if self.settings.ocr_enabled:
                return self.ocr_service.extract_text_from_pdf(path)
            raise PDFExtractionError("Failed to extract text from PDF and OCR fallback is disabled") from exc

    def _extract_text_with_pdfplumber(self, path: str) -> str:
        """Extrae texto usando pdfplumber (sin OCR).

        Args:
            path: Ruta al archivo PDF.

        Returns:
            Texto concatenado de todas las páginas.
        """
        texto = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                texto.append(page_text)

        return "\n".join(texto)

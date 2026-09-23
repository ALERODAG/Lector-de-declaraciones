"""Configuración legacy de rutas del proyecto.

NOTA: Esta configuración está migrada a infrastructure/config.py (AppSettings).
Este módulo se mantiene por compatibilidad con código legacy que lo importa.

Uso recomendado:
    from infrastructure.config import AppSettings
    settings = AppSettings()
    settings.pdf_directory  # en vez de PDF_DIRECTORY
    settings.output_dir     # en vez de OUTPUT_DIR
    settings.csv_headers    # en vez de HEADERS
"""

import os
from infrastructure.config import AppSettings

# Obtener configuración de la fuente centralizada
_settings = AppSettings()

# Constantes legacy para compatibilidad
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PDF_DIRECTORY = os.path.join(BASE_PATH, "..", _settings.pdf_directory)
OUTPUT_DIR = os.path.join(BASE_PATH, "..", _settings.output_dir)
HEADERS = _settings.csv_headers

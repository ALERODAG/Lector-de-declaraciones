"""Configuración centralizada de la aplicación usando Pydantic Settings.

Lee las variables de entorno desde el archivo .env y las convierte
en un objeto tipado AppSettings. Esta es la fuente única de configuración
para todo el proyecto.

Uso:
    from infrastructure.config import AppSettings
    settings = AppSettings()
    print(settings.log_level)
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class AppSettings(BaseSettings):
    """Configuración centralizada de la aplicación.

    Attributes:
        app_name: Nombre de la aplicación.
        app_version: Versión actual de la aplicación.
        environment: Entorno de ejecución (development, production, testing).
        cors_allowed_origins: Lista de orígenes permitidos para CORS.
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file_path: Ruta al archivo de logs.
        log_backup_count: Número de archivos de respaldo de logs a mantener.
        ocr_enabled: Habilitar OCR como fallback de extracción de texto.
        ocr_engine: Motor OCR a usar (tesseract).
        temp_directory: Directorio para archivos temporales.
        allow_origins: Lista de orígenes permitidos para CORS (alias de cors_allowed_origins).
        pdf_directory: Directorio donde se encuentran los PDFs a procesar.
        output_dir: Directorio de salida para resultados procesados.
        csv_headers: Lista de encabezados para columnas CSV (Columna1-Columna90).
    """

    app_name: str = "lector_declaraciones"
    app_version: str = "1.0.0"
    environment: str = "development"
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    log_level: str = "INFO"
    log_file_path: str = "logs/app.log"
    log_backup_count: int = 7
    ocr_enabled: bool = True
    ocr_engine: str = "tesseract"
    temp_directory: str = "/tmp"
    allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Configuración de rutas (migrado de config/settings.py)
    pdf_directory: str = Field(default="PDF_A_LEER")
    output_dir: str = Field(default="PDF_A_LEER/EXCEL_PDF_LEIDOS")
    csv_headers: list[str] = Field(default_factory=lambda: [f"Columna{i}" for i in range(1, 91)])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )

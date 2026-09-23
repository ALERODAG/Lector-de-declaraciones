"""Configuración de logging con formato JSON y rotación de archivos.

Proporciona logging estructurado en formato JSON para facilitar
el monitoreo y análisis de logs en producción.

Flujo:
    AppSettings → configure_logging() → handlers (consola + archivo)
"""

import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any

from infrastructure.config import AppSettings

# python-json-logger es opcional: si no está instalado, se usa un formato
# estándar y la aplicación arranca igualmente.
try:
    from pythonjsonlogger import jsonlogger  # type: ignore[import-not-found]
except ImportError:
    jsonlogger = None

# Los nombres en fmt deben ser atributos ORIGINALES del LogRecord
# (asctime, levelname, ...). El rename se aplica al serializar a JSON.
JSON_FMT = "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s"
JSON_RENAME_FIELDS = {"asctime": "timestamp", "levelname": "level"}
JSON_DATEFMT = "%Y-%m-%dT%H:%M:%S%z"
STD_FMT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s [correlation_id=%(correlation_id)s]"


class CorrelationIdFilter(logging.Filter):
    """Filtro que agrega correlation_id a cada registro de log.

    Si el registro no tiene correlation_id, asigna "unknown".
    Útil para rastrear requests a través de múltiples servicios.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Aplica el filtro al registro de log.

        Args:
            record: Registro de log a filtrar.

        Returns:
            Siempre True (no descarta registros, solo agrega campos).
        """
        record.correlation_id = getattr(record, "correlation_id", "unknown")
        return True


def _build_formatter_definition() -> dict[str, Any]:
    """Devuelve la definición del formatter para logging.config.dictConfig.

    Usa JsonFormatter si python-json-logger está disponible; en caso
    contrario usa el Formatter estándar de logging.

    Returns:
        Diccionario con la configuración del formatter.
    """
    if jsonlogger is not None:
        return {
            "()": jsonlogger.JsonFormatter,
            "fmt": JSON_FMT,
            "rename_fields": JSON_RENAME_FIELDS,
            "datefmt": JSON_DATEFMT,
        }
    return {
        "format": STD_FMT,
    }


def configure_logging(settings: AppSettings) -> None:
    """Configura el sistema de logging.

    Crea dos handlers:
    - Console: Para logs en tiempo real (desarrollo).
    - File: Para logs persistentes con rotación diaria (producción).

    Si python-json-logger no está instalado, usa un formato estándar
    (texto plano) para no impedir el arranque de la aplicación.

    Args:
        settings: Configuración de la aplicación con log_level,
                  log_file_path y log_backup_count.
    """
    log_path = Path(settings.log_file_path)
    if log_path.parent and not log_path.parent.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "correlation_id": {
                "()": CorrelationIdFilter,
            }
        },
        "formatters": {
            "app": _build_formatter_definition(),
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "app",
                "level": settings.log_level,
                "filters": ["correlation_id"],
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "app",
                "when": "midnight",
                "backupCount": settings.log_backup_count,
                "filename": settings.log_file_path,
                "encoding": "utf-8",
                "delay": True,
                "level": settings.log_level,
                "filters": ["correlation_id"],
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": settings.log_level,
        },
    }

    logging.config.dictConfig(config)

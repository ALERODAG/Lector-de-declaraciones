"""Extractor de declaraciones de importación desde texto PDF.

Convierte el texto crudo extraído de un PDF de declaración DIM en un
DataFrame pandas con las columnas renombradas según el mapeo del
archivo column_maps.py.

Flujo de datos:
    texto PDF → separar_declaraciones() → limpiar_lineas() → DataFrame
"""

import pandas as pd
from constants.column_maps import COLUMN_RENAMES
from utils.text_utils import separar_declaraciones, limpiar_lineas
from config.settings import HEADERS


def extract_declarations(texto: str) -> pd.DataFrame:
    """Extrae declaraciones de importación del texto y las convierte en DataFrame.

    Separa el texto en bloques de declaraciones, limpia cada línea,
    las organiza en columnas según HEADERS y renombra las columnas
    usando COLUMN_RENAMES.

    Args:
        texto: Texto completo extraído del PDF de declaración de importación.

    Returns:
        DataFrame pandas con las declaraciones extraídas y columnas renombradas.
        Retorna DataFrame vacío si no se encuentran declaraciones.
    """
    declaraciones = separar_declaraciones(texto)
    all_rows = []
    for decl in declaraciones:
        lines = limpiar_lineas(decl["contenido"])
        row = lines[:len(HEADERS)] + [None] * max(0, len(HEADERS) - len(lines))
        all_rows.append(row)

    if all_rows:
        return (
            pd.DataFrame(all_rows, columns=HEADERS)
            .dropna(axis=1, how="all")
            .rename(columns=COLUMN_RENAMES)
        )
    return pd.DataFrame()

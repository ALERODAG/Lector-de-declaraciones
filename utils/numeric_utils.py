"""Utilidades centralizadas para conversión y parsing de valores numéricos.

Soporta formatos:
- Europeo: 1.234,56 (punto separador miles, coma decimal)
- Americano: 1,234.56 (coma separador miles, punto decimal)
- Con espacios: 1 234,56 (espacio separador miles, coma decimal)
"""

import re


def parse_number(value) -> float | None:
    """Convierte un valor a float, manejando múltiples formatos numéricos internacionales.

    Detecta automáticamente si el separador decimal es coma o punto
    basándose en la posición relativa de ambos caracteres.

    Args:
        value: Valor a convertir. Puede ser str, int, float, o None.

    Returns:
        Número float convertido, o None si el valor es None, vacío, o no convertible.

    Examples:
        >>> parse_number("1.234,56")
        1234.56
        >>> parse_number("1,234.56")
        1234.56
        >>> parse_number("1 234,56")
        1234.56
        >>> parse_number("42.5")
        42.5
    """
    if value is None:
        return None

    texto = str(value).strip()
    if not texto or texto.lower() == "none":
        return None

    # Si ya es número, retornar directamente
    if isinstance(value, (int, float)):
        return float(value)

    # Limpiar caracteres no numéricos excepto dígitos, comas, puntos y guiones
    texto = texto.replace(" ", "").replace("\u00A0", "")
    texto = re.sub(r"[^0-9,\.\-]", "", texto)

    if not texto:
        return None

    puntos = texto.count(".")
    comas = texto.count(",")

    # Caso 1: Formato europeo con espacio como miles (1 234,56)
    # Ya se limpiaron los espacios arriba
    if comas == 1 and puntos == 0:
        # Solo coma -> asumir decimal europeo
        texto = texto.replace(",", ".")
    elif puntos > 0 and comas > 0:
        # Determinar cuál es el separador decimal (el último)
        pos_punto = texto.rfind(".")
        pos_coma = texto.rfind(",")

        if pos_punto > pos_coma:
            # Formato americano: 1,234.56
            texto = texto.replace(",", "")
        else:
            # Formato europeo: 1.234,56
            texto = texto.replace(".", "").replace(",", ".")
    elif puntos > 1 and comas == 0:
        # Múltiples puntos: 1.234.567 -> 1234567 (todos son separadores de miles)
        parts = texto.rsplit(".", 1)
        texto = parts[0].replace(".", "") + "." + parts[1]

    try:
        return float(texto)
    except (ValueError, TypeError):
        return None

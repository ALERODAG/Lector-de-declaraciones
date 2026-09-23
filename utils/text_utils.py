"""Utilidades para procesamiento de texto de declaraciones de importación.

Proporciona funciones para separar y limpiar el contenido de declaraciones
DIM (Declaración de Importación) extraído de archivos PDF.
"""

import re

_RE_DECLARACION = re.compile(r"DECLARACION\s+(\d+)\s+DE\s+(\d+)", re.IGNORECASE)


def separar_declaraciones(texto: str, fin_delim: str = "^DO  LAC$") -> list:
    """Separa el texto completo en bloques individuales de declaraciones.

    Busca todas las declaraciones usando el patrón "DECLARACION X DE Y" y
    extrae el contenido entre cada declaración y el delimitador de fin o la
    siguiente declaración.

    Args:
        texto: Texto completo extraído del PDF de declaración de importación.
        fin_delim: Delimitador de fin de cada bloque de declaración.
                   Por defecto "^DO  LAC$".

    Returns:
        Lista de diccionarios ordenada por número de declaración, donde cada
        diccionario tiene:
            - numero (int): Número secuencial de la declaración.
            - contenido (str): Texto completo de la declaración incluyendo
                               la etiqueta "DECLARACION X DE Y".
    """
    matches = list(_RE_DECLARACION.finditer(texto))
    fin_re = re.compile(re.escape(fin_delim), re.IGNORECASE)
    declaraciones = []
    for i, match in enumerate(matches):
        numero = int(match.group(1))
        start = match.start()
        fin_match = fin_re.search(texto, start)
        if fin_match:
            end = fin_match.end()
        elif i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(texto)
        declaraciones.append({"numero": numero, "contenido": texto[start:end].strip()})
    return sorted(declaraciones, key=lambda x: x["numero"])


def limpiar_lineas(texto: str) -> list:
    """Limpia y normaliza las líneas de texto de una declaración.

    Elimina espacios en blanco al inicio/final, reemplaza comas por puntos
    (normalización numérica) y elimina líneas vacías.

    Args:
        texto: Texto crudo de una declaración individual.

    Returns:
        Lista de strings con las líneas limpiadas y sin líneas vacías.
    """
    return [line.replace(",", ".") for line in
            (l.strip() for l in texto.splitlines()) if line]

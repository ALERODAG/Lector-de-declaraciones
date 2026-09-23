"""Registro centralizado de extractores de facturas.

Implementa el patrón Registry para registrar y recuperar extractores
de facturas de forma dinámica. Los extractores se registran usando
el decorador @register_extractor("nombre").

Uso:
    from core.registry import register_extractor, get_registered_extractors

    @register_extractor("mi_extractor")
    class MiExtractor(BaseExtractor):
        ...

    extractors = get_registered_extractors()  # {"mi_extractor": MiExtractor}
"""

from typing import Any, Callable, Dict, Type

# Diccionario global que almacena los extractores registrados.
# Clave: nombre del extractor (str), Valor: clase del extractor (Type)
EXTRACTOR_REGISTRY: Dict[str, Type[Any]] = {}


def register_extractor(name: str) -> Callable[[Type[Any]], Type[Any]]:
    """Decorador que registra un extractor en el EXTRACTOR_REGISTRY.

    Args:
        name: Nombre único del extractor (ej: "sofabex", "gate").

    Returns:
        Decorador que agrega la clase al registry y la retorna sin modificar.
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        EXTRACTOR_REGISTRY[name] = cls
        return cls

    return decorator


def get_registered_extractors() -> Dict[str, Type[Any]]:
    """Retorna una copia del diccionario de extractores registrados.

    Returns:
        Diccionario con los extractores disponibles. No modifica el original.
    """
    return dict(EXTRACTOR_REGISTRY)

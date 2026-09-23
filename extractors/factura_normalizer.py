"""Normalizador de campos de items de facturas.

Proporciona funciones para normalizar los nombres de campos extraídos
por diferentes extractores a un formato estándar (snake_case).

Flujo de datos:
    items con nombres variados → normalizar_items() → items con nombres estandarizados
"""

MAPEO_CAMPOS = {
    "cantidad": [
        "cantidad",
        "Cantidad",
        "qty",
        "quantity",
        "quantite",
    ],

    "valor_unitario": [
        "valor_unitario",
        "Precio_Unitario",
        "unit_price",
        "precio_unitario",
        "prix_unitaire",
    ],

    "valor_total": [
        "valor_total",
        "Valor_Total",
        "total",
        "importe",
        "montant_total",
    ],

    "descripcion": [
        "descripcion",
        "Description",
        "description",
    ],

    "referencia": [
        "referencia",
        "Referencia",
        "reference",
    ],
}


def normalizar_item(item: dict) -> dict:
    """Normaliza un item de factura usando MAPEO_CAMPOS.

    Busca cada campo estándar en las diferentes variantes de nombre
    soportadas y retorna un diccionario con claves normalizadas.

    Args:
        item: Diccionario con los campos extraidos por el extractor.
              Las claves pueden variar según el proveedor.

    Returns:
        Diccionario con claves normalizadas en snake_case:
        cantidad, valor_unitario, valor_total, descripcion, referencia.
    """
    item_normalizado: dict = {}

    for campo_estandar, aliases in MAPEO_CAMPOS.items():
        valor: object = None

        for alias in aliases:
            if alias in item:
                valor = item[alias]
                break

        item_normalizado[campo_estandar] = valor

    return item_normalizado


def normalizar_items(items: list[dict]) -> list[dict]:
    """Normaliza una lista de items de factura.

    Args:
        items: Lista de diccionarios con items de factura.

    Returns:
        Lista de diccionarios normalizados.
    """
    return [normalizar_item(it) for it in items]

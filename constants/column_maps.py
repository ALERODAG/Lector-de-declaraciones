"""Mapeo de columnas de declaraciones de importación (DIM).

Define el mapeo de nombres genéricos (Columna1, Columna2, ...) a
nombres descriptivos del dominio (DECLARACION, AÑO, NIT_YADAS, ...).

Este mapeo se usa en extractors/declaration_extractor.py para
renombrar las columnas del DataFrame resultante.

Flujo de datos:
    DataFrame(Columna1..Columna90) → rename(COLUMN_RENAMES) → DataFrame(DECLARACION, AÑO, ...)
"""

COLUMN_RENAMES = {
    "Columna1":  "DECLARACION",
    "Columna2":  "AÑO",
    "Columna3":  "NIT_YADAS",
    "Columna4":  "NUMERO_DE_VERIFICACION",
    "Columna5":  "APELLIDO_Y_O_RAZON_SOCIAL",
    "Columna6":  "DIRECCION",
    "Columna7":  "TELEFONO",
    "Columna8":  "COD_ADMINISTRACION",
    "Columna9":  "COD_DEPARTAMENTO",
    "Columna10": "COD_MUNICIPIO",
    "Columna11": "NIT_DECLARANTE",
    "Columna12": "NUMERO_VERIFICACION_DECLARANTE",
    "Columna13": "RAZON_SOCIAL_DECLARANTE",
    "Columna14": "TIPO_DE_USUARIO",
    "Columna15": "COD_USUARIO",
    "Columna16": "NUMERO_DE_DOCUMENTO",
    "Columna17": "NOMBRES_Y_APELLIDOS",
    "Columna18": "CLASE_IMPORTADOR",
    "Columna19": "TIPO_DECLARACION",
    "Columna20": "COD_DECLARACION",
    "Columna21": "FORMATO_ANTERIOR",
    "Columna22": "AÑO_MES_DIA",
    "Columna23": "DECLARACION_DE_EXPORTACION",
    "Columna24": "AÑO_MES_DIA2",
    "Columna54": "EMPRESA_TRANSPORTADORA",
    "Columna57": "SUBPARTIDA_ARANCELARIA",
    "Columna68": "COD_PAIS_EXPORTADOR",
    "Columna69": "PESO_BRUTO",
    "Columna70": "DMS_PESO_BRUTO_KG",
    "Columna71": "PESO_NETO_KG",
    "Columna72": "DMS_PESO_NETO_KG",
    "Columna73": "CODIGO_EMBALAJE",
    "Columna74": "NUMERO_BULTOS",
    "Columna75": "SUBPARTIDAS",
    "Columna76": "COD_UNIDAD_CAL",
    "Columna77": "CANTIDAD",
    "Columna78": "DMS_CANTIDAD",
    "Columna79": "VALOR_FOB_USD",
    "Columna80": "VALOR_FLETES_USD",
    "Columna81": "VALOR_SEGUROS_USD",
    "Columna82": "VALOR_OTROS_GASTOS",
    "Columna83": "SUMATORIA_FLETES_SEGUROS_OTROS_USD",
    "Columna84": "AJUSTE_VALOR_USD",
    "Columna85": "VALOR_ADUANA_USD",
    "Columna88": "COD_OFICINA",
}

# Columnas que NO deben extraerse de las declaraciones
COLUMNAS_PROHIBIDAS = {
    "Moneda", "Valor_FOB", "Incoterm", "Peso_Neto", "Peso_Bruto", "API", "ACEA"
}

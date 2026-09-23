# =================================
#   factura_universal.py
#   Parser universal inteligente para cualquier formato de factura
#
#   Flujo de datos:
#       pdf_path → extraer_tabla_inteligente() → DataFrame con productos
#
#   Soporta: español, francés, inglés. Detecta columnas automáticamente.
#   Último recurso cuando los extractores específicos no reconocen el formato.
# =================================

import pdfplumber
import pandas as pd
import re
from typing import Dict, List, Optional

from utils.numeric_utils import parse_number as convertir_numero

# -----------------------------
#   MAPEO DE COLUMNAS
# -----------------------------
COLUMN_MAPPINGS = {
    # Spanish
    "l/n": "Line_Number",
    "línea": "Line_Number",
    "ln": "Line_Number",
    "nº": "Line_Number",
    "num": "Line_Number",
    "numero": "Line_Number",
    "número": "Line_Number",
    "codigo": "Referencia",
    "código": "Referencia",
    "code": "Referencia",
    "ref": "Referencia",
    "referencia": "Referencia",
    "codigo 2": "Code_2",
    "código 2": "Code_2",
    "codigo2": "Code_2",
    "descripcion": "Description",
    "descripción": "Description",
    "desc": "Description",
    "nombre": "Description",
    "marca": "Brand",
    "cantidad": "Cantidad",
    "cant": "Cantidad",
    "qtd": "Cantidad",
    "precio": "Precio_Unitario",
    "precio unitario": "Precio_Unitario",
    "precio unit": "Precio_Unitario",
    "p.u": "Precio_Unitario",
    "pu": "Precio_Unitario",
    "importe": "Valor_Total",
    "total": "Valor_Total",
    "subtotal": "Valor_Total",
    "montante": "Valor_Total",
    
    # French
    "lg": "Line_Number",
    "ligne": "Line_Number",
    "code article": "Referencia",
    "article": "Code_2",
    "libellé": "Description",
    "libelle": "Description",
    "qté": "Cantidad",
    "qte": "Cantidad",
    "quantité": "Cantidad",
    "qt": "Cantidad",
    "unité": "Unit",
    "unite": "Unit",
    "u": "Unit",
    "prix unit": "Precio_Unitario",
    "prix unit.": "Precio_Unitario",
    "prix unitaire": "Precio_Unitario",
    "pu": "Precio_Unitario",
    "p.u.": "Precio_Unitario",
    "c/m": "CM",
    "montant ht": "Valor_Total",
    "montant": "Valor_Total",
    "amount": "Valor_Total",
    "amount ht": "Valor_Total",
    "total ht": "Valor_Total",
    
    # English
    "item": "Line_Number",
    "line": "Line_Number",
    "no": "Line_Number",
    "number": "Line_Number",
    "parts no": "Referencia",
    "parts no.": "Referencia",
    "part no": "Referencia",
    "part no.": "Referencia",
    "part number": "Referencia",
    "supply code": "Code_2",
    "description": "Description",
    "desc": "Description",
    "qty": "Cantidad",
    "quantity": "Cantidad",
    "qnt": "Cantidad",
    "price": "Precio_Unitario",
    "unit price": "Precio_Unitario",
    "unit cost": "Precio_Unitario",
    "total": "Valor_Total",
    "amount": "Valor_Total",
    "subtotal": "Valor_Total",
    "brand": "Brand",
    "order no": "Order_Number",
    "unit": "Unit"
}

# Palabras clave que indican que NO es una fila de producto
PALABRAS_INVALIDAS = [
    "total", "subtotal", "sub-total", "grand total", "total general",
    "tva", "iva", "tax", "vat", "impuesto",
    "page", "página", "pagina",
    "facture", "factura", "invoice", "bill",
    "conditions", "condiciones", "terms", "terminos",
    "transporteur", "transporte", "shipping", "envio",
    "notes", "comentarios", "observations",
    "deposito", "deposit", "remise", "descuento", "discount"
]


# -----------------------------
#   NORMALIZAR NOMBRE DE COLUMNA
# -----------------------------
def normalizar_columna(nombre: str) -> str:
    """
    Normaliza el nombre de una columna para mapeo.
    
    Args:
        nombre: Nombre de columna del PDF
        
    Returns:
        Nombre normalizado en minúsculas sin espacios extra
    """
    if not nombre or not isinstance(nombre, str):
        return ""
    
    # Convertir a minúsculas y limpiar
    nombre = nombre.lower().strip()
    # Eliminar puntos, acentos y espacios múltiples
    nombre = re.sub(r'\s+', ' ', nombre)
    nombre = nombre.replace('.', '').replace(',', ' ').replace(':', '')
    # Remover acentos simples
    nombre = nombre.replace('á', 'a').replace('é', 'e').replace('í', 'i')
    nombre = nombre.replace('ó', 'o').replace('ú', 'u')
    
    return nombre


# -----------------------------
#   DETECTAR COLUMNAS
# -----------------------------
def detectar_columnas(headers: List) -> Dict[int, str]:
    """
    Detecta y mapea columnas de tabla a nombres estándar.
    
    Args:
        headers: Lista de nombres de columnas del PDF
        
    Returns:
        Dict mapeando índice de columna a nombre estándar
    """
    mapeo = {}
    
    for idx, header in enumerate(headers):
        if not header:
            continue
            
        header_norm = normalizar_columna(header)
        
        # Buscar en el diccionario de mapeos
        if header_norm in COLUMN_MAPPINGS:
            mapeo[idx] = COLUMN_MAPPINGS[header_norm]
        else:
            # Si no se encuentra mapeo exacto, usar el nombre original limpio
            mapeo[idx] = header.strip()
    
    return mapeo


# -----------------------------
#   VALIDAR FILA DE PRODUCTO
# -----------------------------
def es_fila_producto(fila: List) -> bool:
    """
    Determina si una fila representa un producto válido.
    
    Args:
        fila: Lista de valores de la fila
        
    Returns:
        True si es una fila de producto, False si es encabezado/total/etc
    """
    if not fila or len(fila) == 0:
        return False
    
    # Convertir fila a texto para análisis
    texto_fila = " ".join(str(cell).lower() if cell else "" for cell in fila)
    
    # Rechazar si contiene palabras inválidas
    for palabra in PALABRAS_INVALIDAS:
        if palabra in texto_fila:
            return False
    
    # Debe tener al menos un número (cantidad o precio)
    tiene_numero = any(
        str(cell).replace(",", "").replace(".", "").replace(" ", "").isdigit()
        for cell in fila if cell
    )
    
    return tiene_numero


# -----------------------------
#   LIMPIAR Y COMPLETAR PRODUCTO
# -----------------------------
def limpiar_producto(producto: Dict) -> Dict:
    """
    Limpia y completa un diccionario de producto.
    
    Args:
        producto: Diccionario con datos del producto
        
    Returns:
        Diccionario limpio y completado
    """
    if not producto:
        return producto
    
    # Remover valores vacíos y None
    producto_limpio = {k: v for k, v in producto.items() if v is not None and v != ""}
    
    # Intentar calcular Valor_Total si falta
    if "Valor_Total" not in producto_limpio or producto_limpio["Valor_Total"] is None:
        if "Cantidad" in producto_limpio and "Precio_Unitario" in producto_limpio:
            cant = producto_limpio.get("Cantidad")
            precio = producto_limpio.get("Precio_Unitario")
            if cant is not None and precio is not None and isinstance(cant, (int, float)) and isinstance(precio, (int, float)):
                producto_limpio["Valor_Total"] = float(cant) * float(precio)
    
    # Si no hay Referencia pero hay Description, intentar extraer código
    if ("Referencia" not in producto_limpio or not producto_limpio["Referencia"]) and "Description" in producto_limpio:
        desc = str(producto_limpio["Description"]).strip()
        # Buscar un código al inicio de la descripción (ej: "N300501 POMPE")
        match = re.match(r'^([A-Z0-9\-]+)\s+(.+)$', desc)
        if match:
            codigo = match.group(1)
            # Validar que parezca un código (no es una palabra común)
            if len(codigo) <= 20 and codigo not in ["THE", "AND", "FOR", "FROM"]:
                producto_limpio["Referencia"] = codigo
                producto_limpio["Description"] = match.group(2).strip()
    
    # Si no hay descripción pero hay otras info, construir una
    if ("Description" not in producto_limpio or not producto_limpio["Description"]):
        partes = []
        if "Referencia" in producto_limpio:
            partes.append(str(producto_limpio["Referencia"]))
        if "Code_2" in producto_limpio:
            partes.append(str(producto_limpio["Code_2"]))
        if "Brand" in producto_limpio:
            partes.append(f"({producto_limpio['Brand']})")
        if partes:
            producto_limpio["Description"] = " ".join(partes)
    
    return producto_limpio


# -----------------------------
#   EXTRAER TABLA INTELIGENTE
# -----------------------------
def extraer_tabla_inteligente(pdf_path: str) -> Optional[pd.DataFrame]:
    """
    Extrae tablas de productos usando detección inteligente de columnas.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        DataFrame con productos o None si no se encontraron
    """
    todas_filas = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                # Extraer todas las tablas de la página
                tablas = page.extract_tables()
                
                if not tablas:
                    continue
                
                for tabla in tablas:
                    if not tabla or len(tabla) < 1:
                        continue
                    
                    # Primera fila como encabezados
                    headers = tabla[0]
                    
                    # Detectar mapeo de columnas
                    mapeo_columnas = detectar_columnas(headers)
                    
                    if not mapeo_columnas:
                        continue
                    
                    # Verificar si es una tabla de productos (debe tener columnas clave)
                    nombres_std = set(mapeo_columnas.values())
                    tiene_columnas_producto = any(
                        col in nombres_std 
                        for col in ["Referencia", "Description", "Cantidad", "Precio_Unitario", "Valor_Total"]
                    )
                    
                    if not tiene_columnas_producto:
                        # Ser más flexible: aceptar si hay al menos Description y Cantidad o Precio
                        tiene_minimo = ("Description" in nombres_std or "Referencia" in nombres_std) and \
                                      ("Cantidad" in nombres_std or "Precio_Unitario" in nombres_std or "Valor_Total" in nombres_std)
                        if not tiene_minimo:
                            continue
                    
                    # Procesar filas de datos
                    for fila in tabla[1:]:
                        # CASO 1: Fila normal con celdas separadas
                        if len([c for c in fila if c]) > 1:
                            if not es_fila_producto(fila):
                                continue
                            
                            # Crear diccionario de producto
                            producto = {}
                            
                            for idx, nombre_columna in mapeo_columnas.items():
                                if idx < len(fila):
                                    valor = fila[idx]
                                    
                                    # Intentar convertir a número si el nombre sugiere valor numérico
                                    if nombre_columna in ["Cantidad", "Precio_Unitario", "Valor_Total", "Total", "Price", "Amount", "Unit_Price"]:
                                        valor = convertir_numero(valor)
                                    elif isinstance(valor, str):
                                        valor = valor.strip() if valor else None
                                    
                                    if valor is not None and valor != "":
                                        producto[nombre_columna] = valor
                            
                            if producto:
                                # Limpiar y completar el producto
                                producto = limpiar_producto(producto)
                                todas_filas.append(producto)
                        
                        # CASO 2: Todas las filas están en una sola celda (texto fusionado)
                        elif len(fila) > 0 and fila[0] and '\n' in str(fila[0]):
                            texto_fusionado = str(fila[0])
                            lineas = texto_fusionado.split('\n')
                            
                            # Intentar parsear cada línea como un producto
                            for linea in lineas:
                                linea = linea.strip()
                                if not linea:
                                    continue
                                
                                # Limpiar caracteres especiales de PDF (cid:160 = espacio no rompible)
                                linea = re.sub(r'\(cid:\d+\)', ' ', linea)
                                linea = re.sub(r'\s+', ' ', linea)  # Normalizar espacios
                                
                                # Remove spaces used as thousands separators to avoid splitting the number
                                linea = re.sub(r'(?<=\d)\s+(?=\d{3}(?:[.,]\d{2}|\b|\s))', '', linea)
                                
                                # Patron para líneas de productos franceses/españoles
                                # Formato: 001 N300501 /N3005 POMPE N3005-BOITE SOFABEX EMBALLE 360,00 O 9,54 3 434,40
                                patron_fr = re.compile(
                                    r'^(\d{1,3})\s+'  # Lg (001, 002, etc.) - flexible para 1-3 dígitos
                                    r'([A-Z0-9\-]+)\s+'  # Code (N300501)
                                    r'/?([A-Z0-9\-]*)\s*'  # Article (opcional /N3005)
                                    r'(.+?)\s+'  # Libellé (descripción) - non-greedy
                                    r'([\d\s,\.]+?)\s+'  # Qté (cantidad con posibles espacios)
                                    r'([A-Z\d])\s+'  # Unité (O, EA, PC, etc.)
                                    r'([\d,\.]+?)\s+'  # Prix Unit
                                    r'([\d\s,\.]+)$'  # Montant HT
                                )
                                
                                match = patron_fr.match(linea)
                                if match:
                                    try:
                                        producto = {
                                            "Line_Number": match.group(1),
                                            "Referencia": match.group(2),
                                        }
                                        
                                        if match.group(3):
                                            producto["Code_2"] = match.group(3)
                                        
                                        producto["Description"] = match.group(4).strip()
                                        producto["Cantidad"] = convertir_numero(match.group(5))
                                        producto["Unit"] = match.group(6)
                                        producto["Precio_Unitario"] = convertir_numero(match.group(7))
                                        producto["Valor_Total"] = convertir_numero(match.group(8))
                                        
                                        # Calcular Total si no existe
                                        cant = producto.get("Cantidad")
                                        precio = producto.get("Precio_Unitario")
                                        if cant is not None and precio is not None and isinstance(cant, (int, float)) and isinstance(precio, (int, float)):
                                            if producto.get("Valor_Total") is None:
                                                producto["Valor_Total"] = float(cant) * float(precio)
                                        
                                        # Limpiar producto
                                        producto = limpiar_producto(producto)
                                        todas_filas.append(producto)
                                    except Exception as e:
                                        print(f"Error parseando linea con patrón: {linea} - {e}")
                                        continue
        
        if not todas_filas:
            return None
        
        df = pd.DataFrame(todas_filas)
        
        # Calcular Total si no existe pero tenemos Quantity y Unit_Price
        if "Valor_Total" not in df.columns or df["Valor_Total"].isna().any():
            if "Cantidad" in df.columns and "Precio_Unitario" in df.columns:
                mask = df["Valor_Total"].isna() if "Valor_Total" in df.columns else True
                if mask is True or mask.any():
                    if "Valor_Total" not in df.columns:
                        df["Valor_Total"] = 0.0
                    df.loc[df["Valor_Total"].isna(), "Valor_Total"] = df["Cantidad"] * df["Precio_Unitario"]
        
        return df
    
    except Exception as e:
        print(f"Error en extraer_tabla_inteligente: {e}")
        import traceback
        traceback.print_exc()
        return None


# -----------------------------
#   FUNCIÓN PRINCIPAL
# -----------------------------
def procesar_factura_universal(pdf_path: str) -> Optional[pd.DataFrame]:
    """
    Procesa cualquier factura usando detección inteligente de tablas.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        DataFrame con productos extraídos o None si falla
    """
    try:
        df = extraer_tabla_inteligente(pdf_path)
        
        if df is not None and not df.empty:
            return df
        
        return None
    
    except Exception as e:
        print(f"Error procesando factura universal: {e}")
        return None

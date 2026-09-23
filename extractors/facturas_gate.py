# ============================
#   facturas_gate.py (MODULAR)
# ============================

import re
import pdfplumber
import pandas as pd

from utils.numeric_utils import parse_number


# -----------------------------
#   LECTURA PDF
# -----------------------------
def read_pdf_text(pdf_path: str) -> str:
    """Lee el texto completo de un PDF usando fitz (PyMuPDF) con fallback a pdfplumber.

    Args:
        pdf_path: Ruta al archivo PDF a leer.

    Returns:
        Cadena con el texto concatenado de todas las páginas del PDF.
    """
    text = ""
    try:
        import fitz
        with fitz.open(pdf_path) as doc:
            for page in doc:
                t = page.get_text("text", sort=True)
                if t:
                    text += t + "\n"
    except ImportError:
        # Fallback if fitz is not installed (though it should be)
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    return text
    

# -----------------------------
#   EXTRACCIÓN HEADER
# -----------------------------
def extract_header_fields(text: str):
    """Extrae campos del encabezado de la factura Gate (Invoice No, Date, Shipment, etc.).

    Args:
        text: Texto completo del PDF de la factura.

    Returns:
        Diccionario con los campos del encabezado extraídos.
    """
    patterns = {
        "Invoice": r"INVOICE NO\..*?\n.*?(\b[0-9]+I\b)",
        "Date": r"INVOICE DATE.*?\n.*?(\b[0-9]{2}-[A-Z]{3}-[0-9]{4}\b)",
        "Shipment No": r"SHIPMENT NO:.*?\n.*?(\b[0-9]{7}\b)",
        "Purchase Order": r"PURCHASE ORD NO:.*?\n.*?(\b[0-9]{2}-[0-9]{4}\s+[A-Za-z0-9]+)",
        "Customer Number": r"CUSTOMER NO:.*?\n.*?(\b[0-9]{6}\b)"
    }

    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.MULTILINE)
        extracted[key] = match.group(1).strip() if match else None

    return extracted


# -----------------------------
#   EXTRACCIÓN PRODUCTOS
# -----------------------------


def separar_referencia_descripcion(texto_combinado: str) -> tuple[str, str]:
    """Separa referencia y descripción de un texto combinado.

    Args:
        texto_combinado: Texto que contiene referencia y descripción.

    Returns:
        Tupla (referencia, descripción).
    """
    if not texto_combinado or not texto_combinado.strip():
        return "", ""
    
    texto_combinado = texto_combinado.strip()
    tokens = texto_combinado.split()

    # Patrón 1: Referencia alfanumérica al inicio (tipo T185, TCK1671, etc.)
    # La referencia es típicamente 1-20 caracteres, luego espacio, luego descripción
    patron_ref = re.compile(r'^([A-Z0-9]{1,20})\s+(.+)$')
    match = patron_ref.match(texto_combinado)
    if match:
        referencia = match.group(1).strip()
        descripcion = match.group(2).strip()
        # Validar que tenga sentido como referencia (no es una palabra común)
        if referencia and len(referencia) <= 20:
            return referencia, descripcion

    # Patrón 2: token único con aspecto de referencia (contiene dígitos)
    # Ej.: "ABC-123", "T185". Las descripciones simples (POMPE, EMBALLE)
    # no contienen dígitos y se conservan como descripción.
    if len(tokens) == 1 and re.search(r"\d", tokens[0]):
        return tokens[0], ""

    # Patrón 3: Si el primer token es muy corto (<=4 chars) y alfanumérico
    if tokens:
        primer_token = tokens[0]
        if len(primer_token) <= 4 and re.match(r'^[A-Z0-9]+$', primer_token):
            referencia = primer_token
            descripcion = " ".join(tokens[1:])
            return referencia, descripcion
    
    # Si no hay patrón claro, retornar todo como descripción
    return "", texto_combinado


def infer_quantity_price_total(numbers: list[float]) -> tuple[float, float, float] | tuple[None, None, None]:
    """Infiere cuál número es cantidad, precio unitario y valor total.

    Prueba todas las permutaciones de 3 números y valida que qty * price ≈ total.

    Args:
        numbers: Lista de exactamente 3 números float.

    Returns:
        Tupla (cantidad, precio_unitario, valor_total) o (None, None, None).
    """
    if len(numbers) != 3:
        return None, None, None

    tolerance = 0.05
    for i in range(3):
        for j in range(3):
            if i == j:
                continue
            k = 3 - i - j
            if k == i or k == j or k < 0 or k > 2:
                continue
            qty = numbers[i]
            price = numbers[j]
            total = numbers[k]
            if qty is None or price is None or total is None:
                continue
            if abs(round(qty * price, 2) - total) < tolerance:
                return qty, price, total

    return None, None, None


def fallback_extract_line(line: str):
    """Extrae datos de producto de una línea de texto usando análisis de tokens.

    Método de respaldo cuando el patrón principal regex no coincide.
    Analiza tokens de la línea, identifica los 3 últimos numéricos y
    valida la relación cantidad × precio = total.

    Args:
        line: Línea de texto del PDF.

    Returns:
        Diccionario con datos del producto o None si no se pudo extraer.
    """
    tokens = re.split(r"\s{2,}|\t|\s+", line.strip())
    if len(tokens) < 6:
        return None

    numeric_tokens = []
    for idx, token in enumerate(tokens):
        num = parse_number(token)
        if num is not None:
            numeric_tokens.append((idx, num))

    if len(numeric_tokens) < 3:
        return None

    # Take the last three numeric values from the line.
    last_three = numeric_tokens[-3:]
    if last_three[-1][0] != len(tokens) - 1:
        return None

    indices, values = zip(*last_three)
    cantidad, precio_unitario, valor_total = infer_quantity_price_total(list(values))
    if cantidad is None or precio_unitario is None or valor_total is None:
        return None

    unidad = tokens[1] if len(tokens) > 1 else ""
    product_idx = indices[0] - 1
    product_number = tokens[product_idx] if product_idx >= 0 else ""
    
    # Mejorado: separar referencia y descripción
    descripcion_full = " ".join(tokens[2:product_idx]) if product_idx > 2 else ""
    referencia, descripcion = separar_referencia_descripcion(descripcion_full)

    return {
        "Cantidad": cantidad,
        "Description": descripcion,
        "Referencia": referencia,
        "Product Number": product_number,
        "Unidad": unidad,
        "Precio_Unitario": precio_unitario,
        "Valor_Total": round(valor_total, 2),
    }


def extract_product_lines(text: str):
    """Extrae líneas de productos del texto del PDF, separando referencia y descripción.

    Maneja patrones más flexibles. Usa regex principal y fallback a análisis
    de tokens si el patrón no coincide.

    Args:
        text: Texto completo del PDF de la factura.

    Returns:
        Lista de diccionarios con datos de cada producto extraído.
    """
    line_pattern = re.compile(
        r"^(\d+)\s+EA\s+([A-Z0-9\- ]+?)\s+([0-9]{5,12})\s+(.*)$",
        re.MULTILINE
    )

    items = []

    for line_match in line_pattern.finditer(text):
        line_number = parse_number(line_match.group(1))
        descripcion_raw = line_match.group(2).strip()
        product_number = line_match.group(3).strip()
        tail = line_match.group(4).strip()

        tokens = tail.split()
        numeric_values = [parse_number(tok) for tok in tokens if parse_number(tok) is not None]

        cantidad = precio_unitario = valor_total = None

        if len(numeric_values) >= 3:
            cantidad, precio_unitario, valor_total = infer_quantity_price_total(numeric_values[-3:])

        if cantidad is None and len(numeric_values) >= 2:
            cantidad = numeric_values[-2]
            precio_unitario = numeric_values[-1]
            valor_total = round(cantidad * precio_unitario, 2)

        if cantidad is None or precio_unitario is None:
            continue

        # Mejorado: usar la función para separar referencia y descripción
        referencia, descripcion = separar_referencia_descripcion(descripcion_raw)

        item = {
            "Cantidad": cantidad,
            "Description": descripcion,
            "Referencia": referencia,
            "Product Number": product_number,
            "Precio_Unitario": precio_unitario,
            "Valor_Total": round(valor_total if valor_total is not None else cantidad * precio_unitario, 2),
        }
        items.append(item)

    if not items:
        # fallback to generic parser if modular pattern did not match
        for line in text.splitlines():
            item = fallback_extract_line(line)
            if item is not None:
                items.append(item)

    return items


# -----------------------------
#   FUNCIÓN PRINCIPAL (MODULAR)
# -----------------------------
def procesar_factura_gate(pdf_path: str):
    """Procesa una factura del proveedor Gate y extrae header + productos.

    Intenta extraer productos usando patrones regex específicos de Gate.
    Si no encuentra productos, retorna None (indica que este parser no aplica).

    Args:
        pdf_path: Ruta al archivo PDF de la factura Gate.

    Returns:
        DataFrame con header y productos, o None si no se pudo procesar.
    """
    text = read_pdf_text(pdf_path)
    header = extract_header_fields(text)
    products = extract_product_lines(text)

    if not products:
        return None  # Indica: "este parser no aplica"

    # Post-procesamiento: asegurar que Referencia y Description estén bien separados
    for prod in products:
        # Si Referencia está vacía o es "0", intentar extraerla de Description
        if not prod.get("Referencia") or prod.get("Referencia") == "0" or prod.get("Referencia") == "":
            if prod.get("Description"):
                ref, desc = separar_referencia_descripcion(prod["Description"])
                if ref:
                    prod["Referencia"] = ref
                    prod["Description"] = desc
        # Si Description está vacía, pero hay referencia y product_number, construir descripción
        elif not prod.get("Description") or prod.get("Description") == "":
            partes = []
            if prod.get("Product Number"):
                partes.append(prod["Product Number"])
            if partes:
                prod["Description"] = " ".join(partes)
    
    df = pd.DataFrame([{**header, **prod} for prod in products])
    return df

import pdfplumber
import pandas as pd
import re
from infrastructure.pdf.text_extractor import extract_text_from_pdf
from utils.numeric_utils import parse_number as convertir_numero


def procesar_factura_sofabex(pdf_path: str):
    """Procesa una factura del proveedor SOFABEX y extrae metadata + items.

    Args:
        pdf_path: Ruta al archivo PDF de la factura SOFABEX.

    Returns:
        Diccionario con estructura {"metadata": {...}, "items": [...]} o None
        si el PDF no contiene datos de SOFABEX.
    """
    raw_texto = extract_text_from_pdf(pdf_path)
    texto_upper = raw_texto.upper()
    
    if "SOFABEX" not in texto_upper:
        return None

    metadata = {
        "num_factura": "",
        "fecha_factura": "",
        "proveedor": "SOFABEX",
        "pais_origen": "FRANCIA",
        "incoterm": "FOB",
        "moneda": "EUR",
        "tipo_cambio": "1.0",
        "importador": "",
        "registro_declaracion": "",
        "fecha_declaracion": "",
        "aduana": "",
        "medio_transporte": "",
        "conocimiento_embarque": "",
        "fecha_embarque": "",
        "total_mercancia": 0.0,
        "flete": 0.0,
        "seguro": 0.0,
        "otros_gastos": 0.0,
        "total_factura": 0.0
    }

    # Extract Invoice Number
    match_num = re.search(r"FACTURE\s+N[°º]?\s*[:]\s*([A-Z0-9\-]+)", texto_upper)
    if match_num:
        metadata["num_factura"] = match_num.group(1).strip()

    # Extract Date
    match_date = re.search(r"(\d{2}/\d{2}/\d{4})", raw_texto)
    if match_date:
        metadata["fecha_factura"] = match_date.group(1)

    # Extract Importador
    match_imp = re.search(r"ADRESSE DE FACTURATION\s*:\s*\n?([^\n]+)", texto_upper)
    if match_imp:
        metadata["importador"] = match_imp.group(1).strip()

    items = []
    lineas = raw_texto.split("\n")
    
    # Patrón mejorado para Sofabex
    # 001 N300501 /N3005 POMPE N3005-BOITE SOFABEX EMBALLE 360,00 O 9,54 3 434,40
    # Buscamos: Lg(3) -> Código/Desc -> Cantidad -> Unidad -> Precio -> Total
    # El Total puede tener espacios como miles.
    
    # Regex 1: Más estricto con separadores
    re_item_main = re.compile(
        r"^(\d{3})\s+"                      # Lg
        r"(.+?)\s+"                          # Código + Libellé (captura perezosa)
        r"([\d\s\.]+(?:[.,]\d+)?)\s+"    # Qté (Cantidad con separadores de miles y coma decimal)
        r"([A-Z0-9]{1,3})\s+"                # Unité (Unidad)
        r"([\d\s\.]+(?:[.,]\d+)?)\s+"    # Prix Unit (Precio Unitario)
        r"([\d\s\.]+(?:[.,]\d+)?)"        # Montant HT (Total)
    )

    for linea in lineas:
        linea = re.sub(r'\s+', ' ', linea.strip())
        if not linea or not linea[0].isdigit():
            continue

        m = re_item_main.match(linea)
        if m:
            lg = m.group(1)
            desc_code = m.group(2).strip()
            qty_val = convertir_numero(m.group(3))
            unidad = m.group(4).strip()
            px_val = convertir_numero(m.group(5))
            tot_val = convertir_numero(m.group(6))

            if qty_val is None or px_val is None or tot_val is None:
                continue
            
            try:
                # Separar código de descripción si es posible (Sofabex suele poner el código primero)
                # Ejemplo: N300501 /N3005 POMPE ...
                parts = desc_code.split(" ", 1)
                codigo = parts[0]
                descripcion = parts[1] if len(parts) > 1 else desc_code

                items.append({
                    "linea": lg,
                    "descripcion": descripcion,
                    "marca": "SOFABEX",
                    "referencia": codigo,
                    "destino_uso": "PARA VEHICULOS",
                    "cantidad": qty_val,
                    "unidad": unidad,
                    "valor_unitario": px_val,
                    "valor_total": tot_val
                })
            except:
                continue

    if items:
        metadata["total_mercancia"] = sum(item["valor_total"] for item in items)
        metadata["total_factura"] = metadata["total_mercancia"] + metadata["flete"] + metadata["seguro"] + metadata["otros_gastos"]

    return {
        "metadata": metadata,
        "items": items
    }

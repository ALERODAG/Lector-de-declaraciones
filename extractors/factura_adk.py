# =============================
# factura_adk.py
# Parser de facturas del proveedor ADK
#
# Flujo de datos:
#     pdf_path → procesar_factura_adk() → DataFrame o None
#
# Estrategia: Busca bloques de texto delimitados por patrón de inicio
# (LN + código) y fin (marca + cantidad + precio).
# Usa fitz (PyMuPDF) como extractor principal, pdfplumber como fallback.
# =============================

import pdfplumber
import pandas as pd
import re

# Marcas conocidas (puedes ampliar)
MARCAS = ["GMB", "NSK", "KOYO", "SKF", "FAG"]

# Inicio de producto: LN + Código
PAT_INICIO = re.compile(
    r"^(?P<ln>\d{1,4})\s+(?P<ref>[A-Z0-9\-\/]+)"
)

# Fin de producto: Marca + Cantidad + Precio (+ Extensión).
# Se admite separador de miles en cantidad y precios (p.ej. 1.945,00)
# y cantidades de 4+ dígitos sin separador (p.ej. 4000, 1500).
PRE_NUMERO = r"(?:\d{1,3}(?:\.\d{3})*|\d{4,})"
PAT_FIN = re.compile(
    rf"(?P<marca>{'|'.join(MARCAS)})\s+(?P<cantidad>{PRE_NUMERO})\s+"
    rf"(?P<precio>\d{{1,3}}(?:\.\d{{3}})*,\d{{2}})(?:\s+(?P<ext>\d{{1,3}}(?:\.\d{{3}})*,\d{{2}}))?"
)


def _read_pdf_text(pdf_path: str) -> str:
    """Lee el texto completo de un PDF (fitz con fallback a pdfplumber).

    Args:
        pdf_path: Ruta al archivo PDF de la factura ADK.

    Returns:
        Cadena con el texto concatenado de todas las páginas.
    """
    try:
        import fitz
        with fitz.open(pdf_path) as doc:
            return "\n".join(
                page.get_text("text", sort=True)
                for page in doc
                if page.get_text("text", sort=True)
            )
    except ImportError:
        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(
                text
                for page in pdf.pages
                if (text := page.extract_text())
            )


def _parse_numero(texto: str) -> float:
    """Convierte un número con formato latino (1.945,00) a float."""
    return float(texto.replace(".", "").replace(",", "."))


def procesar_factura_adk_text(text: str) -> pd.DataFrame | None:
    """Procesa el texto extraído de una factura ADK.

    Escanea las líneas del texto buscando bloques delimitados por
    PAT_INICIO (LN + código) y PAT_FIN (marca + cantidad + precio).

    Args:
        text: Texto crudo extraído del PDF de la factura.

    Returns:
        DataFrame con los productos o None si no se encontró ninguno.
    """
    rows: list[dict] = []
    bloque: list[str] = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if PAT_INICIO.match(line):
            if bloque:
                _procesar_bloque(bloque, rows)
                bloque = []
            bloque.append(line)
        elif bloque:
            bloque.append(line)

        if bloque and PAT_FIN.search(line):
            _procesar_bloque(bloque, rows)
            bloque = []

    # Cierre final (común)
    if bloque:
        _procesar_bloque(bloque, rows)

    if not rows:
        return None

    return pd.DataFrame(rows)


def procesar_factura_adk(pdf_path: str) -> pd.DataFrame | None:
    """Procesa una factura del proveedor ADK a partir de su PDF.

    Args:
        pdf_path: Ruta al archivo PDF de la factura ADK.

    Returns:
        DataFrame con header y productos, o None si no se pudo procesar.
    """
    text = _read_pdf_text(pdf_path)
    return procesar_factura_adk_text(text)


_PAT_FACTURA_NO = re.compile(r"Factura\s+No[.:]?\s*([A-Za-z0-9\-/]+)", re.IGNORECASE)
_PAT_FECHA = re.compile(r"Fecha[.:]?\s*([A-Za-z0-9\-/]+)", re.IGNORECASE)
_PAT_VENDIDO_A = re.compile(r"Vendido\s+a[.:]?\s*(.+?)\s+NIT[.:]", re.IGNORECASE)
_PAT_NIT = re.compile(r"NIT[.:]?\s*([0-9.\-]+)", re.IGNORECASE)
_PAT_INCOTERM = re.compile(r"\b(FOB|CIF|CFR|EXW|FCA|DAP|DDP|CPT|CIP|FAS)\b", re.IGNORECASE)
_PAT_MONEDA = re.compile(r"Total\s+([A-Z]{3})\s+[\d.,]+", re.IGNORECASE)
_PAT_TOTAL = re.compile(r"Total\s+[A-Z]{3}\s+([\d.,]+)", re.IGNORECASE)
_PAT_SUBTOTAL = re.compile(r"Sub[- ]Total\s+([\d.,]+)", re.IGNORECASE)


def extraer_metadata_adk(text: str) -> dict:
    """Extrae la metadata de cabecera de una factura ADK.

    Se basa en el encabezado típico de ADK CORPORATION:
        ADK CORPORATION / Factura No: F9999-00001
        Vendido a: IMPORTADORA EJEMPLO S.A.S NIT: 999.999.999-9 Fecha: 2-oct-25
        FOB OSAKA / Total JPY 12.912.482,00

    Args:
        text: Texto crudo de la factura ADK.

    Returns:
        Dict con las claves de InvoiceMetadata.
    """
    m = _PAT_FACTURA_NO.search(text)
    num_factura = m.group(1).strip() if m else "N/A"

    m = _PAT_FECHA.search(text)
    fecha = m.group(1).strip() if m else "N/A"

    m = _PAT_VENDIDO_A.search(text)
    importador = m.group(1).strip() if m else "N/A"

    m = _PAT_NIT.search(text)
    nit = m.group(1).strip() if m else ""

    m = _PAT_INCOTERM.search(text)
    incoterm = m.group(1).upper() if m else "N/A"

    m = _PAT_MONEDA.search(text)
    moneda = m.group(1).upper() if m else "USD"

    m = _PAT_TOTAL.search(text)
    total = _parse_numero(m.group(1)) if m else 0.0

    m = _PAT_SUBTOTAL.search(text)
    subtotal = _parse_numero(m.group(1)) if m else total

    pais_origen = ""
    if "OSAKA" in text.upper():
        pais_origen = "OSAKA"
    elif "JAPAN" in text.upper() or "JAPON" in text.upper():
        pais_origen = "JAPON"

    return {
        "num_factura": num_factura,
        "fecha_factura": fecha,
        "proveedor": "ADK",
        "pais_origen": pais_origen or "N/A",
        "incoterm": incoterm,
        "moneda": moneda,
        "tipo_cambio": 1.0,
        "importador": f"{importador}{(' ' + nit.strip()) if nit else ''}".strip(),
        "total_mercancia": subtotal,
        "flete": 0.0,
        "seguro": 0.0,
        "otros_gastos": 0.0,
        "total_factura": total,
    }


def _procesar_bloque(bloque: list[str], rows: list[dict]):
    texto = " ".join(bloque)

    ini = PAT_INICIO.search(texto)
    fin = PAT_FIN.search(texto)

    if not ini or not fin:
        return

    ln = int(ini.group("ln"))
    referencia = ini.group("ref")
    if len(bloque) > 1:
        for extra in bloque[1:]:
            if not PAT_FIN.search(extra):
                referencia = f"{referencia} {extra.strip()}"

    marca = fin.group("marca")
    cantidad = int(_parse_numero(fin.group("cantidad")))
    precio = _parse_numero(fin.group("precio"))

    # Texto intermedio (códigos + descripción)
    cuerpo = texto[ini.end():fin.start()].strip()
    partes = cuerpo.split(" ", 1)

    code_2 = ""
    descripcion = cuerpo

    if (
        len(partes) == 2
        and re.fullmatch(r"[A-Z0-9\-/]+", partes[0])
        and re.search(r"\d", partes[0])
    ):
        code_2 = partes[0]
        descripcion = partes[1]

    valor_total = _parse_numero(fin.group("ext")) if fin.group("ext") else round(cantidad * precio, 2)

    rows.append({
        "LN": ln,
        "Referencia": referencia,
        "Code_2": code_2,
        "Description": descripcion.strip(),
        "Brand": marca,
        "Cantidad": cantidad,
        "Precio_Unitario": precio,
        "Valor_Total": valor_total,
    })

if __name__ == "__main__":
    import os
    possible_paths = ["facturas_pdf", "PDF_A_LEER", "."]
    test_pdf = None
    
    print("Buscando un PDF para probar...")
    for p in possible_paths:
        if os.path.exists(p):
            if p.lower().endswith(".pdf"):
                test_pdf = p
                break
            else:
                pdfs = [f for f in os.listdir(p) if f.lower().endswith(".pdf")]
                if pdfs:
                    test_pdf = os.path.join(p, pdfs[0])
                    break
    
    if test_pdf:
        print(f"Procesando: {test_pdf}")
        df = procesar_factura_adk(test_pdf)
        if df is not None:
            print("\nDATOS EXTRAÍDOS:")
            print("="*100)
            print(df.to_string(index=False))
            print("="*100)
            print(f"Total de líneas extraídas: {len(df)}")
        else:
            print("No se pudo extraer información del PDF.")
    else:
        print("No se encontró el PDF en la ruta de Documentos ni en carpetas locales.")

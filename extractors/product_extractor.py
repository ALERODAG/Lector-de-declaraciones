"""Extractor de productos de declaraciones de importación (DIM).

Analiza el texto extraído de PDFs de declaraciones de importación y
extrae información detallada de cada producto declarado, incluyendo:
marca, modelo, referencia, serial, país de origen, cantidad, etc.

Flujo de datos:
    texto PDF → ProductExtractor.extract_products_from_text() → DataFrame

Patrón de diseño: Template Method con regex compilados en __init__.
"""

import os
import re
from typing import cast, List, Dict
import pandas as pd
from openpyxl.styles import PatternFill

# =========================
# Dependencia: PyMuPDF
# =========================
try:
    import pymupdf as fitz
except ImportError as e:
    raise RuntimeError(
        "No se encontró PyMuPDF. Instálalo con:\n\n    pip install pymupdf\n"
    ) from e

# =========================
# TextUtils (fallback mínimo)
# =========================
try:
    from utils.text_utils import TextUtils  # type: ignore[import-not-found]
except Exception:
    class TextUtils:
        """Fallback mínimo de limpieza de texto si text_utils no está disponible."""
        def clean_text(self, t: str) -> str:
            t = t.replace("\r", "\n")
            t = re.sub(r"[ \t]+", " ", t)
            t = re.sub(r"\n+", "\n", t)
            return t.strip()


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extrae texto de un PDF usando PyMuPDF (fitz).

    Args:
        ruta_pdf: Ruta al archivo PDF a extraer.

    Returns:
        Cadena con el texto extraído de todas las páginas.
        Retorna cadena vacía si ocurre un error de lectura.
    """
    partes: List[str] = []
    try:
        with fitz.open(ruta_pdf) as doc:
            for p in doc:
                page = cast("fitz.Page", p)
                partes.append(page.get_text("text"))  # type: ignore[attr-defined]
    except Exception as e:
        print(f"Error al leer {ruta_pdf}: {e}")
    return "".join(partes)




# =========================
# Extractor de productos
# =========================

class ProductExtractor:
    """Extractor de productos de PDFs de declaraciones de importación (autopartes).

    Analiza el texto de declaraciones DIM usando una colección extensa de
    regex compilados para extraer campos como: Producto, Marca, Modelo,
    Referencia, Serial, País de Origen, Cantidad, etc.

    Attributes:
        SUMAR_CANTIDADES_EN_BLOQUE: Si True, suma cantidades de productos
            repetidos en un mismo bloque. Por defecto False.
        BASE_COLUMNS: Columnas base que siempre se incluyen en el DataFrame.
        OPTIONAL_COLUMNS: Columnas opcionales que se elimin si están vacías.
        STD_COLUMNS: Unión de BASE_COLUMNS y OPTIONAL_COLUMNS.
    """

    SUMAR_CANTIDADES_EN_BLOQUE = False

    BASE_COLUMNS = [
        'Producto','Marca', 'Modelo', 'Referencia', 'Serial',
        'Destino', 'Cantidad', 'Unidad', 'Pais_Origen', 'Codigo_Pais_Origen',
        'Archivo', 'Declaracion'
    ]

    OPTIONAL_COLUMNS = [
        # 'Categoria', 'Material', 'Composicion', 'Presentacion_Comercial',
        # 'Estado_Producto', 'Norma_Tecnica', 'Numero_OEM', 'Numero_Aftermarket',
        # 'Pais_Procedencia',
        # 'Viscosidad', 'Tipo_Aceite', 'Capacidad_L',
        # 'Tipo_Filtro', 'Micraje', 'Medidas',
        # 'Tipo_Bujia', 'Rosca', 'Numero_Calor',
        # 'Tipo_Terminal', 'Longitud', 'Ancho', 'Paso',
        # 'Tipo_Sensor', 'Voltaje',
        # 'Tipo_Soporte',
        # 'Incluye_Accesorios',
    ]

    STD_COLUMNS = BASE_COLUMNS + OPTIONAL_COLUMNS

    def __init__(self):
        self.text_utils = TextUtils()

        # Patrones compilados — se compilan una sola vez al instanciar
        _F = re.IGNORECASE

        self.re_uso          = [re.compile(p, _F) for p in [
            r"USO\s*:\s*([^,]+)",
            r"USO\s*O\s*DESTINO\s*:\s*([^,]+)",
            r"APLICACI[ÓO]N\s*:\s*([^,]+)",
            r"COMPATIBILIDD\s*:\s*([^,]+)",
            # r"DESTINO\s*:\s*([^,]+)",
        ]]
        self.re_categoria    = [re.compile(p, _F) for p in [
            r"CATEGOR[ÍI]A\s*:\s*([^,]+)", r"TIPO\s*DE\s*REPUESTO\s*:\s*([^,]+)"
        ]]
        self.re_material     = [re.compile(r"MATERIAL\s*:\s*([^,]+)", _F)]
        self.re_presentacion = [re.compile(p, _F) for p in [
            r"EMPAQUE\s*:\s*([^,]+)", r"PRESENTACI[ÓO]N\s*:\s*([^,]+)"
        ]]
        self.re_estado       = [re.compile(p, _F) for p in [
            r"ESTADO\s*:\s*(NUEVO|USADO|REMANUFACTURADO|RECONSTRUIDO)",
            r"NUEVO|USADO|REMANUFACTURADO|RECONSTRUIDO"
        ]]
        self.re_norma        = [re.compile(p, _F) for p in [
            r"NORMA\s*:\s*([^,]+)", r"CERTIFICACI[ÓO]N\s*:\s*([^,]+)"
        ]]
        self.re_oem          = [re.compile(r"(?:N[ÚU]MERO\s*OEM|OEM|P\/N|PN|P\.N\.)\s*[:\-]?\s*([A-Z0-9\-\._\/ ]+)", _F)]
        self.re_after        = [re.compile(r"(?:AFTERMARKET|EQUIV\.?|EQUIVALENTE)\s*[:\-]?\s*([A-Z0-9\-\._\/ ]+)", _F)]
        self.re_unidad       = [re.compile(r"\bUNIDAD(?:ES)?\b|\bUND\b|\bUNID\b", _F)]
        self.re_procedencia  = [re.compile(r"PA[IÍ]S\s*PROCEDENCIA\s*:\s*([A-ZÁÉÍÓÚÜÑ ]+)", _F)]
        # self.re_subpartida   = [re.compile(r"SUBPARTIDA\s*[:\-]?\s*([\d\.]{8,10})", _F)]

        # Aceites
        self.re_viscosidad   = [re.compile(r"\b(\d{1,2}W-\d{1,2})\b", _F)]
        self.re_tipo_aceite  = [re.compile(r"\b(SINT[EÉ]TICO|MINERAL|SEMISINT[EÉ]TICO)\b", _F)]
        self.re_capacidad_l  = [re.compile(r"\b(\d+(?:[\.,]\d+)?)\s*(L|LTS|LITROS)\b", _F)]

        # Filtros
        self.re_tipo_filtro  = [re.compile(r"\bFILTRO\s*(DE\s*[A-ZÁÉÍÓÚÜÑ]+)?\b", _F)]
        self.re_micraje      = [re.compile(r"\b(\d{1,3})\s*MICRAS?\b", _F)]
        self.re_medidas      = [re.compile(r"\b(\d+(?:[\.,]\d+)?\s*x\s*\d+(?:[\.,]\d+)?\s*x\s*\d+(?:[\.,]\d+)?)\b", _F)]

        # Bujías
        self.re_tipo_bujia   = [re.compile(r"\bBUJ[IÍ]A\s*(IRIDIO|N[IÍ]QUEL|PLATINO)\b", _F)]
        self.re_rosca        = [re.compile(r"\bM\d{6}\b|\bM\d{1,2}\s*x\s*\d(?:[\.,]\d+)?\b", _F)]
        self.re_numero_calor = [re.compile(r"\bN[ÚU]MERO\s*DE\s*CALOR\s*[:\-]?\s*([A-Z0-9\-]+)\b", _F)]

        # Cables / Correas
        self.re_tipo_terminal = [re.compile(r"\bTERMINAL\s*[:\-]?\s*([A-Z0-9\/\-\s]+)\b", _F)]
        self.re_longitud      = [re.compile(r"\bLONGITUD\s*[:\-]?\s*([\d\.,]+)\s*(MM|CM|M)\b", _F)]
        self.re_ancho         = [re.compile(r"\bANCHO\s*[:\-]?\s*([\d\.,]+)\s*(MM|CM|M)\b", _F)]
        self.re_paso          = [re.compile(r"\bPASO\s*[:\-]?\s*([\d\.,]+)\s*(MM|IN)\b", _F)]

        # Sensores / Soportes
        self.re_tipo_sensor  = [re.compile(r"\bSENSOR\s*(MAP|O2|ABS|TPS|MAF|CKP|CMP)\b", _F)]
        self.re_voltaje      = [re.compile(r"\b(\d{1,2}(?:[\.,]\d+)?)\s*V\b", _F)]
        self.re_tipo_soporte = [re.compile(r"\bSOPORTE\s*(HIDR[ÁA]ULICO|DE\s*CAUCHO|RIGIDO)\b", _F)]
        self.re_incluye      = [re.compile(r"\b(CON\s*TAPA|SIN\s*TAPA|CON\s*SENSOR|SIN\s*SENSOR)\b", _F)]

        # Patrones de first-label y referencia/serial
        self.re_first_label = re.compile(
            r'\b(?:REFERENCIA|REF\.?|SER(?:IAL)?\.?|USO|DESTINO|APLICACI[ÓO]N|COMPATIBILIDAD'
            r'|PA[IÍ]S\s*ORIGEN|PA[IÍ]S\s*PROCEDENCIA|MARCA|MODELO|COMPOSICION|MATERIAL'
            r'|CATEGOR[ÍI]A|PRESENTACI[ÓO]N|SUBPARTIDA)\s*:',
            _F
        )
        _next = r'(?=\s*(?:CANT|MARCA|MODELO|COMPOSICION|MATERIAL|USO|DESTINO|APLICACI[ÓO]N|COMPATIBILIDAD|PAIS|PROCEDENCIA|REFERENCIA|REF|SER|SERIAL|SUBPARTIDA|PRESENTA)\s*:?)'
        self.re_referencia = [
            re.compile(r'\bREFERENCIA\s*:\s*(.*?)' + _next, re.IGNORECASE | re.DOTALL),
            re.compile(r'\bREF\.?\s*:\s*(.*?)'     + _next, re.IGNORECASE | re.DOTALL),
        ]
        self.re_serial = [
            re.compile(r'\bSERIAL\s*:\s*(.*?)' + _next.replace('SUBPARTIDA|PRESENTA', 'SERIAL'), re.IGNORECASE | re.DOTALL),
            re.compile(r'\bSER\.?\s*:\s*(.*?)'  + _next.replace('SUBPARTIDA|PRESENTA', 'SERIAL'), re.IGNORECASE | re.DOTALL),
        ]

        # Cantidades
        _units = r'UND|UNID|UNIDADES|PCS|PIEZAS|PZA|PZ'
        self.re_qty_with_unit      = re.compile(r'\bCANT(?:IDAD)?(?:(?!CANT).){0,60}?(\d{1,9})\s*(?:' + _units + r')\b', _F)
        self.re_qty_paren_opt_unit = re.compile(r'\bCANT(?:IDAD)?(?:(?!CANT).){0,60}?\(([\d\.,]{1,9})\)\s*(?:' + _units + r')?', _F)
        self.re_qty_simple_no_unit = re.compile(r'\bCANT(?:IDAD)?(?:(?!CANT).){0,60}?(\d{1,9})(?!\s*(?:' + _units + r'))', _F)
        self.re_unit_suffix        = re.compile(r'^\)\s*(?:' + _units + r')\b', _F)

        # Patrones de pais de origen (compilados)
        self.re_pais_origen = [
            re.compile(r'PA[IÍ]S\s*(?:DE\s*)?ORIGEN\s*:\s*([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)\s*[-–—]\s*(\d{2,3})', _F),
            re.compile(r'PA[IÍ]S\s*(?:DE\s*)?ORIGEN\s*:\s*([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)\s+(\d{2,3})', _F),
            re.compile(r'PA[IÍ]S\s*:\s*([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)\s*[-–—]\s*(\d{2,3})', _F),
        ]
        self.re_pais_origen_fallback = re.compile(
            r'PA[IÍ]S\s*(?:DE\s*)?ORIGEN\s*:\s*([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]{2,30}?)(?:\s*[,\.\n]|$)', _F
        )

    # ==========================
    # Limpiezas internas
    # ==========================
    def _strip_no_diligenciable_blocks(self, t: str) -> str:
        src = t
        low = src.lower()
        while True:
            i1, i2 = low.find('<!-- continua'), low.find('<-- continua')
            start = i1 if (i1 != -1 and (i2 == -1 or i1 < i2)) else i2
            if start == -1:
                break
            candidates = [c for c in (low.find('<< do', start), low.find('<<do', start)) if c != -1]
            if not candidates:
                break
            src = src[:start] + src[min(candidates):]
            low = src.lower()
        return src

    def _strip_inline_do_markers(self, t: str) -> str:
        src, low, pos, out = t, t.lower(), 0, []
        L = len(src)
        while pos < L:
            i = low.find('<<', pos)
            if i == -1:
                out.append(src[pos:])
                break
            out.append(src[pos:i])
            j = low.find('>>', i + 2)
            if j == -1:
                out.append(src[i:])
                break
            inner = low[i+2:j].strip()
            out.append(' ' if ('do' in inner or 'declar' in inner) else src[i:j+2])
            pos = j + 2
        cleaned = ''.join(out)
        cleaned = re.sub(r'[ \t]+', ' ', cleaned)
        return re.sub(r'\n{3,}', '\n\n', cleaned)

    def clean_text(self, text: str) -> str:
        t = self.text_utils.clean_text(text)
        t = self._strip_no_diligenciable_blocks(t)
        t = self._strip_inline_do_markers(t)
        t = re.sub(r'NO\s+DILIGENCIABLE', ' ', t, flags=re.IGNORECASE)
        t = re.sub(r'\s*:\s*', ': ', t)
        t = re.sub(r'PA[IÍ]S\s+DE\s+ORIGEN', 'PAIS ORIGEN', t, flags=re.IGNORECASE)
        t = re.sub(r'PA[IÍ]S\s*\n+\s*ORIGEN', 'PAIS ORIGEN', t, flags=re.IGNORECASE)
        t = re.sub(r'[ \t]+', ' ', t)
        return re.sub(r'\n+', '\n', t).strip()

    # ==========================
    # Helpers
    # ==========================
    def _first_label_pos(self, text: str) -> int:
        m = self.re_first_label.search(text)
        return m.start() if m else -1

    def _trim_numeric_tail(self, s: str) -> str:
        m = re.search(r',\s*(?:[\d\s\.,]{6,})$', s)
        return s[:m.start()] if m else s

    def _dedupe_ref(self, ref: str) -> str:
        ref = ref.strip()
        if '-' in ref:
            left, right = ref.split('-', 1)
            if left.strip().upper() == right.strip().upper():
                return left.strip()
        return ref

    def _extract_with_patterns(self, text: str, compiled_patterns: list) -> str:
        for pat in compiled_patterns:
            m = pat.search(text)
            if m:
                return (m.group(1) if m.groups() else m.group(0)).strip()
        return ""

    def _extract_pais_origen(self, text: str, fields: dict) -> None:
        for pat in self.re_pais_origen:
            m = pat.search(text)
            if m:
                fields['Pais_Origen'] = re.sub(r'\s+', ' ', m.group(1).strip())
                fields['Codigo_Pais_Origen'] = m.group(2).strip()
                return
        m = self.re_pais_origen_fallback.search(text)
        if m:
            fields['Pais_Origen'] = re.sub(r'\s+', ' ', m.group(1).strip())

    # ==========================
    # Núcleo de extracción
    # ==========================
    def _extract_product_fields(self, product_block: str) -> dict:
        """Extrae todos los campos de un bloque de producto individual.

        Usa extracción dinámica basada en delimitador de coma y regex
        precompilados para extraer campos como Marca, Modelo, Referencia,
        Serial, País de Origen, Cantidad, etc.

        Args:
            product_block: Texto del bloque de producto (contenido después
                          de "PRODUCTO:" o "NOMBRE TECNICO DEL PRODUCTO:").

        Returns:
            Diccionario con los campos extraídos del producto.
        """
        fields: Dict[str, str] = {}
        block = product_block.strip()

        # Insertar coma antes de etiquetas clave si no hay una,
        # para que al eliminar saltos de línea no se fusionen campos.
        labels = r'\b(?:MARCA|MODELO|REFERENCIA|REF\.?|SER(?:IAL)?\.?|USO|DESTINO|APLICACI[ÓO]N|COMPATIBILIDAD|PA[IÍ]S\s*ORIGEN|CATEGOR[ÍI]A|MATERIAL|PRESENTACI[ÓO]N|ESTADO|NORMA|CERTIFICACI[ÓO]N|OEM|AFTERMARKET|CANT(?:IDAD)?|COMPOSICI[ÓO]N|SUBPARTIDA)\b'
        block = re.sub(r'(?<!,)\s+(' + labels + r')(?=\s*:?)', r', \1', block, flags=re.IGNORECASE)
        
        # Eliminar saltos de línea para que no corten la extracción de valores
        block = re.sub(r'\s*\n\s*', ' ', block).strip().lstrip(', ')

        # --- INICIO EXTRACCIÓN DINÁMICA (Basada en delimitador de coma) ---
        parts = block.split(',')
        current_label = None
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            colon_idx = part.find(':')
            if colon_idx != -1:
                label = part[:colon_idx].strip()
                value = part[colon_idx+1:].strip()
                
                label_clean = re.sub(r'\s+', '_', label.title())
                std_mapping = {
                    'Marca': 'Marca', 'Modelo': 'Modelo', 'Referencia': 'Referencia', 'Ref': 'Referencia',
                    'Serial': 'Serial', 'Ser': 'Serial', 'Destino': 'Destino', 'Uso': 'Destino',
                    'Uso_O_Destino': 'Destino', 'Aplicacion': 'Destino', 'Aplicación': 'Destino',
                    'Compatibilidad': 'Compatibilidad', 'Pais_Origen': 'Pais_Origen', 
                    'Pais_De_Origen': 'Pais_Origen', 'Cantidad': 'Cantidad', 'Cant': 'Cantidad',
                    'Oem': 'Numero_OEM', 'Part_Number': 'Numero_OEM', 'Composicion': 'Composicion'
                }
                label_clean = std_mapping.get(label_clean, label_clean)
                
                if value.endswith('//'):
                    value = value[:-2].strip()
                
                if label_clean in fields and fields[label_clean]:
                    fields[label_clean] += f" {value}"
                else:
                    fields[label_clean] = value
                current_label = label_clean
                
            else:
                part_clean = part.replace('//', '').strip()
                if re.match(r'^CANT(?:IDAD)?\b', part_clean, re.IGNORECASE):
                    fields['Cantidad'] = part_clean
                    current_label = 'Cantidad'
                elif current_label:
                    fields[current_label] += f", {part_clean}"
                else:
                    if 'Producto' not in fields:
                        fields['Producto'] = part_clean
                    else:
                        fields['Producto'] += f", {part_clean}"
        # --- FIN EXTRACCIÓN DINÁMICA ---

        labeled = block

        # Referencia
        for pat in self.re_referencia:
            m = pat.search(labeled)
            if m:
                fields['Referencia'] = self._dedupe_ref(m.group(1).strip())
                break

        # Serial
        for pat in self.re_serial:
            m = pat.search(labeled)
            if m:
                fields['Serial'] = m.group(1).strip()
                break

        m = re.search(r'\bMARCA\s*:\s*([^,]+)', labeled, re.IGNORECASE)
        if m:
            fields['Marca'] = m.group(1).strip()

        m = re.search(r'\bMODELO\s*:\s*([^,]+)', labeled, re.IGNORECASE)
        if m:
            modelo = re.sub(r'\s+', ' ', m.group(1).strip())
            if len(modelo) > 1:
                fields['Modelo'] = modelo

        for attr, re_list, key in [
            ('re_uso',          self.re_uso,          'Compatibilidad'),
            ('re_categoria',    self.re_categoria,    'Categoria'),
            ('re_material',     self.re_material,     'Material'),
            ('re_presentacion', self.re_presentacion, 'Presentacion_Comercial'),
            ('re_norma',        self.re_norma,        'Norma_Tecnica'),
            ('re_oem',          self.re_oem,          'Numero_OEM'),
            ('re_after',        self.re_after,        'Numero_Aftermarket'),
            # ('re_subpartida',   self.re_subpartida,   'Subpartida'),
            ('re_unidad',       self.re_unidad,       'Unidad'),
            ('re_procedencia',  self.re_procedencia,  'Pais_Procedencia'),
            ('re_viscosidad',   self.re_viscosidad,   'Viscosidad'),
            ('re_tipo_aceite',  self.re_tipo_aceite,  'Tipo_Aceite'),
            ('re_tipo_filtro',  self.re_tipo_filtro,  'Tipo_Filtro'),
            ('re_micraje',      self.re_micraje,      'Micraje'),
            ('re_medidas',      self.re_medidas,      'Medidas'),
            ('re_tipo_bujia',   self.re_tipo_bujia,   'Tipo_Bujia'),
            ('re_rosca',        self.re_rosca,        'Rosca'),
            ('re_numero_calor', self.re_numero_calor, 'Numero_Calor'),
            ('re_tipo_terminal',self.re_tipo_terminal,'Tipo_Terminal'),
            ('re_tipo_sensor',  self.re_tipo_sensor,  'Tipo_Sensor'),
            ('re_tipo_soporte', self.re_tipo_soporte, 'Tipo_Soporte'),
            ('re_incluye',      self.re_incluye,      'Incluye_Accesorios'),
        ]:
            val = self._extract_with_patterns(labeled, re_list)
            if val:
                fields[key] = val.upper() if key in ('Tipo_Aceite', 'Estado_Producto', 'Incluye_Accesorios') else val

        m = re.search(r'\bCOMPOSICI[ÓO]N\s*:\s*([^,]+)', labeled, re.IGNORECASE)
        if m:
            fields['Composicion'] = m.group(1).strip()

        estado = self._extract_with_patterns(labeled, self.re_estado)
        if estado:
            fields['Estado_Producto'] = estado.upper()

        # Unidad especial: normaliza a 'UND'
        if 'Unidad' in fields:
            fields['Unidad'] = 'UND'

        # Capacidad
        cap_l = self._extract_with_patterns(labeled, self.re_capacidad_l)
        if cap_l:
            m = re.search(r'[\d]+(?:[\.,]\d+)?', cap_l)
            if m:
                fields['Capacidad_L'] = m.group(0).replace(',', '.')

        # Medidas numéricas
        for re_list, key, clean in [
            (self.re_longitud, 'Longitud', True),
            (self.re_ancho,    'Ancho',    True),
            (self.re_paso,     'Paso',     True),
            (self.re_voltaje,  'Voltaje',  True),
        ]:
            val = self._extract_with_patterns(labeled, re_list)
            if val:
                fields[key] = re.sub(r'[^\d\.,]', '', val) if clean else val

        # Cantidades
        qty_candidates = [
            {"n": int(m.group(1)), "unit": "UND", "has_unit": True, "pos": m.start()}
            for m in self.re_qty_with_unit.finditer(labeled)
        ]
        for m in self.re_qty_paren_opt_unit.finditer(labeled):
            suffix = ')' + labeled[m.end(1): m.end(1) + 15]
            has_unit = bool(self.re_unit_suffix.search(suffix))
            qty_candidates.append({"n": int(m.group(1)), "unit": "UND" if has_unit else None,
                                   "has_unit": has_unit, "pos": m.start()})
        qty_candidates += [
            {"n": int(m.group(1)), "unit": None, "has_unit": False, "pos": m.start()}
            for m in self.re_qty_simple_no_unit.finditer(labeled)
        ]

        if qty_candidates:
            qty_candidates.sort(key=lambda q: q["pos"])
            with_unit = [q for q in qty_candidates if q["has_unit"]]
            chosen = with_unit[0] if with_unit else qty_candidates[0]
            fields['Cantidad'] = str(chosen["n"])
            fields['Unidad']   = chosen["unit"] or fields.get('Unidad') or 'UND'

        self._extract_pais_origen(labeled, fields)

        # Limpieza final: eliminar comas al final de cada valor
        for k in fields:
            if isinstance(fields[k], str):
                fields[k] = fields[k].strip().rstrip(',')
                
        return fields

    # ==========================
    # Utilidades de DataFrame
    # ==========================
    def _drop_empty_optional_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        cols_drop = [
            col for col in self.OPTIONAL_COLUMNS
            if col in df.columns and (
                df[col].astype(str).str.strip().eq("").all() or df[col].isna().all()
            )
        ]
        return df.drop(columns=cols_drop) if cols_drop else df

    def extract_products_from_text(self, text: str, pdf_filename: str) -> pd.DataFrame:
        """Extrae todos los productos de todas las declaraciones del texto.

        Busca bloques de declaración ("DECLARACION X DE Y") y dentro de
        cada uno busca bloques de producto ("PRODUCTO:" o "NOMBRE TECNICO:").

        Args:
            text: Texto completo del PDF de declaración de importación.
            pdf_filename: Nombre del archivo PDF (para metadatos).

        Returns:
            DataFrame con todos los productos extraídos, ordenados por
            columnas conocidas primero y columnas dinámicas después.
        """
        cleaned_text = self.clean_text(text)
        declaration_pattern = re.compile(r'(DECLARACI[ÓO]N\s+(\d+)\s+DE\s+\d+)', re.IGNORECASE)
        declaration_matches = list(declaration_pattern.finditer(cleaned_text))

        product_pattern = re.compile(
            r'(?:PRODUCTO|NOMBRE\s+TECNICO\s+DEL\s+PRODUCTO)\s*:\s*'
            r'(.*?)(?://\s*(?=(?:PRODUCTO|NOMBRE\s+TECNICO\s+DEL\s+PRODUCTO)\s*:|$)|\Z)',
            re.IGNORECASE | re.DOTALL
        )

        all_products = []
        for idx, match in enumerate(declaration_matches):
            declaration_num = match.group(2)
            start = match.end()
            end = declaration_matches[idx + 1].start() if idx + 1 < len(declaration_matches) else len(cleaned_text)
            declaration_text = cleaned_text[start:end].strip()

            for product_match in product_pattern.finditer(declaration_text):
                product_text = product_match.group(1).strip()
                if not product_text:
                    continue
                product_data = self._extract_product_fields(product_text)
                if product_data:
                    product_data['Archivo']    = pdf_filename
                    product_data['Declaracion'] = declaration_num
                    all_products.append(product_data)

        if all_products:
            df = pd.DataFrame(all_products)
            
            # Ordenamos primero las columnas conocidas si existen, luego las dinámicas
            ordered = [c for c in self.BASE_COLUMNS if c in df.columns] + \
                      [c for c in self.OPTIONAL_COLUMNS if c in df.columns]
            
            dynamic_cols = [c for c in df.columns if c not in ordered]
            ordered.extend(dynamic_cols)
            
            df = df[ordered]
            
            # Eliminar CUALQUIER columna que esté completamente vacía
            cols_to_drop = [
                col for col in df.columns
                if df[col].astype(str).str.strip().eq("").all() or df[col].isna().all() or df[col].astype(str).str.lower().eq("nan").all()
            ]
            if cols_to_drop:
                df = df.drop(columns=cols_to_drop)
        else:
            df = pd.DataFrame(columns=self.BASE_COLUMNS)

        return df

    def save_products_to_excel(self, df: pd.DataFrame, excel_file: str) -> None:
        """Guarda el DataFrame de productos en un archivo Excel con formato.

        Crea el directorio de salida si no existe y aplica color de fondo
        azul claro a los encabezados de columna.

        Args:
            df: DataFrame con los productos extraídos.
            excel_file: Ruta completa del archivo Excel de salida.

        Raises:
            RuntimeError: Si openpyxl no está instalado.
        """
        if df.empty:
            print("No se encontraron productos para guardar.")
            return
        os.makedirs(os.path.dirname(excel_file), exist_ok=True)
        header_fill = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
        try:
            with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name='Productos', index=False)
                ws = writer.sheets['Productos']
                for cell in ws[1]:
                    cell.fill = header_fill
        except ImportError as e:
            raise RuntimeError("Para escribir .xlsx necesitas 'openpyxl'. Instala con: pip install openpyxl") from e
        print(f"Productos guardados en {excel_file}: {len(df)} productos")


# =========================
# Programa principal
# =========================

if __name__ == "__main__":
    base_path     = os.path.dirname(os.path.abspath(__file__))
    pdf_directory = os.path.join(base_path, "PDF_A_LEER")
    output_dir    = os.path.join(pdf_directory, "EXCEL_PRODUCTOS_LEIDOS")
    os.makedirs(pdf_directory, exist_ok=True)
    os.makedirs(output_dir,    exist_ok=True)

    pdf_files = [
        os.path.join(pdf_directory, f)
        for f in os.listdir(pdf_directory)
        if f.lower().endswith(".pdf")
    ]

    if not pdf_files:
        print(f"No se encontraron archivos PDF en: {pdf_directory}")
        raise SystemExit(0)

    extractor = ProductExtractor()

    for ruta_pdf in pdf_files:
        base           = os.path.basename(ruta_pdf)
        nombre_sin_ext = os.path.splitext(base)[0]
        print(f"\nProcesando: {base}")

        texto_extraido = extraer_texto_pdf(ruta_pdf)

        print("   -> Extrayendo productos...")
        df_products = pd.DataFrame()
        try:
            df_products = extractor.extract_products_from_text(texto_extraido, base)
            if not df_products.empty:
                print(f"   -> Productos extraídos: {len(df_products)}")
            else:
                print("   -> No se encontraron productos en este PDF.")
        except Exception as e:
            print(f"   -> Error al extraer productos: {e}")

        if df_products.empty:
            continue

        excel_path = os.path.join(output_dir, f"{nombre_sin_ext}_productos.xlsx")
        try:
            extractor.save_products_to_excel(df_products, excel_path)
        except Exception as e:
            print(f"   -> Error al guardar productos: {e}")

    print("\nProceso de extracción de productos completado.")

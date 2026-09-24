"""Entidades de dominio del sistema de declaración de importación.

Define las entidades de negocio principales:
- Declaration: Declaración de importación (DIM)
- Product: Producto declarado en la importación
- InvoiceItem: Línea individual de una factura
- InvoiceMetadata: Metadatos de una factura
- InvoiceDocument: Documento completo de factura (metadata + items)
- ProcessingResult: Resultado del procesamiento de documentos

Estas entidades son independientes de la infraestructura y se
usan en toda la capa de aplicación.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from domain.value_objects import Money, Quantity


@dataclass
class Declaration:
    """Representa una declaración de importación (DIM).

    Attributes:
        numero: Número secuencial de la declaración (ej: "1", "2").
        fecha: Fecha de la declaración en formato DD/MM/AAAA.
        proveedor: Nombre del proveedor o "DECLARACION".
        raw: Texto crudo de la declaración (opcional).
    """
    numero: str
    fecha: str
    proveedor: str
    raw: str | None = None


@dataclass
class Product:
    """Representa un producto declarado en una importación.

    Attributes:
        referencia: Código de referencia del producto.
        descripcion: Descripción del producto.
        cantidad: Cantidad declarada (objeto Quantity).
        unidad: Unidad de medida (ej: "UND", "KG").
        pais_origen: País de origen del producto (opcional).
    """
    referencia: str
    descripcion: str
    cantidad: Quantity
    unidad: str
    pais_origen: str | None = None


@dataclass
class InvoiceItem:
    """Representa una línea individual de una factura.

    Attributes:
        referencia: Código de referencia del producto.
        descripcion: Descripción del producto.
        cantidad: Cantidad facturada (objeto Quantity).
        unidad: Unidad de medida.
        valor_unitario: Precio unitario (objeto Money).
        valor_total: Valor total de la línea (objeto Money).
    """
    referencia: str
    descripcion: str
    cantidad: Quantity
    unidad: str
    valor_unitario: Money
    valor_total: Money


@dataclass
class InvoiceMetadata:
    """Metadatos de una factura de importación.

    Attributes:
        num_factura: Número de factura.
        fecha_factura: Fecha de la factura.
        proveedor: Nombre del proveedor.
        pais_origen: País de origen de la mercancía.
        incoterm: Término comercial (ej: FOB, CIF).
        moneda: Moneda de la factura (ej: EUR, USD).
        tipo_cambio: Tipo de cambio a moneda local.
        importador: Nombre del importador.
        registro_declaracion: Número de registro de declaración.
        fecha_declaracion: Fecha de la declaración.
        aduana: Aduana de ingreso.
        medio_transporte: Medio de transporte utilizado.
        conocimiento_embarque: Número de conocimiento de embarque.
        total_mercancia: Valor total de la mercancía.
        flete: Costo de flete.
        seguro: Costo de seguro.
        otros_gastos: Otros gastos.
        total_factura: Total de la factura.
    """
    num_factura: str
    fecha_factura: str
    proveedor: str
    pais_origen: str
    incoterm: str
    moneda: str
    tipo_cambio: Decimal
    importador: str
    registro_declaracion: str | None = None
    fecha_declaracion: str | None = None
    aduana: str | None = None
    medio_transporte: str | None = None
    conocimiento_embarque: str | None = None
    total_mercancia: Money | None = None
    flete: Money | None = None
    seguro: Money | None = None
    otros_gastos: Money | None = None
    total_factura: Money | None = None


@dataclass
class InvoiceDocument:
    """Documento completo de factura con metadata e items.

    Attributes:
        metadata: Metadatos de la factura (InvoiceMetadata).
        items: Lista de ítems de la factura (list[InvoiceItem]).
    """
    metadata: InvoiceMetadata
    items: list[InvoiceItem]


@dataclass
class ProcessingResult:
    """Resultado del procesamiento de documentos de importación.

    Attributes:
        declarations: Lista de declaraciones extraídas (entidades de dominio).
        products: Lista de productos extraídos (entidades de dominio).
        invoices: Lista de facturas procesadas.
        declarations_data: Lista de diccionarios con los datos completos de
            declaraciones (columnas DIM originales, para el frontend).
        products_data: Lista de diccionarios con los datos completos de
            productos (todas las columnas del extractor, para el frontend).
    """
    declarations: list[Declaration]
    products: list[Product]
    invoices: list[InvoiceDocument]
    declarations_data: list[dict] | None = None
    products_data: list[dict] | None = None
    comparative: dict | None = None

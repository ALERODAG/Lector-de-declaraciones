"""Tests del servicio de comparativo DIM vs facturas."""

from decimal import Decimal

from application.services.comparative_service import (
    FACTOR_SEGUROS,
    ComparativeService,
    _normalizar_referencia,
    _parse_decimal,
)
from domain.entities import InvoiceDocument, InvoiceItem, InvoiceMetadata
from domain.value_objects import Money, Quantity


def _invoice(referencias_cant):
    items = [
        InvoiceItem(
            referencia=ref,
            descripcion="",
            cantidad=Quantity(value=Decimal(str(cant))),
            unidad="UND",
            valor_unitario=Money(amount=Decimal("1.00")),
            valor_total=Money(amount=Decimal("0.00")),
        )
        for ref, cant in referencias_cant
    ]
    return InvoiceDocument(
        metadata=InvoiceMetadata(
            num_factura="F1",
            fecha_factura="01/01/2026",
            proveedor="PROV",
            pais_origen="FR",
            incoterm="FOB",
            moneda="USD",
            tipo_cambio=Decimal("1.0"),
            importador="IMP",
        ),
        items=items,
    )


class TestParseDecimal:
    def test_millares_y_decimales(self):
        assert _parse_decimal("26.559.09") == Decimal("26559.09")

    def test_millares_sin_decimales(self):
        assert _parse_decimal("2.200") == Decimal("2200")

    def test_decimal_espanol(self):
        assert _parse_decimal("22.58") == Decimal("22.58")

    def test_decimal_con_coma(self):
        assert _parse_decimal("1.234,56") == Decimal("1234.56")

    def test_entero(self):
        assert _parse_decimal("360") == Decimal("360")

    def test_none_y_vacio(self):
        assert _parse_decimal(None) is None
        assert _parse_decimal("") is None


class TestNormalizarReferencia:
    def test_con_codigo_alterno(self):
        assert _normalizar_referencia("N300501/N3005") == "N300501"

    def test_simple(self):
        assert _normalizar_referencia("TCK1671") == "TCK1671"

    def test_case_insensitive(self):
        assert _normalizar_referencia("tck1671") == "TCK1671"


class TestSeguros:
    def test_seguro_cuadra_con_factor(self):
        # FOB SOFABEX real: 26559.09 x 0.00085 = 22.575 -> 22.58
        svc = ComparativeService()
        r = svc.build(
            [{"DECLARACION": "D1", "VALOR_FOB_USD": "26.559.09",
              "VALOR_SEGUROS_USD": "22.58"}],
            [],
            [],
        )
        assert len(r["seguros"]) == 1
        s = r["seguros"][0]
        assert s["seguros_calculado"] == "22.58"
        assert s["seguros_declarado"] == "22.58"
        assert s["match"] is True
        assert r["factor_seguros"] == str(FACTOR_SEGUROS)

    def test_seguro_con_diferencia(self):
        svc = ComparativeService()
        r = svc.build(
            [{"DECLARACION": "D1", "VALOR_FOB_USD": "1000.00",
              "VALOR_SEGUROS_USD": "5.00"}],
            [],
            [],
        )
        s = r["seguros"][0]
        assert s["seguros_calculado"] == "0.85"
        assert s["match"] is False

    def test_sin_valores_seguros(self):
        svc = ComparativeService()
        r = svc.build([{"DECLARACION": "D1", "VALOR_FOB_USD": "1000.00"}], [], [])
        s = r["seguros"][0]
        assert s["seguros_declarado"] == "0.00"
        assert s["match"] is False


class TestCantidades:
    def test_solo_referencias_dim_que_existen_en_factura(self):
        svc = ComparativeService()
        prods = [
            {"Referencia": "N300501/N3005", "Cantidad": 320},
            {"Referencia": "N301701/N3017", "Cantidad": 360},
            {"Referencia": "N999999", "Cantidad": 99},  # no esta en factura
        ]
        inv = _invoice([("N300501", 360), ("N301701", 360), ("N304701", 1520)])
        r = svc.build([], prods, [inv])
        cantidad = r["cantidades"]
        refs = [c["referencia"] for c in cantidad]
        assert refs == ["N300501", "N301701"]
        assert cantidad[0]["match"] is False  # 360 vs 320
        assert cantidad[1]["match"] is True   # 360 vs 360

    def test_cantidades_agrupadas_por_referencia(self):
        svc = ComparativeService()
        prods = [{"Referencia": "A", "Cantidad": 10},
                  {"Referencia": "A", "Cantidad": 5}]
        inv = _invoice([("A", 15)])
        r = svc.build([], prods, [inv])
        assert len(r["cantidades"]) == 1
        assert r["cantidades"][0]["cantidad_dim"] == "15"
        assert r["cantidades"][0]["match"] is True

    def test_sin_facturas_no_genera_cantidades(self):
        svc = ComparativeService()
        r = svc.build([], [{"Referencia": "A", "Cantidad": 5}], [])
        assert r["cantidades"] == []

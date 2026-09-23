from decimal import Decimal

from application.services.invoice_processor import InvoiceProcessor
from infrastructure.extractors.adk import AdkExtractor
from infrastructure.extractors.gate import GateExtractor
from infrastructure.extractors.sofabex import SofabexExtractor
from infrastructure.extractors.universal import UniversalExtractor

GATE_TEXT = (
    "INVOICE NO. INV-2024-010\n"
    "INVOICE DATE 15-APR-2024\n"
    "SHIPMENT NO: 1234567\n"
    "CUSTOMER NO: 654321\n"
    "1 EA T185 TIMING BELT 85950080 100 7.505 750.5\n"
)

ADK_TEXT = (
    "IMPORTADORA EJEMPLO F9999-00037\n"
    "0001 0115410Z GMB 10 25,50 255,00\n"
)

UNIVERSAL_TEXT = (
    "001 X1234 POMPE ROTATIVE 25 O 9,54 238,50\n"
)

ADK_YADAS_REAL_TEXT = (
    "ADK CORPORATION\n"
    "CLAVE 8752\n"
    "RUC 155665129-2-2018 DV-02\n"
    "Zona Comercial Coco Ejemplo, Manzana CO-3-1 Local D9, Zona Libre de Colón, Rep. de Panamá\n"
    "Cuenta No: 9999 Factura No: F9999-00032\n"
    "Vendido a: IMPORTADORA EJEMPLO S.A.S NIT: 999.999.999-9 Fecha: 2-oct-25\n"
    "Dirección: BOGOTA - COLOMBIA Vendedor: J. MARTINEZ\n"
    "FOB OSAKA\n"
    "Consignado A:\n"
    "Condición: CREDITO\n"
    "Pedido: 0003640\n"
    "L/N\n"
    "Código Código 2 Descripción Marca Cantidad Precio Extensión\n"
    "1 G5-153X CRUCETA UNIVERSAL 27*82 GMB 4000 483,00 1.932.000,00\n"
    "2 G5-160X CRUCETA ISU. NPR 1998~2008 / FORD GMB 800 653,00 522.400,00\n"
    "60030x107\n"
    "3 GUT-21 04371-35020 CRUCETA.TOY. HILUX/4RUNNER RN/YN 84- GMB 800 688,00 550.400,00\n"
    "29*77\n"
    "4 G5-121X G5-121X CRUCETA TOY. LC/4.5/ VIGO 2.7/2TR-FE GMB 800 446,00 356.800,00\n"
    "FORTUNER 27*82\n"
    "5 GUIS-52 CRUCETA CHEV. LUV 1.6~2.0~2.2~2.3 (4x4) GMB 600 745,00 447.000,00\n"
    "TROOPER/NKR 29*79\n"
    "6 GUN-29 CRUCETA NIS. GMB 500 653,00 326.500,00\n"
    "D22/SAMURAI/510/N510/P510/TERRANO28*80\n"
    "7 GU-500 8-94158-199-1 CRUCETA ISU. CARIBE 1.9/2.3 24*62 GMB 400 440,00 176.000,00\n"
    "8 GUT-29 04371-0K080 / 04371C-0R4U0C30ETA TOY. HILUX/VIGO1KD/2KD 27*92 GMB 400 748,00 299.200,00\n"
    "9 GUN-46 CRUCETA NIS. FRONTIER D21/PICKUP/PATROL GMB 300 682,00 204.600,00\n"
    "Y60\n"
    "10 G5-310X CRUCETA 27*61.86 GMB 300 455,00 136.500,00\n"
    "11 GUT-20 04371-36021 CRUCETA TOY. COASTER/LAND CRUISER GMB 350 952,00 333.200,00\n"
    "12 GUD-84 CRUCETA DAI. DELTA 28*80 GMB 300 780,00 234.000,00\n"
    "13 GUT-23 04371-35030 CRUCETA TOY. GRN210/GRN280/285/VZJ95 GMB 200 810,00 162.000,00\n"
    "PRADO\n"
    "14 G5-178X CRUCETA MIT. MONTERO/DAKAR (369) CHEV. GMB 200 596,00 119.200,00\n"
    "C30\n"
    "15 G5-188X CRUCETA CHEV. B60 & C70 / DODGE 600 GMB 150 980,00 147.000,00\n"
    "(DIESEL) / FORD 600 & 800 35*107\n"
    "16 GUS-1 CRUCETA SUZ. SJ480/SJ410 25*65 GMB 100 546,00 54.600,00\n"
    "17 GUM-91 MB000948 CRUCETA MIT. MONTERO 25X76.50 GMB 100 965,00 96.500,00\n"
    "18 GUM-99 CRUCETA MIT. MONTERO 71.1*30 GMB 50 892,00 44.600,00\n"
    "19 GUK-12 CRUCETA GMB 50 923,00 46.150,00\n"
    "20 GUIS-66 CRUCETA ISU. NPR55 88-99 GMB 50 1.294,00 64.700,00\n"
    "21 GUMZ-9 CRUCETA KIA. BEST/SPORTAGE/CERES 26*71 GMB 40 710,00 28.400,00\n"
    "22 GUMZ-6 CRUCETA MAZ. B1600/B2600 28*59 GMB 40 682,00 27.280,00\n"
    "23 GUM-81 MB000393 CRUCETA MIT. L200/L300/LANCER // CHEV. GMB 1500 587,00 880.500,00\n"
    "SUPER CARRY/N200/N300 // SUZ. SJ413 25*64\n"
    "24 GWS-13A 17400-60D01 965189B7/7A G96U5A6 3C9H5E8V.CMV/SPARK 0.8/1.0 DAE.DAMAS GMB 50 1.945,00 97.250,00\n"
    "3CYL/TICO 0.8\n"
    "25 GWS-15A 17400-82820 B/AGUA SUZ. G13A/SWIFT/FORSA 2/STEEM GMB 300 1.548,00 464.400,00\n"
    "26 GWIS-25A 8-94140-341-0 B/AGUA ISU. 4JA1/4JB1/D-MAX/NKR GMB 300 1.855,00 556.500,00\n"
    "27 GWMZ-31A 8AB3-15-010B B/AGUA MAZ. B3/B5/B6 323/SOHC GMB 200 1.565,00 313.000,00\n"
    "28 GWS-08A 17400-82810 B/AGUA SUZ. G10A/SPRINT/FORSA 1 GMB 200 1.272,00 254.400,00\n"
    "29 GWS-03A 17400-73001 B/AGUA SUZ. F10A/CARRY LJ80/SJ410 GMB 200 1.222,00 244.400,00\n"
    "30 GWMZ-58A LF01-15-100A B/AGUA MAZ. 3/6 2.0/6 2.3/ECOSPORT LF/L3 GMB 180 1.996,00 359.280,00\n"
    "31 GWS-16A 17400-60810 B/AGUA SUZ. G16A/G16A VITARA GMB 150 1.457,00 218.550,00\n"
    "32 GWMZ-57A ZJ01-15-010A B/AGUA MAZDA 2 1.5CC MAZDA 3 1.6CC GMB 120 2.601,00 312.120,00\n"
    "33 GWHY-19A 25100-02500/ GWKRB-1/A0G7AUA.HYU. ATOS/PRIME KIA.PICANTO GMB 50 1.674,00 83.700,00\n"
    "34 GWMZ-21A E301-15-010A B/AGUA MAZ. E3/E5 323 GMB 100 1.217,00 121.700,00\n"
    "35 GWM-17A MD997076 B/AGUA HYU. G4EH ACCENT/EXCEL GMB 100 1.360,00 136.000,00\n"
    "MIT.LANCER 4G15\n"
    "B/AGUA HYU. G4EH ACCENT/EXCEL\n"
    "MIT.LANCER 4G15\n"
    "36 GWS-36A 17400-77810 B/AGUA SUZ. J18A/J20A VITARA 97- GMB 100 2.183,00 218.300,00\n"
    "37 GWN-84A 21010-VK525/EB300B/AGUA NIS. YD25/NAVARA GMB 80 2.640,00 211.200,00\n"
    "38 GWN-90A 21010-EN225 B/AGUA NIS. MR18DE/MR20DE/TIIDA/QASHQAI GMB 80 2.446,00 195.680,00\n"
    "39 GWMZ-41A 8AG9-15-010 B/AGUA MAZ. FS/MATSURI/626 GMB 50 1.963,00 98.150,00\n"
    "40 GWMZ-38A 8AL1-15-010A B/AGUA MAZ. G5/G6 MPV/B2600 GMB 50 1.825,00 91.250,00\n"
    "41 GWF-119A BOMBA DE AGUA FORD GMB 60 2.412,00 144.720,00\n"
    "42 GWMZ-39A 8ABB-15-010A B/AGUA MAZ. ZL/ZM/B5/B6/BP 323/DOHC GMB 50 2.582,00 129.100,00\n"
    "43 GWN-40A 21010-40F00 B/AGUA NIS. KA24-DE PICKUP/D22 GMB 50 1.457,00 72.850,00\n"
    "44 GWR-13A 7701472182 B/AGUA REN. MEGANE 2/DUSTER 2.0 (4X4-4X2) GMB 50 1.996,00 99.800,00\n"
    "45 GWT-12A 16100-39116 B/AGUA TOY. 12R/HILUX GMB 40 2.187,00 87.480,00\n"
    "46 GWT-150A 16100-09260/39485B/AGUA TOY. 1KD-FTV/2KD-FTV GMB 10 4.060,00 40.600,00\n"
    "VIGO/PRADO/FORTUNER\n"
    "47 GWN-86A 21010-6N225/6 B/AGUA NIS. QR25DE/QR20DE XTRAIL/T30/T31 GMB 30 2.446,00 73.380,00\n"
    "48 GWN-73A 21010-4M500 B/AGUA NIS. QG15/QG18DE ALMERA 00- GMB 10 1.674,00 16.740,00\n"
    "49 GWIS-31A 8-94376-847-0 B/AGUA ISU. 4ZE1/TROOPER 2.6 GMB 20 2.021,00 40.420,00\n"
    "50 GWDW-18A 96353151 B/AGUA CHEV. OPTRA 1.8 LIMITEC 1.8L VIVANT GMB 20 2.096,00 41.920,00\n"
    "51 GWM-23A MD971582 B/AGUA MIT. 4G63K/4GG4K L300 GMB 20 1.471,00 29.420,00\n"
    "52 GWMZ-49A 8ALA-15-100 B/AGUA MAZ. WL/BT50/B2500 GMB 20 1.816,00 36.320,00\n"
    "53 GWS-20A 17400-66810 B/AGUA SUZ. GRAND VITARA 2.5 Y 2.7 (H25A) GMB 30 2.839,00 85.170,00\n"
    "/GMB\n"
    "54 GWIS-29A BOMBA AGUA CHEVROLET LUV 1.6 1995 WFR GMB 40 2.282,00 91.280,00\n"
    "/GMB\n"
    "55 GWT-75A 16100-61012 B/AGUA TOY. 3F/FJ70 ALTA GMB 30 3.084,00 92.520,00\n"
    "56 GWO-18A B/AGUA DAEWO GMB 12 2.096,00 25.152,00\n"
    "57 G5-213X CRUCETA FORD. RANGER 27*92 GMB 1000 512,00 512.000,00\n"
    "58 ST-1640-G CRUCETA TIMON 16X40 GMB 200 641,00 128.200,00\n"
    "16032 Sub-Total 12.912.482,00\n"
    "Total JPY 12.912.482,00\n"
    "Página 2 de 2\n"
)


def _build_processor() -> InvoiceProcessor:
    return InvoiceProcessor(
        {
            "sofabex": SofabexExtractor,
            "gate": GateExtractor,
            "adk": AdkExtractor,
            "universal": UniversalExtractor,
        }
    )


def test_processor_selects_gate_extractor() -> None:
    document = _build_processor().process(GATE_TEXT)

    assert document.metadata.proveedor == "GATE"
    assert len(document.items) == 1
    assert document.items[0].referencia == "T185"
    assert document.items[0].cantidad.value == Decimal("100")
    assert document.items[0].valor_total.amount == Decimal("750.5")


def test_processor_selects_adk_extractor() -> None:
    document = _build_processor().process(ADK_TEXT)

    assert document.metadata.proveedor == "ADK"
    assert len(document.items) == 1
    assert document.items[0].referencia == "0115410Z"
    assert document.items[0].cantidad.value == Decimal("10")
    assert document.items[0].valor_unitario.amount == Decimal("25.5")
    assert document.items[0].valor_total.amount == Decimal("255.0")


def test_processor_falls_back_to_universal_extractor() -> None:
    document = _build_processor().process(UNIVERSAL_TEXT)

    assert document.metadata.proveedor == "UNIVERSAL"
    assert len(document.items) == 1
    assert document.items[0].referencia == "X1234"
    assert document.items[0].cantidad.value == Decimal("25")
    assert document.items[0].valor_total.amount == Decimal("238.50")


def test_adk_yadas_real_invoice_extracts_58_items() -> None:
    document = _build_processor().process(ADK_YADAS_REAL_TEXT)

    assert document.metadata.proveedor == "ADK"
    assert len(document.items) == 58
    assert document.items[0].referencia == "G5-153X"
    assert document.items[0].cantidad.value == Decimal("4000")
    assert document.items[0].valor_unitario.amount == Decimal("483.0")
    assert document.items[0].valor_total.amount == Decimal("1932000.0")
    assert document.items[-1].referencia == "ST-1640-G"


def test_adk_yadas_real_invoice_metadata() -> None:
    document = _build_processor().process(ADK_YADAS_REAL_TEXT)

    assert document.metadata.num_factura == "F9999-00032"
    assert document.metadata.fecha_factura == "2-oct-25"
    assert document.metadata.moneda == "JPY"
    assert document.metadata.incoterm == "FOB"
    assert document.metadata.pais_origen == "OSAKA"
    assert "IMPORTADORA EJEMPLO" in document.metadata.importador
    assert document.metadata.total_factura.amount == Decimal("12912482.0")


def test_adk_yadas_item_totals_match_invoice_subtotal() -> None:
    document = _build_processor().process(ADK_YADAS_REAL_TEXT)

    subtotal = sum(item.valor_total.amount for item in document.items)
    assert subtotal == Decimal("12912482.0")
    assert subtotal == document.metadata.total_mercancia.amount


def test_registry_contains_all_clean_extractors() -> None:
    import importlib

    from core.registry import get_registered_extractors

    if not get_registered_extractors():
        importlib.reload(__import__("infrastructure.extractors", fromlist=["*"]))

    registry = get_registered_extractors()
    assert {"sofabex", "gate", "adk", "universal"} <= set(registry)
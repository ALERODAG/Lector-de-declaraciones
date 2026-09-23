from extractors.facturas_gate import extract_product_lines


def test_extract_product_lines_gate_parses_quantity_price_total() -> None:
    sample_text = "1 EA ABC-123 123456 2 474.50 949.00\n"
    items = extract_product_lines(sample_text)

    assert len(items) == 1
    item = items[0]
    assert item["Cantidad"] == 2
    assert item["Precio_Unitario"] == 474.50
    assert item["Valor_Total"] == 949.00
    assert item["Referencia"] == "ABC-123"
    assert item["Product Number"] == "123456"


def test_extract_product_lines_gate_recovers_shifted_quantity_and_unit_price() -> None:
    sample_text = "1 EA T185 TIMING BELT 85950080 100 7.505 750.5\n"
    items = extract_product_lines(sample_text)

    assert len(items) == 1
    item = items[0]
    assert item["Cantidad"] == 100.0
    assert item["Precio_Unitario"] == 7.505
    assert item["Valor_Total"] == 750.5
    assert item["Referencia"] == "T185"
    assert item["Product Number"] == "85950080"

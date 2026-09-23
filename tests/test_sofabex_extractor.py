from decimal import Decimal

from infrastructure.extractors.sofabex import SofabexExtractor


def test_sofabex_extractor_handles_space_in_quantity() -> None:
    sample_text = (
        "SOFABEX\n"
        "FACTURE N: ABC123\n"
        "ADRESSE DE FACTURATION: CLIENT EXAMPLE\n"
        "001 N300501 /N3005 POMPE N3005-BOITE SOFABEX EMBALLE 1 520 O 9,54 3 434,40"
    )

    extractor = SofabexExtractor()
    document = extractor.extract(sample_text)

    assert document.metadata.proveedor == "SOFABEX"
    assert len(document.items) == 1
    assert document.items[0].cantidad.value == Decimal("1520")
    assert document.items[0].valor_total.amount == Decimal("3434.40")

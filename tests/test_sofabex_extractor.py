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


SOFABEX_REAL_STRIPPED_TEXT = (
    "website.sofabex.com\n"
    "5 RUE DU FER A CHEVAL F9999-00108 SARCELLES\n"
    "95200 SARCELLES FRANCE\n"
    "Adresse de Facturation: 001415 001\n"
    "IMPORTADORA EJEMPLO S.A.S.\n"
    "FACTURE n\u00b0 : F9999-00108\n"
    "NIT 999.999.999-9\n"
    "Date n\u00b0 Compte tiers 217 BOGOTA\n"
    "17/10/2025 025100 COLOMBIE\n"
    "Adresse de Livraison:\n"
    "IMPORTADORA EJEMPLO S.A.S.\n"
    "217 BOGOTA\n"
    "ORIGINE FRANCE Page 1\n"
    "LLgg Code Article Libell� Qt� Unit� Prix Unit. C/M Montant HT\n"
    "Cde :001415 / 001 BL : 000001 Du : 17/10/2025 V/R�f. mail 26/07/25\n"
    "001 N300501 /N3005 POMPE N3005-BOITE SOFABEX EMBALLE 360,00 O 9,54 3 434,40 N30 3 POMP 001\n"
    "002 N301701 /N3017 POMPE N3017-BOITE SOFABEX EMBALLE 320,00 O 9,69 3 100,80 N30 3 POMP 002\n"
    "003 N304701 /N3047 POMPE N3047-BOITE SOFABEX EMBALLE 1 520,00 O 10,57 16 066,40 N30 3 POMP 003\n"
    "1 075,00 985,00 55,00 5,00\n"
    "Total : 5 palette(s) comprenant 55 cartons. Poids total Net : 985 Kg Total Brut : 1075 Kg\n"
    "0,00\n"
    "NIT 999.999.999-9 - HS Code : 84133080\nThe exporter of the products covered by this document\n"
    "Transporteur : EXW\n"
    "CONDITIONS DE REGLEMENT : Avant Exp. Devise : EURO\n"
    "Montant HT Escompte Dont Port Dont Emballage TVA % Base TVA Montant TVA Montant TTC\n"
    "22 601,60 0,00 0,00 0,00 0,00 0,00 0,00 22 601,60\n"
    "SOFABEX : T.V.A. Payee sur les debits. SAS au capital de 243000 Euros - SIRET: 99999999900000 - APE 2813Z\n"
)


def test_sofabex_extractor_real_invoice_extracts_3_items() -> None:
    document = SofabexExtractor().extract(SOFABEX_REAL_STRIPPED_TEXT)

    assert document.metadata.proveedor == "SOFABEX"
    assert document.metadata.num_factura == "F9999-00108"
    assert document.metadata.moneda == "EUR"
    assert document.metadata.importador != "N/A"
    assert len(document.items) == 3

    assert document.items[0].referencia == "N300501"
    assert document.items[0].cantidad.value == Decimal("360")
    assert document.items[0].valor_unitario.amount == Decimal("9.54")
    assert document.items[0].valor_total.amount == Decimal("3434.40")

    assert document.items[2].cantidad.value == Decimal("1520")
    assert document.items[2].valor_total.amount == Decimal("16066.40")


def test_sofabex_extractor_real_invoice_totals_match_legacy() -> None:
    document = SofabexExtractor().extract(SOFABEX_REAL_STRIPPED_TEXT)

    subtotal = sum(item.valor_total.amount for item in document.items)
    assert subtotal == Decimal("22601.6")
    assert subtotal == document.metadata.total_mercancia.amount
    assert subtotal == document.metadata.total_factura.amount

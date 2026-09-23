from decimal import Decimal

from application.use_cases.process_documents import ProcessDocumentsUseCase
from application.services.invoice_processor import InvoiceProcessor
from infrastructure.parsers.declaration_parser import DeclarationParser
from domain.entities import Product
from infrastructure.extractors.sofabex import SofabexExtractor
from core.registry import EXTRACTOR_REGISTRY


class DummyTextExtractor:
    def extract_text(self, path: str) -> str:
        if "declaration" in path:
            return "DECLARACION 1 DE 2024\n12/12/2024"

        return (
            "SOFABEX\n"
            "FACTURE N: ABC123\n"
            "ADRESSE DE FACTURATION: CLIENT EXAMPLE\n"
            "001 N300501 /N3005 POMPE N3005-BOITE SOFABEX EMBALLE 1 520 O 9,54 3 434,40"
        )


def test_process_documents_use_case_with_dummy_extractor() -> None:
    EXTRACTOR_REGISTRY.clear()
    EXTRACTOR_REGISTRY["sofabex"] = SofabexExtractor

    text_extractor = DummyTextExtractor()
    declaration_parser = DeclarationParser()
    invoice_processor = InvoiceProcessor(EXTRACTOR_REGISTRY)
    use_case = ProcessDocumentsUseCase(
        text_extractor=text_extractor,
        declaration_parser=declaration_parser,
        invoice_processor=invoice_processor,
    )

    result = use_case.execute("declaration.pdf", ["invoice.pdf"], products=[])  # type: ignore[arg-type]

    assert len(result.declarations) == 1
    assert result.declarations[0].numero == "1"
    assert len(result.invoices) == 1
    assert result.invoices[0].items[0].cantidad.value == Decimal("1520")

from infrastructure import extractors  # noqa: F401
from core.registry import get_registered_extractors


def test_extractor_registry_contains_sofabex() -> None:
    registry = get_registered_extractors()
    assert "sofabex" in registry
    assert registry["sofabex"].__name__ == "SofabexExtractor"

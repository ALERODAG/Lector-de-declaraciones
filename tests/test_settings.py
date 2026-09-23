from infrastructure.config import AppSettings


def test_app_settings_defaults() -> None:
    settings = AppSettings(_env_file=None)

    assert settings.app_name == "lector_declaraciones"
    assert settings.environment == "development"
    assert isinstance(settings.cors_allowed_origins, list)
    assert settings.ocr_enabled is True

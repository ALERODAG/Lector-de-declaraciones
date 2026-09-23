import pytest

from infrastructure.config import AppSettings


@pytest.fixture(scope="session")
def app_settings() -> AppSettings:
    return AppSettings(_env_file=None)

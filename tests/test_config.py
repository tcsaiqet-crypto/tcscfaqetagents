"""Unit tests for config and secure API key loader."""

from src.config import config


def test_get_api_key_secure_loader() -> None:
    key = config.get_api_key()
    # Key should be non-empty string and stripped
    assert isinstance(key, str)
    assert len(key) > 0, "API key should be successfully detected from api/ folder"
    assert not key.startswith(" ") and not key.endswith(" ")

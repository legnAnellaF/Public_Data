from backend.app.config import get_settings


def test_enable_dynamic_public_data_defaults_to_false(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_DYNAMIC_PUBLIC_DATA", raising=False)
    get_settings.cache_clear()

    assert get_settings().enable_dynamic_public_data is False

    get_settings.cache_clear()

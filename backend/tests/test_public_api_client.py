import pytest

from backend.app.config import Settings
from backend.app.schemas.common import CategoryId
from backend.app.schemas.intent import IntentResult
from backend.app.schemas.public_data import PublicDataSource
from backend.app.services.public_api_adapters import adapt_external_payload, build_query_params
from backend.app.services.public_api_client import PublicApiClient
from backend.app.utils.errors import MalformedPublicDataError


def _settings(**overrides: object) -> Settings:
    values = {
        "app_name": "test",
        "version": "0.1.0",
        "app_env": "test",
        "mock_public_api": True,
        "public_api_timeout_seconds": 1,
        "public_api_cache_ttl_seconds": 300,
        "public_data_service_key": "",
        "air_quality_api_base_url": "",
        "real_estate_api_base_url": "",
        "traffic_api_base_url": "",
        "weather_api_base_url": "",
        "economy_api_base_url": "",
        "allowed_origins": ["http://localhost"],
    }
    values.update(overrides)
    return Settings(**values)


def _intent(category: CategoryId = CategoryId.ENVIRONMENT_AIR_QUALITY) -> IntentResult:
    return IntentResult(
        category=category,
        keywords=["서울", "미세먼지"],
        params={"region": "서울"},
        confidence=0.79,
        matched_rules=["environment_air_quality_keyword", "region_keyword"],
    )


def test_public_api_client_uses_mock_data_when_mock_mode_enabled() -> None:
    result = PublicApiClient(settings=_settings(mock_public_api=True)).fetch(_intent(), "서울 미세먼지")

    assert result.used_mock is True
    assert result.raw.category == CategoryId.ENVIRONMENT_AIR_QUALITY
    assert result.raw.data["region"] == "서울"
    assert result.raw.source.is_mock is True


def test_public_api_client_falls_back_to_mock_without_configured_base_url() -> None:
    result = PublicApiClient(settings=_settings(mock_public_api=False)).fetch(_intent(), "서울 미세먼지")

    assert result.used_mock is True
    assert result.fallback_reason == "base_url_missing"
    assert result.raw.source.is_mock is True


def test_build_query_params_includes_query_category_params_and_service_key() -> None:
    params = build_query_params(_intent(), "서울 미세먼지", "test-key")

    assert params == {
        "query": "서울 미세먼지",
        "category": "environment_air_quality",
        "region": "서울",
        "serviceKey": "test-key",
    }


def test_adapt_external_payload_accepts_dict_data_field() -> None:
    source = PublicDataSource(name="test api", url="https://example.test", updated_at="external", is_mock=False)
    raw = adapt_external_payload(
        CategoryId.REAL_ESTATE,
        {"data": {"labels": ["6월"], "values": [18.7]}},
        {"region": "강남구"},
        source,
    )

    assert raw.category == CategoryId.REAL_ESTATE
    assert raw.params == {"region": "강남구"}
    assert raw.data == {"labels": ["6월"], "values": [18.7]}
    assert raw.source == source


def test_adapt_external_payload_rejects_non_dict_data_field() -> None:
    source = PublicDataSource(name="test api", url=None, updated_at="external", is_mock=False)

    with pytest.raises(MalformedPublicDataError):
        adapt_external_payload(CategoryId.REAL_ESTATE, {"data": []}, {}, source)

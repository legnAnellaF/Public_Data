from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.cache import widget_response_cache


client = TestClient(app)


def setup_function() -> None:
    widget_response_cache.clear()


def test_widget_endpoint_returns_air_quality_widget_payload() -> None:
    response = client.post("/api/widget", json={"query": "서울 미세먼지"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["query"] == "서울 미세먼지"
    assert body["intent"]["category"] == "environment_air_quality"
    assert body["intent"]["params"] == {"region": "서울"}
    assert body["widget"]["title"] == "서울 미세먼지 현황"
    assert body["widget"]["chart"]["type"] == "bar"
    assert body["widget"]["chart"]["labels"] == ["PM10", "PM2.5"]
    assert body["widget"]["source"]["is_mock"] is True
    assert body["meta"]["cache_hit"] is False
    assert body["meta"]["mock_mode"] is True


def test_widget_endpoint_returns_cache_hit_on_repeated_query() -> None:
    first_response = client.post("/api/widget", json={"query": "서울 미세먼지"})
    second_response = client.post("/api/widget", json={"query": "서울 미세먼지"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["meta"]["cache_hit"] is False
    assert second_response.json()["meta"]["cache_hit"] is True


def test_widget_endpoint_returns_unsupported_for_unknown_query() -> None:
    response = client.post("/api/widget", json={"query": "아이돌 콘서트 예매"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unsupported"
    assert body["intent"]["category"] == "unknown"
    assert body["widget"] is None
    assert body["message"] == "현재 지원하지 않는 검색어입니다."

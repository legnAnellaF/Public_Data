from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from backend.app.config import get_settings
from backend.app.main import app
from backend.app.services.dataset_search import parse_data_go_kr_dataset_html, search_public_datasets

client = TestClient(app)

FIXTURE_HTML = """
<ul class="result-list">
  <li>
    <dl>
      <dt><a href="/tcs/dss/selectFileDataDetailView.do?publicDataPk=1"><span class="title">서울시 미세먼지 측정정보</span></a></dt>
      <dd class="desc">측정소별 PM10, PM2.5 농도 정보</dd>
    </dl>
    <div class="info-data"><p>제공기관 서울특별시</p></div>
  </li>
  <li>
    <dl>
      <dt><a href="https://www.data.go.kr/tcs/dss/selectFileDataDetailView.do?publicDataPk=2"><span class="title">전국 대기오염 통계</span></a></dt>
      <dd class="desc">월별 대기오염 통계 파일</dd>
    </dl>
    <div class="info-data"><p>제공기관 환경부</p></div>
  </li>
</ul>
"""


def setup_function() -> None:
    get_settings.cache_clear()


def test_parse_data_go_kr_dataset_html_extracts_required_fields() -> None:
    results = parse_data_go_kr_dataset_html(FIXTURE_HTML, limit=5)

    assert len(results) == 2
    assert results[0].title == "서울시 미세먼지 측정정보"
    assert results[0].provider == "서울특별시"
    assert results[0].link == "https://www.data.go.kr/tcs/dss/selectFileDataDetailView.do?publicDataPk=1"
    assert results[0].description == "측정소별 PM10, PM2.5 농도 정보"
    assert results[0].summary == "측정소별 PM10, PM2.5 농도 정보"
    assert results[0].source == "data.go.kr"


def test_search_public_datasets_uses_fixture_fetch_without_network() -> None:
    captured_urls: list[str] = []

    def fake_fetch(url: str) -> str:
        captured_urls.append(url)
        return FIXTURE_HTML

    results = search_public_datasets("서울 미세먼지", limit=1, fetch_html=fake_fetch)

    assert len(results) == 1
    parsed = urlparse(captured_urls[0])
    params = parse_qs(parsed.query)
    assert parsed.netloc == "www.data.go.kr"
    assert params["dType"] == ["FILE"]
    assert params["keyword"] == ["서울 미세먼지"]


def test_dataset_search_route_returns_disabled_schema_by_default(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_DYNAMIC_PUBLIC_DATA", raising=False)
    get_settings.cache_clear()

    response = client.post("/api/datasets/search", json={"query": "서울 미세먼지"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["query"] == "서울 미세먼지"
    assert body["results"] == []
    assert body["meta"]["mock_mode"] is True


def test_legacy_search_alias_returns_same_disabled_schema(monkeypatch) -> None:
    monkeypatch.delenv("ENABLE_DYNAMIC_PUBLIC_DATA", raising=False)
    get_settings.cache_clear()

    response = client.post("/api/search", json={"query": "서울 미세먼지"})

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["results"] == []

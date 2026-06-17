from backend.app.schemas.common import CategoryId
from backend.app.schemas.intent import IntentResult
from backend.app.services.dynamic_adapter import adapt_dynamic_widget_data


def test_dynamic_adapter_returns_widget_payload_contract_and_normalizes_chart_type() -> None:
    intent = IntentResult(category=CategoryId.ECONOMY, keywords=["주식"], params={}, confidence=0.7)
    payload = {
        "title": "업종별 주식수 분석",
        "summary": "공공데이터포털 파일 분석 결과",
        "chart": {
            "type": "pie",
            "labels": ["A", "B"],
            "datasets": [{"label": "주식수", "data": [10, 30], "unit": "주"}],
        },
        "source": {
            "name": "공공데이터포털 실시간 다운로드",
            "url": "https://www.data.go.kr/tcs/dss/selectFileDataDetailView.do?publicDataPk=test",
            "updated_at": "dynamic",
            "is_mock": False,
        },
    }

    widget = adapt_dynamic_widget_data("국내 주식", intent, payload, target_link=payload["source"]["url"])

    assert widget.title == "업종별 주식수 분석"
    assert widget.chart.type == "bar"
    assert widget.chart.labels == ["A", "B"]
    assert widget.chart.datasets[0].data == [10, 30]
    assert widget.cards[0].label == "주식수 합계"
    assert widget.table.columns == ["항목", "주식수"]
    assert widget.source.is_mock is False
    assert widget.source.url == payload["source"]["url"]

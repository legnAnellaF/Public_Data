from backend.app.schemas.common import CategoryId
from backend.app.services.intent_rules import analyze_intent


def test_analyze_intent_extracts_real_estate_region_and_keywords() -> None:
    result = analyze_intent("강남 아파트 실거래가")

    assert result.category == CategoryId.REAL_ESTATE
    assert result.params == {"region": "강남구"}
    assert result.keywords == ["강남구", "아파트", "실거래가"]
    assert result.confidence == 0.91
    assert result.matched_rules == ["real_estate_keyword", "region_keyword"]


def test_analyze_intent_returns_unknown_for_unsupported_query() -> None:
    result = analyze_intent("아이돌 콘서트 예매")

    assert result.category == CategoryId.UNKNOWN
    assert result.keywords == []
    assert result.params == {}
    assert result.confidence == 0.0
    assert result.matched_rules == []

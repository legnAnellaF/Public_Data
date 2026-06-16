import pytest

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


@pytest.mark.parametrize(
    ("query", "category"),
    [
        ("서울 미세먼지", CategoryId.ENVIRONMENT_AIR_QUALITY),
        ("부산 초미세먼지", CategoryId.ENVIRONMENT_AIR_QUALITY),
        ("오늘 대기질", CategoryId.ENVIRONMENT_AIR_QUALITY),
        ("강남 아파트 실거래가", CategoryId.REAL_ESTATE),
        ("강남 아파트 전세 가격 알고 싶어", CategoryId.REAL_ESTATE),
        ("마포대교 교통 상황", CategoryId.TRAFFIC),
        ("지금 내가 마포대교 지나가는 중인데 현재 마포대교 인근의 교통 상황을 알고싶어", CategoryId.TRAFFIC),
        ("오늘 서울 기온", CategoryId.WEATHER),
        ("오늘 서울 기온 알려줘", CategoryId.WEATHER),
        ("소비자물가", CategoryId.ECONOMY),
        ("소비자물가 확인하고 싶어", CategoryId.ECONOMY),
        ("sk하이닉스 주가", CategoryId.ECONOMY),
        ("오늘 오후에 sk하이닉스 주식이 얼마인지 확인하고싶어", CategoryId.ECONOMY),
        ("아이돌 콘서트 예매", CategoryId.UNKNOWN),
        ("맛집 추천", CategoryId.UNKNOWN),
    ],
)
def test_analyze_intent_handles_extended_korean_keyword_cases(query: str, category: CategoryId) -> None:
    result = analyze_intent(query)

    assert result.category == category


def test_analyze_intent_extracts_real_estate_deal_params() -> None:
    result = analyze_intent("강남 아파트 전세 가격 알고 싶어")

    assert result.category == CategoryId.REAL_ESTATE
    assert result.params["region"] == "강남구"
    assert result.params["deal_type"] == "전세"
    assert result.params["property_type"] == "아파트"


def test_analyze_intent_extracts_economy_indicator() -> None:
    result = analyze_intent("sk하이닉스 주가")

    assert result.category == CategoryId.ECONOMY
    assert result.params["indicator"] == "주가"

from dataclasses import dataclass

from backend.app.schemas.common import CategoryId


@dataclass(frozen=True)
class CategoryDefinition:
    id: CategoryId
    label: str
    description: str
    example_queries: list[str]


CATEGORIES: list[CategoryDefinition] = [
    CategoryDefinition(
        id=CategoryId.ENVIRONMENT_AIR_QUALITY,
        label="대기질/환경",
        description="미세먼지, 초미세먼지, 대기오염 등 환경 관련 공공데이터",
        example_queries=["서울 미세먼지", "부산 초미세먼지", "오늘 대기질"],
    ),
    CategoryDefinition(
        id=CategoryId.REAL_ESTATE,
        label="부동산",
        description="아파트 실거래가, 전세, 매매 가격 등 부동산 공공데이터",
        example_queries=["강남 아파트 실거래가", "서울 아파트 전세", "부동산 매매 가격"],
    ),
    CategoryDefinition(
        id=CategoryId.TRAFFIC,
        label="교통",
        description="교통량, 도로 혼잡도, 대중교통 이용객 관련 공공데이터",
        example_queries=["서울 교통량", "도로 혼잡도", "버스 이용객"],
    ),
    CategoryDefinition(
        id=CategoryId.WEATHER,
        label="날씨",
        description="기온, 강수량, 습도 등 날씨 관련 공공데이터",
        example_queries=["서울 날씨", "오늘 기온", "강수량"],
    ),
    CategoryDefinition(
        id=CategoryId.ECONOMY,
        label="경제",
        description="소비자물가, 유가, 환율 등 경제 지표 공공데이터",
        example_queries=["소비자물가", "유가", "환율"],
    ),
    CategoryDefinition(
        id=CategoryId.UNKNOWN,
        label="지원하지 않음",
        description="현재 MVP에서 지원하지 않는 검색어",
        example_queries=["아이돌 콘서트 예매"],
    ),
]


class PublicApiRegistry:
    """Small registry of supported categories and frontend demo queries."""

    def list_categories(self) -> list[dict[str, object]]:
        return [
            {
                "id": category.id.value,
                "label": category.label,
                "description": category.description,
                "example_queries": category.example_queries,
            }
            for category in CATEGORIES
        ]

    def demo_queries(self) -> list[dict[str, str]]:
        return [
            {"query": "서울 미세먼지", "expected_category": CategoryId.ENVIRONMENT_AIR_QUALITY.value},
            {"query": "강남 아파트 실거래가", "expected_category": CategoryId.REAL_ESTATE.value},
            {"query": "서울 교통량", "expected_category": CategoryId.TRAFFIC.value},
            {"query": "오늘 기온", "expected_category": CategoryId.WEATHER.value},
            {"query": "소비자물가", "expected_category": CategoryId.ECONOMY.value},
        ]

from backend.app.schemas.common import CategoryId
from backend.app.schemas.intent import IntentResult
from backend.app.services.keyword_extractor import KeywordExtractionResult, extract_query_keywords
from backend.app.utils.text import normalize_query, unique_preserving_order


REGION_ALIASES: dict[str, str] = {
    "서울": "서울",
    "부산": "부산",
    "대구": "대구",
    "인천": "인천",
    "광주": "광주",
    "대전": "대전",
    "울산": "울산",
    "세종": "세종",
    "경기": "경기",
    "강원": "강원",
    "충북": "충북",
    "충남": "충남",
    "전북": "전북",
    "전남": "전남",
    "경북": "경북",
    "경남": "경남",
    "제주": "제주",
    "강남구": "강남구",
    "강남": "강남구",
    "서초구": "서초구",
    "서초": "서초구",
    "송파구": "송파구",
    "송파": "송파구",
    "마포대교": "마포대교",
    "마포구": "마포구",
    "마포": "마포구",
    "종로구": "종로구",
    "종로": "종로구",
    "영등포구": "영등포구",
    "영등포": "영등포구",
}

DATE_KEYWORDS = {
    "오늘": "today",
    "현재": "current",
    "지금": "current",
    "이번달": "this_month",
    "최근": "recent",
}

CATEGORY_KEYWORDS: dict[CategoryId, list[str]] = {
    CategoryId.ENVIRONMENT_AIR_QUALITY: [
        "미세먼지",
        "초미세먼지",
        "대기질",
        "대기오염",
        "황사",
        "pm10",
        "pm2.5",
        "pm25",
    ],
    CategoryId.REAL_ESTATE: [
        "아파트",
        "실거래가",
        "전세",
        "부동산",
        "매매",
        "월세",
        "주택",
        "집값",
    ],
    CategoryId.TRAFFIC: [
        "교통량",
        "혼잡도",
        "도로",
        "버스",
        "이용객",
        "교통",
        "정체",
    ],
    CategoryId.WEATHER: [
        "날씨",
        "기온",
        "강수량",
        "습도",
        "비",
        "눈",
    ],
    CategoryId.ECONOMY: [
        "소비자물가",
        "물가",
        "유가",
        "환율",
        "cpi",
        "경제",
        "금리",
    ],
}
KOREAN_TO_BACKEND_CATEGORY: dict[str, CategoryId] = {
    "부동산": CategoryId.REAL_ESTATE,
    "교통": CategoryId.TRAFFIC,
    "날씨": CategoryId.WEATHER,
    "환경": CategoryId.ENVIRONMENT_AIR_QUALITY,
    "경제": CategoryId.ECONOMY,
    "금융": CategoryId.ECONOMY,
    "주식": CategoryId.ECONOMY,
    "인구": CategoryId.UNKNOWN,
    "복지": CategoryId.UNKNOWN,
    "관광": CategoryId.UNKNOWN,
    "의료": CategoryId.UNKNOWN,
    "교육": CategoryId.UNKNOWN,
    "일반": CategoryId.UNKNOWN,
}

AIR_QUALITY_PRIORITY_KEYWORDS = (
    "미세먼지",
    "초미세먼지",
    "pm10",
    "pm2.5",
    "대기질",
    "대기오염",
    "대기",
)

REAL_ESTATE_PROPERTY_TYPES = {
    "아파트": "아파트",
    "주택": "주택",
    "빌라": "빌라",
    "오피스텔": "오피스텔",
    "토지": "토지",
}

REAL_ESTATE_DEAL_TYPES = ("전세", "월세", "매매")

INDICATOR_KEYWORDS = {
    "소비자물가": "소비자물가",
    "환율": "환율",
    "금리": "금리",
    "주가": "주가",
}


def _find_regions(normalized_query: str) -> list[str]:
    matches: list[tuple[int, int, str]] = []
    for alias, canonical in REGION_ALIASES.items():
        index = normalized_query.find(alias.lower())
        if index >= 0:
            matches.append((index, -len(alias), canonical))
    matches.sort()
    return unique_preserving_order([match[2] for match in matches])


def _find_date_keywords(query: str) -> list[tuple[str, str]]:
    matches: list[tuple[int, str, str]] = []
    for keyword, value in DATE_KEYWORDS.items():
        index = query.find(keyword)
        if index >= 0:
            matches.append((index, keyword, value))
    matches.sort()
    return [(keyword, value) for _, keyword, value in matches]


def _find_category_keywords(normalized_query: str) -> dict[CategoryId, list[str]]:
    result: dict[CategoryId, list[str]] = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        found = [keyword for keyword in keywords if keyword.lower() in normalized_query]
        if found:
            result[category] = found
    return result


def _compact_search_text(normalized_query: str, extracted_keywords: list[str]) -> str:
    text = f"{normalized_query} {' '.join(extracted_keywords).lower()}"
    return text.replace(" ", "").replace("-", "").replace("_", "").replace(".", "")


def _find_air_quality_priority_keywords(
    normalized_query: str,
    extracted_keywords: list[str],
) -> list[str]:
    compact_text = _compact_search_text(normalized_query, extracted_keywords)
    found: list[str] = []
    for keyword in AIR_QUALITY_PRIORITY_KEYWORDS:
        if keyword.replace(".", "") in compact_text:
            found.append(keyword)
    return unique_preserving_order(found)

def _category_from_extraction(extraction: KeywordExtractionResult) -> CategoryId:
    return KOREAN_TO_BACKEND_CATEGORY.get(extraction.category, CategoryId.UNKNOWN)


def _choose_category(
    category_matches: dict[CategoryId, list[str]],
    extraction: KeywordExtractionResult,
    air_quality_keywords: list[str],
) -> tuple[CategoryId, list[str]]:
    if air_quality_keywords:
        matched_keywords = unique_preserving_order(
            category_matches.get(CategoryId.ENVIRONMENT_AIR_QUALITY, []) + air_quality_keywords
        )
        return CategoryId.ENVIRONMENT_AIR_QUALITY, matched_keywords

    if category_matches:
        category = max(
            category_matches,
            key=lambda candidate: (len(category_matches[candidate]), -list(CATEGORY_KEYWORDS).index(candidate)),
        )
        return category, category_matches[category]

    category = _category_from_extraction(extraction)
    if category == CategoryId.UNKNOWN:
        return CategoryId.UNKNOWN, []
    return category, extraction.keywords


def _confidence(keyword_count: int, has_region: bool, has_date: bool) -> float:
    if keyword_count <= 0:
        return 0.0
    score = 0.55 + min(keyword_count, 3) * 0.12
    if has_region:
        score += 0.12
    if has_date:
        score += 0.06
    return round(min(score, 0.95), 2)


def _apply_real_estate_params(
    params: dict[str, str],
    normalized_query: str,
    keywords: list[str],
) -> list[str]:
    searchable_text = f"{normalized_query} {' '.join(keywords).lower()}"
    matched_rules: list[str] = []

    deal_type = next((deal for deal in REAL_ESTATE_DEAL_TYPES if deal in searchable_text), None)
    if deal_type:
        params["deal_type"] = deal_type
        matched_rules.append("real_estate_deal_type_keyword")

        for keyword, property_type in REAL_ESTATE_PROPERTY_TYPES.items():
            if keyword in searchable_text:
                params["property_type"] = property_type
                matched_rules.append("real_estate_property_type_keyword")
                break

        if "실거래가" in searchable_text:
            params["price_type"] = "실거래가"
            matched_rules.append("real_estate_price_type_keyword")

    return matched_rules


def _apply_indicator_params(
    params: dict[str, str],
    normalized_query: str,
    keywords: list[str],
) -> list[str]:
    searchable_text = f"{normalized_query} {' '.join(keywords).lower()}"
    for keyword, indicator in INDICATOR_KEYWORDS.items():
        if keyword in searchable_text:
            params["indicator"] = indicator
            return ["indicator_keyword"]
    return []


def analyze_intent(query: str) -> IntentResult:
    """Analyze a Korean search query with deterministic keyword rules."""
    normalized_query = normalize_query(query)
    extraction = extract_query_keywords(query)
    category_matches = _find_category_keywords(normalized_query)
    regions = _find_regions(normalized_query)
    date_keywords = _find_date_keywords(query)
    air_quality_keywords = _find_air_quality_priority_keywords(normalized_query, extraction.keywords)
    category, matched_category_keywords = _choose_category(category_matches, extraction, air_quality_keywords)

    if category == CategoryId.UNKNOWN:
        return IntentResult(
            category=CategoryId.UNKNOWN,
            keywords=[],
            params={},
            confidence=0.0,
            matched_rules=[],
        )

    params: dict[str, str] = {}
    matched_rules = [f"{category.value}_keyword"]
    if regions:
        params["region"] = regions[0]
        matched_rules.append("region_keyword")
    if date_keywords:
        params["date_keyword"] = date_keywords[0][1]
        params["date"] = date_keywords[0][1]
        matched_rules.append("date_keyword")
    if category == CategoryId.REAL_ESTATE:
        matched_rules.extend(_apply_real_estate_params(params, normalized_query, matched_category_keywords))
    if category == CategoryId.ECONOMY:
        matched_rules.extend(_apply_indicator_params(params, normalized_query, matched_category_keywords))

    keywords = unique_preserving_order(regions + [item[0] for item in date_keywords] + matched_category_keywords)

    return IntentResult(
        category=category,
        keywords=keywords,
        params=params,
        confidence=_confidence(len(matched_category_keywords), bool(regions), bool(date_keywords)),
        matched_rules=matched_rules,
    )

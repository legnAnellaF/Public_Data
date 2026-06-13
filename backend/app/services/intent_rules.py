from backend.app.schemas.common import CategoryId
from backend.app.schemas.intent import IntentResult
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


def _confidence(keyword_count: int, has_region: bool, has_date: bool) -> float:
    if keyword_count <= 0:
        return 0.0
    score = 0.55 + min(keyword_count, 3) * 0.12
    if has_region:
        score += 0.12
    if has_date:
        score += 0.06
    return round(min(score, 0.95), 2)


def analyze_intent(query: str) -> IntentResult:
    """Analyze a Korean search query with deterministic keyword rules."""
    normalized_query = normalize_query(query)
    category_matches = _find_category_keywords(normalized_query)
    regions = _find_regions(normalized_query)
    date_keywords = _find_date_keywords(query)

    if not category_matches:
        return IntentResult(
            category=CategoryId.UNKNOWN,
            keywords=[],
            params={},
            confidence=0.0,
            matched_rules=[],
        )

    category = max(
        category_matches,
        key=lambda candidate: (len(category_matches[candidate]), -list(CATEGORY_KEYWORDS).index(candidate)),
    )
    matched_category_keywords = category_matches[category]

    params: dict[str, str] = {}
    matched_rules = [f"{category.value}_keyword"]
    if regions:
        params["region"] = regions[0]
        matched_rules.append("region_keyword")
    if date_keywords:
        params["date_keyword"] = date_keywords[0][1]
        matched_rules.append("date_keyword")

    keywords = unique_preserving_order(regions + [item[0] for item in date_keywords] + matched_category_keywords)

    return IntentResult(
        category=category,
        keywords=keywords,
        params=params,
        confidence=_confidence(len(matched_category_keywords), bool(regions), bool(date_keywords)),
        matched_rules=matched_rules,
    )

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from urllib import error, request


UPSTAGE_API_URL = "https://api.upstage.ai/v1/solar/chat/completions"
SOLAR_MODEL = "solar-pro"
ALLOWED_CATEGORIES = (
    "부동산",
    "교통",
    "주식",
    "금융",
    "경제",
    "날씨",
    "환경",
    "인구",
    "복지",
    "관광",
    "의료",
    "교육",
    "일반",
)

STOPWORDS = {
    "그리고",
    "그러나",
    "하지만",
    "또는",
    "혹은",
    "및",
    "등",
    "것",
    "수",
    "때",
    "중",
    "안",
    "위해",
    "대한",
    "관련",
    "기반",
    "특정",
    "사용자",
    "입력",
    "문장",
    "프롬포트",
    "프롬프트",
    "정보",
    "내용",
    "방법",
    "기능",
    "결과",
    "화면",
    "파일",
    "저장",
    "있는",
    "없는",
    "하고",
    "하는",
    "한다",
    "된다",
    "싶다",
    "만들고",
    "만드는",
    "만들",
    "있다",
    "으로",
    "에서",
    "에게",
    "부터",
    "까지",
    "보다",
    "처럼",
    "통해",
    "알려줘",
    "알려주세요",
    "보여줘",
    "보여주세요",
    "찾아줘",
    "찾아주세요",
    "현재",
    "지금",
    "알고",
    "싶어",
    "주세요",
    "궁금해",
    "나",
    "내가",
    "저",
    "저는",
    "제가",
    "우리",
    "우리가",
    "내",
    "제",
    "방금",
    "요즘",
    "최근",
    "근데",
    "그런데",
    "그래서",
    "혹시",
    "만약",
    "인데",
    "하는데",
    "중인데",
    "중이야",
    "중입니다",
    "지나가",
    "지나가는",
    "가는중",
    "이동중",
    "타려고",
    "하려고",
    "알고싶어",
    "궁금합니다",
    "보고싶어",
    "확인하고싶어",
    "확인",
    "볼만한",
    "있을까",
    "있을까요",
    "있나요",
    "오전",
    "오후",
    "구매할거야",
    "구매할거",
    "구매",
    "살거야",
    "사려고",
    "얼마인지",
    "얼마",
    "인지",
}

PARTICLE_SUFFIXES = (
    "으로부터",
    "로부터",
    "에서는",
    "에게서",
    "한테서",
    "까지",
    "부터",
    "처럼",
    "보다",
    "으로",
    "으로써",
    "로써",
    "에게",
    "한테",
    "에서",
    "에는",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "과",
    "와",
    "도",
    "만",
    "의",
    "에",
    "로",
    "며",
    "나",
    "랑",
)

ENDING_SUFFIXES = (
    "입니다",
    "합니다",
    "됩니다",
    "하였다",
    "했다",
    "한다",
    "된다",
    "하는",
    "하고",
    "하며",
    "하여",
    "해서",
    "되며",
    "되어",
    "싶다",
    "있다",
    "없는",
    "있는",
    "할",
)

CATEGORY_KEYWORDS = {
    "부동산": {
        "아파트",
        "전세",
        "월세",
        "매매",
        "부동산",
        "주택",
        "빌라",
        "오피스텔",
        "땅값",
        "토지",
        "건축",
        "면적",
        "공시지가",
        "실거래가",
        "강남",
        "부지",
    },
    "교통": {
        "버스",
        "지하철",
        "도로",
        "교통",
        "정류장",
        "노선",
        "혼잡도",
        "주차",
        "사고",
        "자전거",
        "대중교통",
        "승하차",
        "차량",
        "정체",
        "혼잡",
        "통행",
        "대교",
        "다리",
        "터널",
        "ic",
        "나들목",
    },
    "주식": {
        "주식",
        "주가",
        "시세",
        "종가",
        "현재가",
        "상장",
        "증권",
        "코스피",
        "코스닥",
        "sk하이닉스",
        "하이닉스",
        "삼성전자",
        "네이버",
        "카카오",
    },
    "금융": {"환율", "금리", "물가", "금융", "은행", "대출", "예금", "채권", "보험"},
    "경제": {"코스피", "코스닥", "주식", "환율", "금리", "물가", "시장", "지수", "경제", "금융", "증권"},
    "날씨": {"날씨", "기온", "강수량", "미세먼지", "습도", "태풍", "폭염", "한파"},
    "환경": {"대기", "오염", "수질", "폐기물", "탄소", "에너지", "환경"},
    "인구": {"인구", "출생", "사망", "연령", "가구", "세대", "유동인구"},
    "복지": {"복지", "지원금", "보조금", "취약계층", "노인", "장애인", "아동"},
    "관광": {"관광", "관광지", "여행", "축제", "맛집", "숙박", "명소", "문화재", "제주도"},
    "의료": {"병원", "약국", "응급실", "진료", "질병", "건강", "의료"},
    "교육": {"학교", "학원", "교육", "대학", "학생", "도서관", "강의"},
}

ONE_CHAR_MAP = {"가": "가격"}
PUBLIC_DATA_TERMS = set().union(*CATEGORY_KEYWORDS.values())

STOCK_COMPANY_ALIASES = {
    "sk하이닉스": {"sk하이닉스", "하이닉스"},
    "삼성전자": {"삼성전자"},
    "네이버": {"네이버", "naver"},
    "카카오": {"카카오"},
}
STOCK_PRICE_INTENT_TERMS = {"주가", "시세", "가격", "현재가", "얼마", "얼마인지"}

NOISE_PATTERNS = (
    r"데이터가\s*있을까",
    r"데이터가\s*있을까요",
    r"데이터\s*있을까",
    r"데이터\s*있을까요",
    r"지나가는\s*중인데",
    r"지나가는\s*중",
    r"가는\s*중인데",
    r"가는\s*중",
    r"알고\s*싶어",
    r"보고\s*싶어",
    r"확인하고\s*싶어",
    r"구매할\s*거야",
    r"구매할\s*거",
    r"살\s*거야",
    r"사려고",
    r"얼마인지",
)

NOISE_PHRASES = (
    "지나가는중인데",
    "지나가는중",
    "지나가는",
    "지나가",
    "가는중인데",
    "가는중",
    "중인데",
    "중이야",
    "중입니다",
    "알고싶어",
    "궁금합니다",
    "궁금해",
    "알려주세요",
    "알려줘",
    "보고싶어",
    "확인하고싶어",
    "볼만한",
    "타려고",
    "하려고",
    "있을까요",
    "있을까",
    "있나요",
    "지금",
    "현재",
    "방금",
    "요즘",
    "최근",
    "내가",
    "제가",
    "저는",
    "우리가",
    "우리",
    "근데",
    "그런데",
    "그래서",
    "혹시",
    "만약",
    "하는데",
    "인데",
    "오전",
    "오후",
    "구매할거야",
    "구매할거",
    "구매",
    "살거야",
    "사려고",
    "얼마인지",
    "얼마",
    "인지",
    "확인",
)


@dataclass(frozen=True)
class KeywordExtractionResult:
    original_query: str
    cleaned_query: str
    keywords: list[str]
    category: str
    formatted_keywords: str
    source: str


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def remove_duplicates(items: list[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def normalize_token(token: str) -> str:
    token = token.strip().lower()
    token = re.sub(r"^[^0-9a-zA-Z가-힣]+|[^0-9a-zA-Z가-힣]+$", "", token)

    if token in PUBLIC_DATA_TERMS:
        return token

    for suffix in ENDING_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            token = token[: -len(suffix)]
            break

    for suffix in PARTICLE_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            token = token[: -len(suffix)]
            break

    return ONE_CHAR_MAP.get(token, token)


def clean_user_query(text: str) -> str:
    cleaned_text = text
    for pattern in NOISE_PATTERNS:
        cleaned_text = re.sub(pattern, " ", cleaned_text)
    for phrase in NOISE_PHRASES:
        cleaned_text = cleaned_text.replace(phrase, " ")
    cleaned_text = re.sub(r"[,.!?;:()\[\]{}\"'“”‘’]", " ", cleaned_text)
    return re.sub(r"\s+", " ", cleaned_text).strip()


def extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", text)
    candidates: list[str] = []

    for token in tokens:
        normalized = normalize_token(token)
        if len(normalized) < 2:
            continue
        if normalized in STOPWORDS:
            continue
        if normalized.isdigit() and len(normalized) < 2:
            continue
        candidates.append(normalized)

    counts = Counter(candidates)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), candidates.index(item[0])))
    selected = [word for word, _ in ranked[:20]]
    return remove_duplicates([word for word in candidates if word in selected])


def classify_category(keywords: list[str], text: str) -> str:
    searchable_text = " ".join(keywords) + " " + text.lower()
    scores: dict[str, int] = {}

    for category, category_keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in category_keywords if keyword in searchable_text)
        if score:
            scores[category] = score

    if not scores:
        return "일반"
    return sorted(scores.items(), key=lambda item: (-item[1], ALLOWED_CATEGORIES.index(item[0])))[0][0]


def find_stock_company(text: str, keywords: list[str]) -> str | None:
    searchable_text = text.lower() + " " + " ".join(keywords).lower()
    for company, aliases in STOCK_COMPANY_ALIASES.items():
        if any(alias in searchable_text for alias in aliases):
            return company
    return None


def refine_intent_keywords(keywords: list[str], original_text: str, cleaned_text: str) -> list[str]:
    refined = list(keywords)
    searchable_text = original_text.lower() + " " + cleaned_text.lower()

    stock_company = find_stock_company(searchable_text, refined)
    has_stock_context = stock_company or "주식" in refined or "주가" in searchable_text
    has_price_intent = any(term in searchable_text for term in STOCK_PRICE_INTENT_TERMS)

    if stock_company and has_stock_context:
        other_keywords = [
            keyword
            for keyword in refined
            if keyword not in STOCK_COMPANY_ALIASES[stock_company] and keyword not in {"오늘", "주식"}
        ]
        refined = []
        if "오늘" in searchable_text:
            refined.append("오늘")
        refined.append(stock_company)
        refined.append("주식")
        if has_price_intent:
            refined.append(f"{stock_company} 주가")
        refined.extend(other_keywords)

    return remove_duplicates(refined)


def expand_keywords_for_public_data(keywords: list[str], category: str) -> list[str]:
    expanded = list(keywords)
    keyword_set = set(keywords)

    if category == "부동산":
        if {"아파트", "전세"} & keyword_set:
            expanded.append("주택")
        if {"땅값", "부지", "면적", "건축", "공시지가"} & keyword_set:
            expanded.append("토지")
    elif category == "교통":
        if {"교통", "상황", "도로", "차량", "정체", "혼잡", "혼잡도", "사고", "통행", "대교", "다리", "터널"} & keyword_set:
            expanded.append("도로")
        if {"버스", "지하철", "노선", "혼잡도", "승하차"} & keyword_set:
            expanded.append("대중교통")
    elif category in {"주식", "경제"}:
        if {"코스피", "코스닥", "지수", "주식"} & keyword_set:
            expanded.extend(["증권", "금융"])

    if category not in expanded and category != "일반":
        expanded.append(category)

    return remove_duplicates(expanded)


def build_solar_prompt(text: str) -> str:
    return f"""
너는 공공데이터포털 검색 키워드 변환기다.
사용자의 질문에 답하지 마라.
실제 정보를 제공하지 마라.
사용자의 일상 대화 표현, 자기 상황 설명, 감정 표현, 요청 표현은 제거하라.
사용자의 문장을 공공데이터포털(data.go.kr)에서 검색하기 좋은 키워드 목록으로만 변환하라.
카테고리도 키워드 중 하나로 포함하라.
반드시 JSON만 반환하라.

예시:
입력: 오늘 오후에 sk하이닉스 주식을 구매할거야. 지금 하이닉스 주식이 얼마인지 확인하고싶어
반환: {{"keywords": ["오늘", "sk하이닉스", "주식", "sk하이닉스 주가"]}}

반환 형식:
{{"keywords": ["키워드1", "키워드2", "키워드3"]}}

입력 문장:
{text}
""".strip()


def parse_solar_keywords(content: str) -> list[str] | None:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.IGNORECASE | re.DOTALL).strip()

    data = json.loads(content)
    keywords = data.get("keywords", [])
    if not isinstance(keywords, list):
        return None

    cleaned_keywords: list[str] = []
    for keyword in keywords:
        if isinstance(keyword, str):
            normalized = keyword.strip().replace("#", "")
            if normalized:
                cleaned_keywords.append(normalized)

    return remove_duplicates(cleaned_keywords) or None


def analyze_with_solar(text: str, enabled: bool | None = None, api_key: str | None = None) -> list[str] | None:
    solar_enabled = _parse_bool(os.getenv("ENABLE_SOLAR_KEYWORD_EXTRACTOR"), False) if enabled is None else enabled
    if not solar_enabled:
        return None

    safe_api_key = api_key if api_key is not None else os.getenv("UPSTAGE_API_KEY", "")
    if not safe_api_key:
        return None

    payload = {
        "model": SOLAR_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "너는 답변 생성기가 아니라 공공데이터포털 검색 키워드 변환기다. JSON만 반환한다.",
            },
            {"role": "user", "content": build_solar_prompt(text)},
        ],
        "temperature": 0.1,
    }

    req = request.Request(
        UPSTAGE_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {safe_api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode("utf-8"))
        content = response_data["choices"][0]["message"]["content"]
        return parse_solar_keywords(content)
    except (error.URLError, error.HTTPError, KeyError, IndexError, json.JSONDecodeError, TimeoutError):
        return None


def analyze_with_rules(text: str) -> list[str]:
    cleaned_text = clean_user_query(text)
    keywords = extract_keywords(cleaned_text)
    keywords = refine_intent_keywords(keywords, text, cleaned_text)
    if not keywords:
        return []

    category = classify_category(keywords, cleaned_text)
    return expand_keywords_for_public_data(keywords, category)


def format_keywords(keywords: list[str]) -> str:
    return " ".join(f"#{keyword}" for keyword in keywords)


def extract_query_keywords(text: str, enable_solar: bool | None = None) -> KeywordExtractionResult:
    cleaned_text = clean_user_query(text)
    solar_keywords = analyze_with_solar(text, enabled=enable_solar)
    if solar_keywords:
        keywords = solar_keywords
        source = "solar"
    else:
        keywords = analyze_with_rules(text)
        source = "rules"

    category = classify_category(keywords, text) if keywords else "일반"
    return KeywordExtractionResult(
        original_query=text,
        cleaned_query=cleaned_text,
        keywords=keywords,
        category=category,
        formatted_keywords=format_keywords(keywords),
        source=source,
    )

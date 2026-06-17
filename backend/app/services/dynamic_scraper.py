import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.app.services.dynamic_crawler import crawl_public_data_file
from backend.app.services.intelligent_visualizer import engine

STOPWORDS = {
    "그리고", "그러나", "하지만", "또는", "혹은", "및", "등", "것", "수", "때", "중", "안",
    "위해", "대한", "관련", "기반", "특정", "사용자", "입력", "문장", "프롬포트",
    "프롬프트", "정보", "내용", "방법", "기능", "결과", "화면", "파일", "저장",
    "있는", "없는", "하고", "하는", "한다", "된다", "싶다", "만들고", "만드는",
    "만들", "있다", "으로", "에서", "에게", "부터", "까지", "보다", "처럼", "통해",
    "알려줘", "알려주세요", "보여줘", "보여주세요", "찾아줘", "찾아주세요",
}

PARTICLE_SUFFIXES = (
    "으로부터", "로부터", "에서는", "에게서", "한테서", "까지", "부터", "처럼", "보다",
    "으로", "으로써", "로써", "에게", "한테", "에서", "에는", "은", "는", "이", "가",
    "을", "를", "과", "와", "도", "만", "의", "에", "로", "며", "나", "랑",
)

ENDING_SUFFIXES = (
    "입니다", "합니다", "됩니다", "하였다", "했다", "한다", "된다", "하는", "하고",
    "하며", "하여", "해서", "되며", "되어", "싶다", "있다", "없는", "있는",
)

RELATED_KEYWORD_RULES = (
    ({"강남", "아파트"}, ["부동산"]),
    ({"아파트", "시세"}, ["부동산"]),
    ({"땅값", "부지"}, ["부동산"]),
    ({"토지", "면적"}, ["부동산"]),
    ({"코스피", "지수"}, ["주식", "금융"]),
    ({"주식", "시세"}, ["금융"]),
    ({"공공데이터", "시각화"}, ["데이터분석"]),
)


def normalize_token(token: str) -> str:
    token = token.strip().lower()
    token = re.sub(r"^[^0-9a-zA-Z가-힣]+|[^0-9a-zA-Z가-힣]+$", "", token)
    for suffix in ENDING_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            token = token[: -len(suffix)]
            break
    for suffix in PARTICLE_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            token = token[: -len(suffix)]
            break
    return token


def extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", text)
    candidates: list[str] = []
    for token in tokens:
        normalized = normalize_token(token)
        if len(normalized) < 2 or normalized in STOPWORDS or (normalized.isdigit() and len(normalized) < 2):
            continue
        candidates.append(normalized)

    counts = Counter(candidates)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), candidates.index(item[0])))
    selected = [word for word, _ in ranked[:20]]
    ordered_keywords: list[str] = []
    for word in candidates:
        if word in selected and word not in ordered_keywords:
            ordered_keywords.append(word)
    return ordered_keywords


def expand_related_keywords(keywords: list[str]) -> list[str]:
    expanded: list[str] = []
    keyword_set = set(keywords)
    for keyword in keywords:
        if keyword == "오늘":
            now_text = datetime.now().strftime("%Y년%m월%d일_%H시%M분")
            for related in ("현재날짜시간", now_text):
                if related not in expanded:
                    expanded.append(related)
            continue
        if keyword not in expanded:
            expanded.append(keyword)

    for required_keywords, related_keywords in RELATED_KEYWORD_RULES:
        if required_keywords.issubset(keyword_set):
            for related in related_keywords:
                if related not in expanded:
                    expanded.append(related)
    return expanded


def _main_keyword(query: str) -> str:
    keywords = expand_related_keywords(extract_keywords(query))
    return " ".join(keywords[:2]) if keywords else query.strip()


def get_dynamic_widget_data(
    query: str,
    target_link: str | None = None,
    download_dir: str | Path | None = None,
) -> dict[str, Any] | None:
    if not target_link:
        return None

    main_keyword = _main_keyword(query)
    if not main_keyword:
        return None

    file_path = crawl_public_data_file(main_keyword, target_link=target_link, download_dir=download_dir)
    if not file_path:
        return None

    schema = engine.process(file_path)
    if not schema or schema.get("status") != "success":
        return None

    return {
        "title": schema["chart_title"],
        "summary": f"공공데이터포털에서 다운로드한 '{main_keyword}' 데이터 분석 결과입니다.",
        "chart": {
            "type": schema["chart_type"],
            "labels": schema["labels"],
            "datasets": schema["datasets"],
        },
        "source": {
            "name": "공공데이터포털 실시간 다운로드",
            "url": target_link,
            "updated_at": "dynamic",
            "is_mock": False,
        },
        "file_name": Path(file_path).name,
    }

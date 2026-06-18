import os
import re
from collections import Counter
from datetime import datetime
import pandas as pd
from app.services.intelligent_visualizer import engine
from app.services.dynamic_crawler import crawl_public_data_csv

# NLP Constants
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

def normalize_token(token):
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

def extract_keywords(text):
    tokens = re.findall(r"[가-힣A-Za-z0-9]+", text)
    candidates = []
    for token in tokens:
        normalized = normalize_token(token)
        if len(normalized) < 2 or normalized in STOPWORDS or (normalized.isdigit() and len(normalized) < 2):
            continue
        candidates.append(normalized)
    counts = Counter(candidates)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], -len(item[0]), candidates.index(item[0])))
    selected = [word for word, _ in ranked[:20]]
    ordered_keywords = []
    for word in candidates:
        if word in selected and word not in ordered_keywords:
            ordered_keywords.append(word)
    return ordered_keywords

def extract_core_keyword(query):
    """
    [AI Module] Extracts the single most important 'Target Entity' (e.g., country, brand, region, company)
    from the natural language query to focus the visualization exactly on the user's intent.
    """
    target_entities = ["한국", "대만", "중국", "일본", "미국", "홍콩", "K브랜드", "서울", "제주도", "부산", "전기차", "삼성전자", "카카오", "네이버", "현대차"]
    for entity in target_entities:
        if entity in query:
            return entity
            
    keywords = extract_keywords(query)
    generic_kws = {"국내", "주식", "전국", "현황", "비교", "데이터", "통계", "정보", "목록"}
    if keywords:
        for kw in keywords:
            if kw not in generic_kws:
                return kw
        return keywords[0]
    return query

def expand_related_keywords(keywords):
    expanded = []
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

def get_dynamic_widget_data(query: str, target_link: str = None):
    """Main pipeline for the backend."""
    core_keyword = extract_core_keyword(query)
    keywords = expand_related_keywords(extract_keywords(query))
    if not keywords:
        return None
        
    # 1. Use the combined top keywords for a more accurate search (e.g. "전국 도서관" instead of just "전국")
    main_kw = " ".join(keywords[:2])
    
    # 2. 파일 다운로드 (target_link가 있으면 해당 링크로 직행)
    file_path = crawl_public_data_csv(main_kw, target_link)
    
    # Fallback if crawling completely fails
    if not file_path:
        return {
            "status": "error",
            "title": "데이터를 찾을 수 없습니다",
            "summary": f"공공데이터포털에서 '{main_kw}'에 대한 엑셀/CSV 다운로드 파일을 찾지 못했습니다. (OpenAPI 형태만 제공되거나 비공개 자료일 수 있습니다.)",
            "chart": None,
            "source": "시스템 알림"
        }

    # 2. Use the new Intelligent Engine
    schema = engine.process(file_path, query, core_keyword)
    
    if schema and schema["status"] == "success":
        return {
            "title": schema["chart_title"],
            "summary": f"AI 로봇이 공공데이터포털에서 직접 다운로드한 '{main_kw}' 실시간 분석 결과입니다.",
            "chart": {
                "type": schema["chart_type"], # 'bar', 'line', 'pie'
                "labels": schema["labels"],
                "datasets": schema["datasets"]
            },
            "table_data": schema.get("table_data"),
            "views": schema.get("views"),
            "available_years": schema.get("available_years"),
            "available_dimensions": schema.get("available_dimensions"),
            "core_keyword": schema.get("core_keyword"),
            "source": "공공데이터포털 실시간 다운로드 크롤링",
            "file_name": os.path.basename(file_path)
        }
        
    return None

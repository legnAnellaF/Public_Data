"""Deprecated compatibility wrapper for Hyeonsu's keyword parser.

The backend API uses `backend.app.services.intent_rules.analyze_intent`, which
returns the stable Pydantic IntentResult contract. This module remains only for
older scripts that imported `backend.keyword_parsing` directly. The extraction
helpers are implemented in `backend.app.services.keyword_extractor`.
"""

from backend.app.services.keyword_extractor import (
    ALLOWED_CATEGORIES,
    CATEGORY_KEYWORDS,
    ENDING_SUFFIXES,
    NOISE_PATTERNS,
    NOISE_PHRASES,
    ONE_CHAR_MAP,
    PARTICLE_SUFFIXES,
    PUBLIC_DATA_TERMS,
    SOLAR_MODEL,
    STOCK_COMPANY_ALIASES,
    STOCK_PRICE_INTENT_TERMS,
    STOPWORDS,
    UPSTAGE_API_URL,
    KeywordExtractionResult,
    analyze_with_rules,
    analyze_with_solar,
    build_solar_prompt,
    classify_category,
    clean_user_query,
    expand_keywords_for_public_data,
    extract_keywords,
    extract_query_keywords,
    find_stock_company,
    format_keywords,
    normalize_token,
    parse_solar_keywords,
    refine_intent_keywords,
    remove_duplicates,
)


def analyze_query(text: str) -> list[str]:
    return extract_query_keywords(text).keywords


def analyze_intent(text: str) -> dict[str, object]:
    result = extract_query_keywords(text)
    return {
        "original_query": result.original_query,
        "keywords": result.keywords,
        "category": result.category,
        "formatted_keywords": result.formatted_keywords,
    }


if __name__ == "__main__":
    samples = [
        "오늘 오후에 sk하이닉스 주식이 얼마인지 확인하고싶어",
        "지금 내가 마포대교 지나가는 중인데 현재 마포대교 인근의 교통 상황을 알고싶어",
        "강남 아파트 전세 가격 알고 싶어",
    ]
    for sample in samples:
        print(sample)
        print(analyze_intent(sample))

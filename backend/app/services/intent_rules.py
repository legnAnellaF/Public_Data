def analyze_intent(query: str):
    """
    Analyzes the user's search query to determine the category and keywords.
    """
    CATEGORY_KEYWORDS = {
        "real_estate": ["아파트", "전세", "월세", "매매", "실거래가"],
        "traffic": ["버스", "지하철", "교통", "혼잡", "도로"],
        "weather": ["날씨", "기온", "강수량", "미세먼지"],
        "economy": ["물가", "유가", "환율", "소비자물가"],
    }
    
    intent = "unknown"
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in query for keyword in keywords):
            intent = category
            break
            
    return {
        "intent": intent,
        "keywords": [k for k in CATEGORY_KEYWORDS.get(intent, []) if k in query],
        "params": {},
        "confidence": 0.9 if intent != "unknown" else 0.1
    }

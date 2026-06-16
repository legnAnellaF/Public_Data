def transform_to_widget(raw_data: dict, intent_result: dict) -> dict:
    """
    Transforms the raw API response into the agreed Widget JSON schema.
    """
    intent = intent_result.get("intent")
    
    if intent == "weather":
        try:
            items = raw_data.get("response", {}).get("body", {}).get("items", [])
            if not items:
                raise ValueError("No items in API response")
            
            labels = []
            data = []
            
            for item in items[:5]:
                labels.append(item.get("stationName", "Unknown"))
                # Handle cases where pm10Value is '-' or missing
                pm10 = item.get("pm10Value")
                try:
                    val = float(pm10)
                except (ValueError, TypeError):
                    val = 0
                data.append(val)
                
            return {
                "title": "서울 미세먼지(PM10) 실시간",
                "summary": "현재 서울 주요 측정소의 미세먼지 농도입니다.",
                "chart": {
                    "type": "bar",
                    "labels": labels,
                    "datasets": [
                        {
                            "label": "PM10 농도",
                            "data": data,
                            "unit": "㎍/㎥"
                        }
                    ]
                },
                "source": "한국환경공단 에어코리아"
            }
        except Exception as e:
            print(f"Error transforming widget data: {e}")
            raise e
            
    return {}


import os
import requests
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

def fetch_public_data(intent_result: dict):
    """
    Calls data.go.kr API based on intent.
    Currently implements the 'weather' (Fine Dust) API.
    """
    intent = intent_result.get("intent")
    
    if intent == "weather":
        # 한국환경공단_에어코리아_대기오염정보 - 시도별 실시간 측정정보 조회
        url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
        api_key = os.getenv("PUBLIC_DATA_API_KEY", "your_api_key_here")
        
        # If API key is not set, throw error to trigger fallback
        if not api_key or api_key == "your_api_key_here":
            raise ValueError("API Key is missing or not configured.")

        # Decode the key in case the user pasted the encoded version
        decoded_key = urllib.parse.unquote(api_key)

        params = {
            "serviceKey": decoded_key,
            "returnType": "json",
            "numOfRows": "5",
            "pageNo": "1",
            "sidoName": "서울",
            "ver": "1.0"
        }
        
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise RuntimeError(f"API Request failed: {e}")
            
    # For other intents, we just return None to trigger fallback in main.py
    return None


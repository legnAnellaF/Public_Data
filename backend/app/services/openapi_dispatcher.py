import os
import requests
import urllib.parse
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

def fetch_air_quality(api_key):
    """
    한국환경공단_에어코리아_대기오염정보 OpenAPI 호출 (시도별 실시간 측정정보)
    상용화 규격: 실시간 JSON 응답 파싱 후 Pandas DataFrame 반환
    """
    url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
    decoded_key = urllib.parse.unquote(api_key)
    
    params = {
        "serviceKey": decoded_key,
        "returnType": "json",
        "numOfRows": "30",
        "pageNo": "1",
        "sidoName": "서울",
        "ver": "1.0"
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    items = data.get("response", {}).get("body", {}).get("items", [])
    if not items:
        return None
        
    df = pd.DataFrame(items)
    df = df[['stationName', 'pm10Value', 'pm25Value', 'o3Value']]
    df.rename(columns={
        'stationName': '측정소명',
        'pm10Value': '미세먼지(PM10)',
        'pm25Value': '초미세먼지(PM2.5)',
        'o3Value': '오존농도(ppm)'
    }, inplace=True)
    
    for col in ['미세먼지(PM10)', '초미세먼지(PM2.5)', '오존농도(ppm)']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    df.dropna(inplace=True)
    return df

def fetch_real_estate_mock():
    # 국토부 아파트 실거래가 API는 별도 심사 및 지역코드 매핑이 필요하므로 현재는 예시 데이터로 대체
    df = pd.DataFrame({
        "자치구명": ["강남구", "서초구", "송파구", "마포구", "용산구", "성동구", "노원구"],
        "평균매매가(억)": [22.5, 20.1, 18.3, 14.2, 19.5, 15.8, 9.2],
        "평균전세가(억)": [12.1, 11.5, 10.2, 8.5, 10.0, 9.1, 5.5]
    })
    return df

def dispatch_openapi(keyword_list):
    """
    키워드에 맞는 정부 공식 OpenAPI로 라우팅하는 분배기
    """
    api_key = os.getenv("PUBLIC_DATA_API_KEY", "")
    keywords_str = " ".join(keyword_list)
    
    # 1. 미세먼지 / 날씨 / 공기 API 라우팅
    if any(k in keywords_str for k in ["미세먼지", "날씨", "대기", "환경"]):
        if not api_key or "여기에" in api_key:
            raise ValueError("API_KEY_MISSING")
        return fetch_air_quality(api_key)
        
    # 2. 부동산 / 아파트 라우팅
    elif any(k in keywords_str for k in ["아파트", "부동산", "집값", "전세", "매매"]):
        return fetch_real_estate_mock()
        
    else:
        # Default fallback to Air Quality if it's a generic request but API key exists
        if not api_key or "여기에" in api_key:
            raise ValueError("API_KEY_MISSING")
        return fetch_air_quality(api_key)

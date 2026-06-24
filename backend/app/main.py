from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import urllib.parse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import requests
from bs4 import BeautifulSoup
import json
import os

from app.services.intent_rules import analyze_intent
from app.services.public_api_client import fetch_public_data
from app.services.widget_transformer import transform_to_widget
from app.services.excel_processor import process_excel
from app.services.dynamic_scraper import get_dynamic_widget_data

app = FastAPI(title="Public Data Widget API", version="1.0.0")

# Enable CORS for the browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtensionRequest(BaseModel):
    query: str
    page_url: str
    source: str
    target_link: Optional[str] = None

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/api/search")
def search_datasets(request: ExtensionRequest):
    """Searches data.go.kr for top 5 datasets and returns their metadata."""
    from app.services.dynamic_scraper import extract_keywords
    
    # Extract keywords
    keywords = extract_keywords(request.query)
    main_kw = " ".join(keywords[:2]) if keywords else request.query
    
    q = urllib.parse.quote(main_kw)
    url = f"https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=FILE&keyword={q}&detailKeyword={q}"
    
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        results = soup.select('.result-list li')
        
        # [Smart Fallback] 검색 결과가 없을 경우 단일 키워드로 재검색
        if not results and keywords:
            fallback_kws = [kw for kw in keywords if kw in ["상권", "창업", "카페", "상점", "영업", "매출", "인구", "부동산", "금융", "아파트", "주택"]]
            if not fallback_kws:
                fallback_kws = [keywords[0]]
                if len(keywords) > 1:
                    fallback_kws.append(keywords[1])
            for fb_kw in fallback_kws:
                print(f"[Search Fallback] '{main_kw}' 검색 결과 없음. '{fb_kw}'(으)로 재검색...")
                q = urllib.parse.quote(fb_kw)
                url = f"https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=FILE&keyword={q}&detailKeyword={q}"
                resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                soup = BeautifulSoup(resp.text, 'html.parser')
                results = soup.select('.result-list li')
                if results:
                    main_kw = fb_kw
                    break
        
        items = []
        for li in results[:5]:
            title_el = li.select_one('dt a .title')
            if not title_el:
                title_el = li.select_one('dt a')
                
            title = title_el.text.strip() if title_el else 'Unknown Title'
            title = title.replace('\n', ' ').replace('\r', '').strip()
            
            provider_el = li.select_one('.info-data p')
            provider = provider_el.text.strip() if provider_el else 'Unknown Provider'
            
            link_el = li.select_one('dt a')
            link = link_el.get('href') if link_el else ''
            if link and not link.startswith('http'):
                link = "https://www.data.go.kr" + link
                
            spans = li.select('.info-data span')
            views = "0"
            downloads = "0"
            mod_date = "N/A"
            
            if len(spans) >= 8:
                mod_date = spans[3].text.strip()
                views = spans[5].text.strip()
                downloads = spans[7].text.strip()
                
            # Create a factual reason based on actual metadata
            reason = f"📊 [사실 정보] 조회수 {views}회, 다운로드 {downloads}건을 기록한 신뢰도 높은 공공데이터입니다. (수정일: {mod_date})"
            
            items.append({
                "title": title,
                "provider": provider,
                "link": link,
                "reason": reason
            })
            
        return {"status": "ok", "results": items}
    except Exception as e:
        print(f"Search API Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/widget")
def get_widget(request: ExtensionRequest):
    query = request.query
    
    if request.target_link == "SMART_JOIN":
        from app.services.dynamic_crawler import crawl_public_data_top5_csv
        from app.services.smart_join_engine import join_engine
        from app.services.dynamic_scraper import extract_core_keyword
        
        file_paths = crawl_public_data_top5_csv(query)
        if not file_paths:
            return {"status": "error", "message": "No data files found for smart join."}
            
        merged_file = join_engine.join_datasets(file_paths, query)
        if not merged_file:
            return {"status": "error", "message": "Failed to intelligently merge datasets."}
            
        core_keyword = extract_core_keyword(query)
        from app.services.intelligent_visualizer import engine
        schema = engine.process(merged_file, query, core_keyword)
        if not schema:
            return {"status": "error", "message": "Failed to visualize merged data."}
            
        # Update summary for Smart Join
        schema["summary"] = f"✨ [AI Smart Join] 5개의 공공데이터를 융합 분석한 결과입니다.\n" + schema.get("summary", "")
        return {"status": "ok", "widget": schema}
        
    # Default single file logic
    try:
        dynamic_data = get_dynamic_widget_data(query, request.target_link)
        if dynamic_data:
            return {
                "status": "ok",
                "widget": dynamic_data
            }
    except Exception as e:
        print(f"Backend error: {e}")

    # If the file was downloaded but the AI Engine couldn't find numerical data:
    return {
        "status": "ok",
        "widget": {
            "title": "데이터 분석 실패",
            "summary": "공공데이터포털에서 파일을 성공적으로 다운로드했으나, 차트로 그릴 수 있는 통계(수치) 데이터가 엑셀에 포함되어 있지 않습니다.",
            "chart": None,
            "source": "시스템 알림"
        }
    }

@app.get("/api/download")
def download_file(file: str):
    """Serves the downloaded public data file to the user."""
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "public_data_downloads")
    file_path = os.path.join(desktop_path, file)
    if os.path.exists(file_path):
        encoded_name = urllib.parse.quote(file)
        headers = {'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_name}"}
        return FileResponse(file_path, headers=headers)
    return {"error": "File not found"}

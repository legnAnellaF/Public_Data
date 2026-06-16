import os
import glob
from playwright.sync_api import sync_playwright

def crawl_public_data_csv(keyword: str, target_link: str = None):
    """
    Playwright를 이용한 무적의 공공데이터 로봇 크롤러.
    target_link가 주어지면 해당 상세 페이지로 직행하여 다운로드합니다.
    다운로드된 CSV 파일의 절대 경로를 반환합니다.
    """
    # 안전한 다운로드 폴더 생성
    download_dir = os.path.join(os.path.expanduser("~"), "Desktop", "public_data_downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    # 이전 찌꺼기 파일 정리 (동일 키워드)
    for f in glob.glob(os.path.join(download_dir, "*.csv")):
        try:
            os.remove(f)
        except:
            pass

    print(f"[Crawler] '{keyword}' 키워드로 공공데이터 탐색을 시작합니다...")
    
    try:
        with sync_playwright() as p:
            # 헤드리스 모드로 실행 (화면 띄우지 않음)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            
            if target_link:
                print(f"[Crawler] 지정된 데이터셋으로 직행합니다: {target_link}")
                page.goto(target_link, timeout=15000)
                page.wait_for_load_state("networkidle")
            else:
                # 1. 파일데이터(dType=FILE)만 검색하는 URL로 바로 이동 (sort=reqCo 활용건수/다운로드 많은 순으로 정렬하여 양질의 데이터 확보)
                search_url = f"https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=FILE&keyword={keyword}&detailKeyword={keyword}&sort=reqCo"
                page.goto(search_url, timeout=15000)
                
                # 2. 검색 결과 리스트 렌더링 대기
                page.wait_for_selector(".result-list", timeout=10000)
                
                # 3. 첫 번째 검색 결과 클릭
                first_result = page.locator(".result-list li dl dt a").first
                if not first_result.is_visible():
                    print("[Crawler] 검색 결과가 없습니다.")
                    browser.close()
                    return None
                
                print(f"[Crawler] 데이터를 찾았습니다. 상세 페이지로 진입합니다.")
                first_result.click()
                page.wait_for_load_state("networkidle")
            
            # 4. 다운로드 버튼 찾기
            # 공공데이터포털의 다양한 다운로드 버튼 형태 모두 대응
            target_btn = page.locator("a:has-text('다운로드'), a.button:has-text('다운로드'), a[href*='fileDownload'], a:has-text('CSV')").first
                
            if not target_btn.is_visible():
                print("[Crawler] CSV 다운로드 버튼을 찾을 수 없습니다.")
                browser.close()
                return None
                
            print(f"[Crawler] 다운로드 버튼 클릭 및 파일 수신 대기...")
            # 5. 다운로드 이벤트 대기 및 파일 저장
            with page.expect_download(timeout=15000) as download_info:
                target_btn.click()
                
            download = download_info.value
            suggested_filename = download.suggested_filename
            final_path = os.path.join(download_dir, suggested_filename)
            
            download.save_as(final_path)
            print(f"[Crawler] 다운로드 완료: {final_path}")
            
            browser.close()
            return final_path
            
    except Exception as e:
        print(f"[Crawler] 크롤링 중 오류 발생: {e}")
        return None

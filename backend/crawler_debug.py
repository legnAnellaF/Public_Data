from playwright.sync_api import sync_playwright

keyword = '도서관'
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    url = f"https://www.data.go.kr/tcs/dss/selectDataSetList.do?dType=FILE&keyword={keyword}&detailKeyword={keyword}"
    page.goto(url, wait_until='networkidle')
    
    first_result = page.locator(".result-list li dl dt a").first
    if first_result.is_visible():
        first_result.click()
        page.wait_for_load_state("networkidle")
        
        # Dump all anchor tags on the detail page
        links = page.eval_on_selector_all('a', 'nodes => nodes.map(n => n.innerText + "|" + n.className + "|" + n.href)')
        for l in links:
            if '다운로드' in l or 'csv' in l.lower() or 'download' in l.lower() or 'btn' in l.lower():
                print(l)
    browser.close()

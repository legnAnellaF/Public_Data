# Extension Integration

`extension/`은 Chrome Extension MV3 구조를 사용합니다. Bumsoo-Shin 브랜치의 초기 `content.js`와 `mainfest.json` 방향을 가져오되, 오타가 있는 `mainfest.json` 대신 표준 `manifest.json`을 만들고 content script를 backend contract에 맞게 정리했습니다.

## Files

- `manifest.json`: Google/Naver/Daum 검색 결과 페이지에 `content.js`를 주입합니다.
- `content.js`: 검색어 감지, `/api/widget` 호출, 우측 하단 overlay 렌더링을 담당합니다.
- `Data_Dashboard.html`: standalone prototype입니다. 최종 content script UI가 아닙니다.
- `README.md`: 로컬 실행과 수동 테스트 절차를 설명합니다.

## Overlay Behavior

`content.js`는 다음 흐름으로 동작합니다.

1. URL parameter에서 검색어를 찾습니다. Google/Daum은 `q`, Naver는 `query`를 우선 사용합니다.
2. URL에서 찾지 못하면 검색 input을 fallback으로 확인합니다.
3. `http://127.0.0.1:8000/api/widget`에 `query`, `page_url`, `source`를 POST합니다.
4. 응답이 `ok`이면 title, summary, badge, cards, text bars, table, source를 표시합니다.
5. `unsupported`, `error`, fetch failure, malformed response는 별도 message overlay로 표시합니다.
6. 새 overlay를 그리기 전 `public-data-widget-overlay` ID의 기존 overlay를 제거합니다.

Chart.js는 content script에 넣지 않았습니다. Chrome Extension CSP와 CDN 문제를 피하기 위해 현재 overlay는 lightweight DOM rendering만 사용합니다.

## Manual Test Queries

- 서울 미세먼지
- 강남 아파트 실거래가
- 마포대교 교통 상황
- 오늘 서울 기온
- sk하이닉스 주가
- 아이돌 콘서트 예매

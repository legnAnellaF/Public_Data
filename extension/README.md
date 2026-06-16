# Public Data Search Widget Extension

이 폴더는 Chrome Extension MV3 기반의 검색 페이지 오버레이와 독립 실행형 대시보드 prototype을 함께 보관합니다. `content.js`가 실제 검색 페이지에서 동작하는 최소 extension UI이고, `Data_Dashboard.html`은 Chart.js와 파일 업로드 실험을 위한 standalone prototype입니다.

## 백엔드 실행

프로젝트 루트에서 FastAPI backend를 실행합니다.

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

기본 extension API 주소는 `http://127.0.0.1:8000`입니다. 로컬 prototype을 브라우저에서 열려면 CORS 허용 origin에 `http://127.0.0.1:5500`과 `http://localhost:5500`이 포함되어야 합니다. 예시는 `../.env.example` 또는 `../backend/.env.example`을 참고하세요.

## Chrome Extension 로드

1. Chrome에서 `chrome://extensions`를 엽니다.
2. Developer Mode를 켭니다.
3. Load unpacked를 눌러 이 `extension/` 폴더를 선택합니다.
4. 백엔드가 실행 중인 상태에서 검색 페이지를 엽니다.

지원 검색 페이지:

- `https://www.google.com/search?q=서울+미세먼지`
- `https://search.naver.com/search.naver?query=서울%20미세먼지`
- `https://search.daum.net/search?q=서울+미세먼지`

`content.js`는 URL 또는 검색 input에서 검색어를 감지하고 `/api/widget`을 호출한 뒤, 우측 하단에 lightweight DOM overlay를 렌더링합니다. Chart.js는 content script에 넣지 않았습니다.

## Standalone Dashboard Prototype

`Data_Dashboard.html`은 최종 extension overlay가 아니라 독립 실행형 prototype입니다. 파일 업로드, SheetJS parsing, Chart.js 시각화, backend `/api/widget` 테스트를 위한 페이지로 유지합니다.

실행 예시:

```bash
cd extension
python -m http.server 5500
```

브라우저에서 엽니다.

```text
http://127.0.0.1:5500/Data_Dashboard.html
```

## 지원 테스트 검색어

- 서울 미세먼지
- 강남 아파트 실거래가
- 서울 교통량
- 오늘 기온
- 소비자물가
- 아이돌 콘서트 예매

## 알려진 제한

- `Data_Dashboard.html`은 prototype이며 최종 extension overlay가 아닙니다.
- Chrome Extension content script에서는 CDN 기반 Chart.js가 CSP 문제를 만들 수 있습니다.
- 현재 overlay는 Chart.js 대신 카드, 표, 텍스트 bar로 요약 정보를 보여줍니다.
- 실제 공공 API 연동 전에는 backend mock mode로 extension end-to-end 동작을 먼저 확인해야 합니다.

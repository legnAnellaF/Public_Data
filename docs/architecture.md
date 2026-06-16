# Architecture Document

## 시스템 흐름
1. **사용자 검색**: 구글/네이버에서 키워드 검색
2. **검색어 추출**: `extension/content.js`가 URL에서 파라미터 파싱
3. **서버 통신**: 백엔드 `/api/widget`에 검색어 전송
4. **Intent 분석**: `backend/app/services/intent_rules.py`에서 검색어 카테고리화
5. **JSON 변환**: Mock/공공데이터 결과를 `contracts/` 형식에 맞춰 JSON으로 변환
6. **오버레이 출력**: 브라우저 화면 우측 하단에 위젯을 랜더링 (Zero-UI Glassmorphism)

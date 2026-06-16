# Public_Data
공공데이터 공모전

검색 연동형 공공데이터 위젯 프로젝트의 뼈대 코드입니다.

## 폴더 구조
- `extension/`: 브라우저 우측 하단에 표시되는 오버레이 위젯 소스코드 (크롬 익스텐션 형태)
- `backend/`: 위젯에 데이터를 공급하는 FastAPI 백엔드
- `contracts/`: 프론트와 백엔드 간 통신을 위한 JSON 스키마 명세
- `docs/`: 기획 및 설계 문서

## 실행 방법

### 1. 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
서버가 `http://localhost:8000`에 실행됩니다.

### 2. 익스텐션 설치
1. 크롬에서 `chrome://extensions` 접속
2. "개발자 모드" 켜기
3. "압축해제된 확장 프로그램을 로드합니다" 클릭
4. 현재 프로젝트의 `extension/` 폴더 선택

### 3. 테스트
구글 또는 네이버에서 `아파트 전세` 혹은 `미세먼지`를 검색해 보세요. 우측 하단에 위젯이 슬라이드업 되는 것을 확인할 수 있습니다.

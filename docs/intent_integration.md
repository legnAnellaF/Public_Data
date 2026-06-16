# Intent Integration

Backend intent 분석은 `backend.app.services.intent_rules.analyze_intent()`가 단일 public entrypoint입니다. `/api/intent`와 `/api/widget`은 이 함수가 반환하는 `IntentResult` contract를 그대로 사용합니다.

## Keyword Extractor

`backend/app/services/keyword_extractor.py`는 Hyeonsu의 한국어 keyword parsing logic을 service layer로 옮긴 파일입니다. 포함된 기능은 다음과 같습니다.

- 검색어 정제
- stopword 제거
- 조사/어미 제거
- 키워드 추출
- 한국어 카테고리 분류
- 주식 키워드 보정
- 공공데이터 검색용 키워드 확장
- 선택적 Upstage Solar keyword extraction

Solar는 기본 OFF입니다. `ENABLE_SOLAR_KEYWORD_EXTRACTOR=true`이고 `UPSTAGE_API_KEY`가 있을 때만 호출합니다. 테스트와 기본 개발 환경은 외부 네트워크를 요구하지 않습니다.

## Category Mapping

한국어 카테고리는 backend 표준 카테고리로 변환됩니다.

| Korean | Backend |
| --- | --- |
| 부동산 | real_estate |
| 교통 | traffic |
| 날씨 | weather |
| 환경 | environment_air_quality |
| 경제, 금융, 주식 | economy |
| 인구, 복지, 관광, 의료, 교육, 일반 | unknown |

`미세먼지`, `초미세먼지`, `PM10`, `PM2.5`, `대기질`, `대기오염`, `대기`가 원문 또는 추출 keyword에 있으면 `environment_air_quality`를 우선 적용합니다.

## Params

기존 지역/date 추출은 유지하면서 가능한 경우 다음 params를 보강합니다.

- `region`: 서울, 부산, 강남구, 마포대교 등
- `property_type`: 아파트, 주택, 오피스텔, 빌라, 토지
- `deal_type`: 전세, 월세, 매매
- `indicator`: 소비자물가, 환율, 금리, 주가

응답 구조는 기존 `category`, `keywords`, `params`, `confidence`, `matched_rules`를 유지합니다.

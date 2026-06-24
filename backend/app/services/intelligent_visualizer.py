import json
import os
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# [환경 설정] 윈도우 한글 깨짐 방지
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

class IntelligentVisualizerEngine:
    """데이터 구조를 스스로 분석하여 최적의 시각화 전략을 세우고 실행하는 엔지니어링 엔진"""

    def __init__(self):
        # 공공데이터에서 시각화 가치가 높은 Y축(수치형) 핵심 키워드 가중치 사전
        self.y_priority_keywords = [
            "합계",
            "금액",
            "평가액",
            "주식수",
            "수치",
            "소계",
            "값",
            "통행량",
            "이용자",
            "건수",
            "농도",
            "인구",
        ]

    def _load_file(self, file_path):
        """[1단계] 범용 공공데이터 정규화 엔진을 통한 데이터 로드 및 정제"""
        from app.services.excel_processor import normalize_excel
        return normalize_excel(file_path)

    def _infer_data_types(self, df):
        """[2단계] 가로/세로 항목의 실제 데이터 형태 추론 엔진"""
        temporal_cols = []
        numerical_cols = []
        categorical_cols = []
        
        # 제외할 키워드 (절대 수치형이 될 수 없는 컬럼들)
        exclude_num_keywords = ["주소", "전화", "번호", "코드", "id", "명칭", "이름", "성명", "위도", "경도", "우편", "지번"]
        temporal_keywords = ["날짜", "일자", "계약일", "년월", "일시", "기간"]

        for col in df.columns:
            valid_series = df[col].dropna()
            if valid_series.empty:
                continue
                
            col_str = str(col).lower()
            
            # 1. 시계열(날짜/시간) 데이터 우선 판별
            is_temporal = any(kw in col_str for kw in temporal_keywords)
            if not is_temporal and (valid_series.astype(str).str.contains(r"^\d{4}-\d{2}-\d{2}$|^\d{8}$").sum() / len(valid_series) > 0.5):
                is_temporal = True
                
            if is_temporal:
                temporal_cols.append(col)
                continue
                
            # 2. 명확한 범주형(주소, 번호 등) 배제
            if any(kw in col_str for kw in exclude_num_keywords):
                categorical_cols.append(col)
                continue

            # 3. 수치형 데이터 판별 (단위 문자만 조심스럽게 제거)
            sample_str = valid_series.astype(str).str.replace(r"[,\s원건명%개만천억(추정)이상미만]", "", regex=True)
            num_conv = pd.to_numeric(sample_str, errors="coerce")

            # 수치 변환 성공률이 70% 이상이거나 컬럼명에 매출, 금액, 비용, 인구, 점포수 등이 포함되어 있으면 수치형으로 확정
            force_numeric_kws = ["매출", "금액", "비용", "인구", "점포", "단가", "수익", "수입", "수출", "합계", "통행량"]
            if num_conv.notna().sum() / len(valid_series) > 0.7 or any(kw in col_str for kw in force_numeric_kws):
                df[col] = num_conv.fillna(0)  # 원본 데이터 가공 후 덮어쓰기
                numerical_cols.append(col)
            else:
                categorical_cols.append(col)

        return temporal_cols, numerical_cols, categorical_cols

    def _select_optimal_axes(self, df, temporal, numerical, categorical, query=""):
        """[3단계] 초보 창업자 맞춤형 최적의 X축과 다중 Y축 자동 선정 알고리즘 (LLM & 시맨틱 가중치 엔진)"""
        final_x = None
        final_y_list = []

        # Y축(수치형) 선정: 무의미한 번호 컬럼 제외
        invalid_y = ["번호", "순번", "id", "순위", "no", "연번", "연도"]
        valid_numerical = [col for col in numerical if not any(inv in col.lower() for inv in invalid_y)]
        
        # 초보 창업자 특화 주요 지표 가중치 사전 (Startup Domain Keyword Rules)
        startup_y_keywords = {
            "상권": ["점포", "유동인구", "매장", "상가", "영업", "폐업", "밀도", "인구"],
            "매출": ["매출", "단가", "수익", "이익", "판매", "금액", "결제"],
            "수출입": ["관세", "수출", "수입", "무역", "달러", "중량", "환율"],
            "인구": ["인구", "가구", "세대", "연령", "거주", "유동"],
            "경쟁": ["경쟁", "업체수", "점포수", "밀집도", "유사"],
            "비용": ["임대료", "권리금", "보증금", "배달비", "관리비", "비용", "단가"],
            "창업": ["매출", "유동인구", "점포", "창업", "폐업", "금액", "합계"]
        }

        # 0. 와이드 포맷 시계열 감지 로직
        time_keywords = ["년", "월", "일", "분기", "현황", "상반기", "하반기"]
        time_cols = [col for col in valid_numerical if any(tk in str(col) for tk in time_keywords)]
                
        if len(time_cols) >= 2:
            final_y_list = time_cols
        else:
            # 1. 쿼리 기반 창업 도메인 지능형 매칭 (Dynamic Semantic Startup Column Matching)
            if query:
                import re
                query_words = re.findall(r'[가-힣A-Za-z0-9]+', query)
                
                # 창업 키워드 매칭 시도
                for q_word in query_words:
                    for domain, kws in startup_y_keywords.items():
                        if domain in q_word or q_word in domain or any(kw in q_word for kw in kws):
                            for col in valid_numerical:
                                col_str = str(col)
                                if any(kw in col_str for kw in kws) and col not in final_y_list:
                                    final_y_list.append(col)
                            if final_y_list:
                                break
                    if final_y_list:
                        break

                # 일반 쿼리 단어 매칭
                if not final_y_list:
                    for col in valid_numerical:
                        col_str = str(col)
                        for w in query_words:
                            if len(w) >= 2 and (w in col_str or col_str in w):
                                if col not in final_y_list:
                                    final_y_list.append(col)
                                if len(final_y_list) >= 1:
                                    break
                        if len(final_y_list) >= 1:
                            break
            
            # 2. 매칭되는 항목이 없을 경우 기존 우선순위 기반 매칭 (Fallback)
            if not final_y_list:
                for kw in self.y_priority_keywords:
                    for col in valid_numerical:
                        if kw in col and col not in final_y_list:
                            final_y_list.append(col)
                        if len(final_y_list) >= 1:
                            break
                    if len(final_y_list) >= 1:
                        break
                        
                if not final_y_list and valid_numerical:
                    final_y_list.append(valid_numerical[0])

        # X축 선정: 무의미한 번호 컬럼 제외
        valid_categorical = [col for col in categorical if not any(inv in col.lower() for inv in invalid_y)]
        
        # 1. 상권/지역/업종 등 핵심 그룹화(X축) 키워드 우선 매칭
        x_priority_keywords = ["지역", "시도", "시군구", "상권", "업종", "구분", "명칭", "이름", "지점", "장소", "행정동", "자치구", "시도명", "시군구명"]
        for kw in x_priority_keywords:
            for col in valid_categorical:
                if kw in str(col) and 2 <= df[col].nunique() <= 100:
                    final_x = col
                    break
            if final_x:
                break

        # 2. 쿼리 기반 지능형 X축 매칭 ('별' 등 접미사 제거 후 매칭)
        if not final_x and query and valid_categorical:
            import re
            query_words = re.findall(r'[가-힣A-Za-z0-9]+', query)
            clean_query_words = [w.replace('별', '') for w in query_words]
            for col in valid_categorical:
                col_str = str(col)
                for w in clean_query_words:
                    if len(w) >= 2 and (w in col_str or col_str in w):
                        final_x = col
                        break
                if final_x:
                    break

        # 3. 매칭 안 될 경우 기본 로직 (Fallback)
        if not final_x:
            if temporal:
                final_x = temporal[0]
            elif valid_categorical:
                for col in valid_categorical:
                    if 2 <= df[col].nunique() <= 100:
                        final_x = col
                        break
                if not final_x:
                    final_x = valid_categorical[0]
            elif df.columns.size > 0:
                final_x = df.columns[0]

        return final_x, final_y_list

    def _generate_startup_precautions(self, df, x, y_list, query):
        """
        [AI 창업 주의사항 및 체크리스트 생성 엔진]
        선택된 데이터의 구조와 지표 흐름(하락 추세, 특정 지역/항목 편중, 이상치 등)을 분석하여
        초보 창업자에게 꼭 필요한 실질적 주의사항과 인사이트를 도출합니다.
        """
        import os
        import requests
        
        precautions = []
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        # 샘플 데이터 구성 (LLM 전달용)
        sample_records = ""
        if x and y_list and not df.empty:
            sample_df = df[[x] + y_list].head(10).to_dict(orient='records')
            sample_records = str(sample_df)

        if gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={gemini_key}"
                prompt = f"당신은 초보 창업자 컨설턴트입니다. 다음 공공데이터 샘플과 창업 아이디어('{query}')를 분석하여 초보 창업자가 주의해야 할 점, 체크리스트, 리스크 요인을 3가지로 요약해주세요. 데이터 샘플: {sample_records}"
                payload = {"contents": [{"parts": [{"text": prompt}]}]}
                resp = requests.post(url, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data['candidates'][0]['content']['parts'][0]['text']
                    precautions = [line.strip() for line in text.split('\n') if line.strip()]
            except Exception as e:
                print(f"[WARN] Gemini API 호출 실패, 룰 기반 생성으로 대체: {e}")
        elif openai_key:
            try:
                url = "https://api.openai.com/v1/chat/completions"
                headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
                prompt = f"당신은 초보 창업자 컨설턴트입니다. 다음 공공데이터 샘플과 창업 아이디어('{query}')를 분석하여 초보 창업자가 주의해야 할 점, 체크리스트, 리스크 요인을 3가지로 요약해주세요. 데이터 샘플: {sample_records}"
                payload = {"model": "gpt-4o", "messages": [{"role": "user", "content": prompt}]}
                resp = requests.post(url, headers=headers, json=payload, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    text = data['choices'][0]['message']['content']
                    precautions = [line.strip() for line in text.split('\n') if line.strip()]
            except Exception as e:
                print(f"[WARN] OpenAI API 호출 실패, 룰 기반 생성으로 대체: {e}")

        # Fallback (API 키가 없거나 실패했을 경우 강력한 룰 기반 시맨틱 분석 엔진 작동)
        if not precautions:
            precautions.append(f"📌 [{query} 관련 핵심 점검] 공공데이터 분석 결과, '{x}' 기준 '{', '.join(y_list)}' 지표의 변동성이 존재하므로 특정 항목에 편중된 투자는 위험할 수 있습니다.")
            if y_list and len(df) >= 2:
                mean_val = df[y_list[0]].mean()
                max_val = df[y_list[0]].max()
                if max_val > mean_val * 3:
                    precautions.append(f"⚠️ [극단적 격차 주의] 최대값({max_val:.1f})이 평균({mean_val:.1f})의 3배 이상으로 큽니다. 상위 권역/항목이 시장을 독식하는 구조인지 확인이 필요합니다.")
                else:
                    precautions.append(f"📊 [균등 분포 시장] 지표들이 비교적 균등하게 분포되어 있습니다. 입지나 단가 외에 차별화된 마케팅 전략이 요구됩니다.")
            precautions.append(f"💡 [초보 창업 필수 체크리스트] 본 공공데이터 외에도 주변 상권 유동인구, 배달앱 입점 경쟁도, 그리고 초기 6개월치 고정비(임대료, 인건비) 확보를 반드시 점검하세요.")

        return precautions

    def _determine_strategy_and_calculate(self, df, x, y_list, temporal_cols, query, core_keyword=""):
        """[4단계] 시각화 전략 수립, 대용량 데이터 정보 추출 및 8가지 차트 맵핑"""
        # [Task 1] 합계/총계 행(Total Row) 자동 제거 로직
        if not pd.api.types.is_numeric_dtype(df[x]):
            exclude_keywords = ['합계', '총계', '전체', '총합', '계']
            mask = ~df[x].astype(str).str.strip().isin(exclude_keywords)
            df = df[mask].copy()

        # [Task 4] 지역명 표준화 (Region Normalization)
        if any(kw in str(x) for kw in ['지역', '시도', '시/도', '시군구', '상권']):
            def normalize_region(val):
                val_str = str(val).strip()
                mapping = {
                    "서울특별시": "서울", "부산광역시": "부산", "대구광역시": "대구", "인천광역시": "인천",
                    "광주광역시": "광주", "대전광역시": "대전", "울산광역시": "울산", "세종특별자치시": "세종", "세종시": "세종",
                    "강원특별자치도": "강원", "전북특별자치도": "전북", "제주특별자치도": "제주"
                }
                for k, v in mapping.items():
                    if val_str.startswith(k):
                        return val_str.replace(k, v)
                return val_str
            df[x] = df[x].apply(normalize_region)
        # 연령(Age) 데이터 스마트 그룹화 (10대, 20대 등)
        if "연령" in str(x) or "나이" in str(x) or "세" in str(x):
            import re
            def bin_age(val):
                val_str = str(val).strip()
                nums = re.findall(r'\d+', val_str)
                if nums:
                    age = int(nums[0])
                    if age < 10: return "10대 미만"
                    elif age >= 80: return "80대"
                    else: return f"{(age // 10) * 10}대"
                return val_str
                
            df[x] = df[x].apply(bin_age)

        # 1. 정보 간결화 (검색어 포커싱 및 '기타' 병합)
        # 여러 행이 같은 카테고리로 묶일 경우 총합(sum)을 구하는 것이 현황 파악에 적합함
        summary = df.groupby(x)[y_list].sum().reset_index()
        
        def match_score(val):
            val_str = str(val)
            if core_keyword and core_keyword in val_str: return 1000
            if query in val_str: return 100
            score = 0
            for w in query.split():
                if w in val_str: score += 10
            return score
            
        summary['match_score'] = summary[x].apply(match_score)
        
        # [Task 2] 시계열 데이터 시간순 정렬 보장
        is_temporal = x in temporal_cols or any(kw in str(x) for kw in ['년', '월', '일', '시간', '연도', '날짜', '분기'])
        
        if is_temporal:
            # 시간순은 기본적으로 최신 데이터(숫자가 큰 년도/월) 100개를 가져온 뒤 오름차순 정렬
            summary = summary.sort_values(by=x, ascending=False).head(100)
            summary = summary.sort_values(by=x, ascending=True)
        else:
            # 핵심 단어 매칭 및 수치 크기로 상위 100개 추출 후 내림차순 정렬
            summary = summary.sort_values(by=['match_score', y_list[0]], ascending=[False, False]).head(100)
            summary = summary.sort_values(by=y_list[0], ascending=False)
            
        summary = summary.drop(columns=['match_score'])
        
        # [Task 3] 롱테일 마이너 항목 "기타" 병합 (Long-tail Binning)
        if not is_temporal and len(summary) > 7:
            top_df = summary.iloc[:7].copy()
            others_df = summary.iloc[7:].copy()
            
            others_sum = others_df[y_list].sum()
            others_row = {x: "기타(Others)"}
            for y_col in y_list:
                others_row[y_col] = others_sum[y_col]
            
            top_df.loc[len(top_df)] = others_row
            summary = top_df

        # [Task 5] 극단적 이상치 상한 조정 (Outlier Capping)
        # 수치가 비정상적으로 하나만 튀는 경우 차트가 찌그러지는 것을 방지
        for y_col in y_list:
            if len(summary) >= 3:
                sorted_vals = summary[y_col].sort_values(ascending=False).values
                max_val = sorted_vals[0]
                second_max = sorted_vals[1]
                mean_val = summary[y_col].mean()
                
                # 최대값이 평균의 10배를 초과하고 2위 값보다 5배 이상 크면 극단적 이상치로 간주
                if max_val > mean_val * 10 and max_val > second_max * 5:
                    cap = second_max * 2.5 # 2위 값의 2.5배 수준으로 캡핑
                    # 라벨에 이상치 제한됨을 명시
                    summary.loc[summary[y_col] == max_val, x] = summary.loc[summary[y_col] == max_val, x].astype(str) + " (이상치 스케일조정)"
                    summary.loc[summary[y_col] == max_val, y_col] = cap

        unique_x_count = len(summary)
        chart_type = "bar"
        strategy_reason = ""
        
        if x in temporal_cols:
            if summary[y_list[0]].sum() > 5000:
                chart_type = "area"
                strategy_reason = "시간 흐름에 따른 누적/볼륨 변화를 강조하기 위해 영역 그래프(area)를 선택했습니다."
            else:
                chart_type = "line"
                strategy_reason = "시간 흐름 추이를 표현하기 위해 꺾은선 그래프(line)를 선택했습니다."
        elif len(y_list) >= 2:
            chart_type = "bar"
            strategy_reason = "다양한 핵심 지표들을 지역/항목별로 한눈에 비교 분석하기 위해 다중 막대 그래프(bar)를 선택했습니다."
        elif unique_x_count <= 3 and len(y_list) == 1:
            chart_type = "pie"
            strategy_reason = "항목 수가 적어 전체 점유율을 한눈에 파악하기 좋은 원그래프(pie)를 선택했습니다."
        elif unique_x_count == 4 and len(y_list) == 1:
            chart_type = "doughnut"
            strategy_reason = "비율 비교와 동시에 중앙 집중도를 높이는 도넛그래프(doughnut)를 선택했습니다."
        elif len(y_list) == 1 and not pd.api.types.is_numeric_dtype(df[x]):
            # Check if labels are actually long
            max_label_len = df[x].astype(str).str.len().max()
            if max_label_len > 8:
                chart_type = "horizontal_bar"
                strategy_reason = "라벨 이름이 길어 가독성을 확보하기 위해 가로 막대 그래프(horizontal_bar)를 선택했습니다."
            else:
                chart_type = "bar"
                strategy_reason = "항목 간의 크기 비교를 직관적으로 전달하기 위해 막대그래프(bar)를 선택했습니다."
        elif pd.api.types.is_numeric_dtype(df[x]) and len(y_list) == 1:
            chart_type = "histogram"
            strategy_reason = "수치 데이터의 구간별 분포를 파악하기 위해 히스토그램(histogram)을 선택했습니다."
        else:
            chart_type = "bar"
            strategy_reason = "항목 간의 크기 비교를 직관적으로 전달하기 위해 막대그래프(bar)를 선택했습니다."
            
        chart_title = f"'{query}' 맞춤형 {x}별 " + ", ".join(y_list) + " 분석"
        
        time_keywords = ["년", "월", "일", "분기", "현황", "상반기", "하반기"]
        is_wide_time_series = len(y_list) >= 2 and all(any(tk in str(y) for tk in time_keywords) for y in y_list)
        
        if is_wide_time_series:
            chart_type = "line"
            strategy_reason = "와이드 포맷(Wide-format) 시계열 데이터가 감지되어, 시간의 흐름을 직관적으로 보여주기 위해 X축과 Y축을 자동으로 피벗(Pivot)하고 꺾은선 그래프(line)를 선택했습니다."
            chart_title = f"'{query}' 시간 흐름에 따른 {x}별 추이 분석"
            
            # 피벗 수행: labels는 시간 칼럼(y_list)이 됨
            labels = [str(y) for y in y_list]
            datasets = []
            
            # datasets는 summary의 각 행(Entity)별로 생성됨
            for idx, row in summary.iterrows():
                entity_name = str(row[x])
                data_list = []
                for y_col in y_list:
                    val = row[y_col]
                    val = 0 if pd.isna(val) else round(float(val), 1)
                    data_list.append(val)
                datasets.append({
                    "label": entity_name,
                    "data": data_list
                })
        else:
            labels = summary[x].astype(str).tolist()
            datasets = []
            for y_col in y_list:
                data_list = summary[y_col].round(1).tolist()
                data_list = [0 if pd.isna(val) else val for val in data_list]
                datasets.append({
                    "label": str(y_col),
                    "data": data_list
                })
            
        return chart_type, chart_title, labels, datasets, strategy_reason

    def process(self, file_path, query="", core_keyword=""):
        """[5단계] 시각화 파이프라인 총괄 구동 및 최종 아웃풋 데이터 패키징"""
        # 1. 파일 로드
        df = self._load_file(file_path)
        if df is None:
            return None

        # 2. 데이터 타입 추론
        temporal, numerical, categorical = self._infer_data_types(df)

        # 3. 최적의 축 매핑 (사용자 검색어 기반 지능형 추출)
        x, y_list = self._select_optimal_axes(df, temporal, numerical, categorical, query)
        if not x or not y_list:
            print("[ERROR] 시각화할 수 있는 유효한 숫자 데이터가 부족합니다.")
            return None

        # 4. 다차원 뷰 생성 (Temporal & Dimensions)
        temporal_col = None
        for col in df.columns:
            if '연도' in col or '년도' in col or '발생년' in col or col in temporal:
                temporal_col = col
                break
                
        other_categorical = []
        for col in categorical:
            if col != x and col != temporal_col and 2 <= df[col].nunique() <= 50:
                other_categorical.append(col)
                
        dimensions = [x]
        if other_categorical:
            best_other = None
            for col in other_categorical:
                if '유형' in str(col) or '원인' in str(col) or '성별' in str(col) or '연령' in str(col):
                    best_other = col
                    break
            if not best_other:
                best_other = other_categorical[0]
            if best_other not in dimensions:
                dimensions.append(best_other)
                
        views = {}
        available_years = []
        
        if temporal_col and df[temporal_col].nunique() > 1 and df[temporal_col].nunique() < 20:
            years = sorted(df[temporal_col].dropna().unique().tolist(), reverse=True)
            available_years = [str(y) for y in years]
            
            for y_val in years:
                year_str = str(y_val)
                views[year_str] = {}
                sub_df = df[df[temporal_col] == y_val].copy()
                
                for dim in dimensions:
                    (c_type, c_title, lbls, dsets, rsn) = self._determine_strategy_and_calculate(sub_df, dim, y_list, temporal, query, core_keyword)
                    table_cols = [dim] + y_list
                    table_df = sub_df[table_cols].head(50).fillna("")
                    views[year_str][dim] = {
                        "chart_type": c_type,
                        "chart_title": f"[{year_str}] {dim} 기준 분석",
                        "labels": lbls,
                        "datasets": dsets,
                        "reason": rsn,
                        "table_data": {"headers": [str(c) for c in table_cols], "rows": table_df.values.tolist()}
                    }
        else:
            views["전체"] = {}
            available_years = ["전체"]
            for dim in dimensions:
                (c_type, c_title, lbls, dsets, rsn) = self._determine_strategy_and_calculate(df, dim, y_list, temporal, query, core_keyword)
                table_cols = [dim] + y_list
                table_df = df[table_cols].head(50).fillna("")
                views["전체"][dim] = {
                    "chart_type": c_type,
                    "chart_title": c_title,
                    "labels": lbls,
                    "datasets": dsets,
                    "reason": rsn,
                    "table_data": {"headers": [str(c) for c in table_cols], "rows": table_df.values.tolist()}
                }

        # 5. 프론트엔드 웹 위젯 레이어 전송용 표준 JSON 스키마 반환
        first_y = available_years[0]
        first_d = dimensions[0]
        first_view = views[first_y][first_d]
        
        startup_precautions = self._generate_startup_precautions(df, x, y_list, query)
        
        widget_schema = {
            "status": "success",
            "available_years": available_years,
            "available_dimensions": dimensions,
            "views": views,
            "core_keyword": core_keyword,
            "startup_precautions": startup_precautions,
            
            # fallback for older code
            "chart_type": first_view["chart_type"],
            "chart_title": first_view["chart_title"],
            "labels": first_view["labels"],
            "datasets": first_view["datasets"],
            "table_data": first_view["table_data"]
        }

        print("\n[SUCCESS] 프론트엔드 웹 위젯 레이어 통신용 표준 JSON 스키마 생성 완료 (창업 주의사항 포함)")
        return widget_schema

# Singleton instance
engine = IntelligentVisualizerEngine()

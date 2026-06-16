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
        """[1단계] 파일 확장자 판별 및 인코딩 방어벽을 통한 데이터 로드"""
        file_ext = os.path.splitext(file_path)[-1].lower()
        import zipfile
        import glob
        
        # 한국 공공데이터의 ZIP 압축 해제 로직
        if file_ext == ".zip":
            extract_dir = os.path.splitext(file_path)[0]
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # euckr encoding for korean filenames in zip
                    zip_ref.extractall(extract_dir)
                
                # Find the first valid csv or excel file in the extracted directory
                extracted_files = []
                for ext in ('*.csv', '*.xlsx', '*.xls'):
                    extracted_files.extend(glob.glob(os.path.join(extract_dir, '**', ext), recursive=True))
                
                if extracted_files:
                    print(f"[INFO] ZIP 파일 내에서 {os.path.basename(extracted_files[0])} 파일을 분석합니다.")
                    return self._load_file(extracted_files[0]) # 재귀 호출로 CSV/Excel 로드
            except Exception as e:
                print(f"[ERROR] ZIP 압축 해제 실패: {e}")
                return None
                
        if file_ext in [".xlsx", ".xls"]:
            try:
                return pd.read_excel(file_path)
            except Exception as e:
                print(f"[ERROR] Excel 로드 실패: {e}")
                return None
        elif file_ext == ".csv":
            # 한국 공공데이터 특유의 변칙 인코딩 순회 감지
            for enc in ["utf-8", "cp949", "euc-kr", "utf-8-sig"]:
                try:
                    return pd.read_csv(file_path, encoding=enc)
                except:
                    continue
        print("[ERROR] 지원하지 않는 파일 형식이거나 손상된 파일입니다.")
        return None

    def _infer_data_types(self, df):
        """[2단계] 가로/세로 항목의 실제 데이터 형태 추론 엔진"""
        temporal_cols = []
        numerical_cols = []
        categorical_cols = []

        for col in df.columns:
            valid_series = df[col].dropna()
            if valid_series.empty:
                continue

            # A. 수치형 데이터 여부 판별 (텍스트가 섞인 수치 데이터 정제 포함)
            sample_str = valid_series.astype(str).str.replace(
                r"[^\d.]", "", regex=True
            )
            num_conv = pd.to_numeric(sample_str, errors="coerce")

            # 수치 변환 성공률이 70% 이상이면 수치형 컬럼으로 확정
            if num_conv.notna().sum() / len(df) > 0.7:
                df[col] = num_conv.fillna(0)  # 원본 데이터 가공 후 덮어쓰기
                numerical_cols.append(col)
                continue

            # B. 시계열(날짜/시간) 데이터 여부 판별
            if "날짜" in col or "일자" in col or "계약일" in col:
                temporal_cols.append(col)
            elif (
                valid_series.astype(str)
                .str.contains(r"\d{4}-\d{2}-\d{2}|\d{8}")
                .sum()
                / len(df)
                > 0.5
            ):
                temporal_cols.append(col)
            else:
                # C. 위 조건에 해당하지 않으면 텍스트(범주형)로 분류
                categorical_cols.append(col)

        return temporal_cols, numerical_cols, categorical_cols

    def _select_optimal_axes(self, df, temporal, numerical, categorical):
        """[3단계] 데이터 성격에 알맞은 최적의 X축과 다중 Y축 자동 선정 알고리즘"""
        final_x = None
        final_y_list = []

        # Y축(수치형) 선정: 무의미한 번호 컬럼 제외
        invalid_y = ["번호", "순번", "id", "순위", "no", "연번", "연도"]
        valid_numerical = [col for col in numerical if not any(inv in col.lower() for inv in invalid_y)]
        
        # 가중치 우선순위에 따라 Y축 최대 3개 선정
        for kw in self.y_priority_keywords:
            for col in valid_numerical:
                if kw in col and col not in final_y_list:
                    final_y_list.append(col)
                if len(final_y_list) >= 3:
                    break
            if len(final_y_list) >= 3:
                break
                
        # 우선순위에 없더라도 유효한 숫자 컬럼이 있다면 추가
        for col in valid_numerical:
            if len(final_y_list) >= 3:
                break
            if col not in final_y_list:
                final_y_list.append(col)

        # X축 선정: 무의미한 번호 컬럼 제외
        valid_categorical = [col for col in categorical if not any(inv in col.lower() for inv in invalid_y)]
        
        if temporal:
            final_x = temporal[0]
        elif valid_categorical:
            for col in valid_categorical:
                if 2 <= df[col].nunique() <= 100:
                    final_x = col
                    break
            if not final_x:
                final_x = valid_categorical[0]
        else:
            final_x = df.columns[0]

        return final_x, final_y_list

    def _determine_strategy_and_calculate(self, df, x, y_list, temporal_cols):
        """[4단계] 시각화 전략 수립, 대용량 데이터 요약/집계 연산 처리"""
        unique_x_count = df[x].nunique()
        chart_type = "bar"
        strategy_reason = ""
        
        if x in temporal_cols:
            chart_type = "line"
            strategy_reason = "시간 흐름 추이를 표현하기 위해 선 그래프(line) 전략을 수립합니다."
        elif unique_x_count <= 5 and len(y_list) == 1:
            chart_type = "pie"
            strategy_reason = "비교 항목 수가 적어 점유율 파악에 용이한 원형 그래프(pie) 전략을 수립합니다."
        elif unique_x_count <= 15 and len(y_list) == 1:
            chart_type = "horizontal_bar"
            strategy_reason = "라벨 가독성 확보를 위해 가로 막대 그래프(horizontal_bar) 전략을 수립합니다."
        else:
            chart_type = "bar"
            strategy_reason = f"다중 지표({len(y_list)}개) 비교 및 복합 렌더링을 위해 막대/선 그래프(bar) 전략을 수립합니다."
            
        chart_title = f"{x}별 " + ", ".join(y_list) + " 분석"
        
        # 집계 연산
        summary = df.groupby(x)[y_list].mean().reset_index()
        
        # 정렬 (첫 번째 Y축 기준)
        if chart_type != "line":
            summary = summary.sort_values(by=y_list[0], ascending=False)
            # 최대 100개까지만 리턴하고, 프론트엔드에서 페이징(더보기) 처리
            summary = summary.head(100)
        else:
            summary = summary.sort_values(by=x)
            summary = summary.head(100)

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

    def process(self, file_path):
        """[5단계] 시각화 파이프라인 총괄 구동 및 최종 아웃풋 데이터 패키징"""
        # 1. 파일 로드
        df = self._load_file(file_path)
        if df is None:
            return None

        # 2. 데이터 타입 추론
        temporal, numerical, categorical = self._infer_data_types(df)

        # 3. 최적의 축 매핑
        x, y_list = self._select_optimal_axes(df, temporal, numerical, categorical)
        if not x or not y_list:
            print("[ERROR] 시각화할 수 있는 유효한 숫자 데이터가 부족합니다.")
            return None

        # 4. 시각화 전략 수립 및 집계 연산
        (
            chart_type,
            chart_title,
            labels,
            datasets,
            reason,
        ) = self._determine_strategy_and_calculate(df, x, y_list, temporal)

        # 5. 브리핑 출력
        print(f"\n================ [INFO] 다차원 데이터 자동 분석 보고서 ================")
        print("[INFO] 분석 파일: " + os.path.basename(file_path))
        print(f"[INFO] 다중 지표: Y축 {y_list}")
        print(f"[INFO] 전략: {reason}")
        print(f"=================================================================\n")

        # 6. 파이썬 로컬/코랩 차트 시각화 실행 (서버 Blocking 방지를 위해 주석 처리)
        """
        plt.figure(figsize=(10, 5))
        if chart_type == "line":
            plt.plot(
                labels, chart_data, marker="o", color="#2bc0e4", linewidth=2.5
            )
        elif chart_type == "pie":
            plt.pie(
                chart_data,
                labels=labels,
                autopct="%1.1f%%",
                startangle=90,
                colors=sns.color_palette("pastel"),
            )
        else:  # bar 형태
            sns.barplot(
                x=labels,
                y=chart_data,
                palette="Blues_r",
                hue=labels,
                legend=False,
            )

        plt.title(chart_title, fontsize=13, fontweight="bold", pad=15)
        if chart_type != "pie":
            plt.xticks(rotation=35, ha="right")
            plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.show()
        """

        # 7. 프론트엔드 크롬 확장 프로그램(웹 위젯) 전송용 표준 JSON 스키마 반환
        widget_schema = {
            "status": "success",
            "chart_type": chart_type,
            "chart_title": chart_title,
            "labels": labels,
            "datasets": datasets,
        }

        print("\n[SUCCESS] 프론트엔드 웹 위젯 레이어 통신용 표준 JSON 스키마 생성 완료")
        return widget_schema

# Singleton instance
engine = IntelligentVisualizerEngine()

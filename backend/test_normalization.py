import os
import sys
import pandas as pd

# Add backend directory to sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.services.excel_processor import normalize_excel
from app.services.intelligent_visualizer import engine

def run_test():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    print("=== [테스트 1] 지저분한 상단 안내문구가 포함된 샘플 CSV 생성 ===")
    sample_path = os.path.join(backend_dir, "data", "sample_dirty_startup.csv")
    os.makedirs(os.path.dirname(sample_path), exist_ok=True)
    
    # 공공데이터 특유의 지저분한 데이터 시뮬레이션 (0~1행 안내문구, 2행 실제 헤더)
    raw_data = [
        ["본 데이터는 공공데이터포털에서 제공하는 상권 분석 자료입니다.", "", "", "", ""],
        ["주의사항: 영리적 목적 활용 시 출처를 표기해주세요.", "", "", "", ""],
        ["지역명", "점포수", "유동인구", "평균매출액", "비고"],
        ["서울 강남구", "1,520개", "450,000명", "52000000원", "상권밀집"],
        ["부산 해운대구", "850개", "280,000명", "38000000원", "관광특구"],
        ["대구 중구", "620개", "190,000명", "29000000원", "구도심"],
        ["인천 부평구", "740개", "250,000명", "34000000원", "교통거점"],
        ["광주 서구", "510개", "160,000명", "27000000원", "신흥상권"]
    ]
    
    df_raw = pd.DataFrame(raw_data)
    df_raw.to_csv(sample_path, index=False, header=False, encoding="utf-8-sig")
    print(f"샘플 파일 생성 완료: {sample_path}")
    
    print("\n=== [테스트 2] normalize_excel 정규화 테스트 ===")
    df_clean = normalize_excel(sample_path)
    print("정규화된 DataFrame 결과:")
    print(df_clean)
    
    print("\n=== [테스트 3] 초보 창업자 '카페 창업' 키워드 기반 시각화 파이프라인 테스트 ===")
    result = engine.process(sample_path, query="카페 창업 상권 분석", core_keyword="카페")
    
    print("\n=== [최종 검증 결과] ===")
    print(f"차트 제목: {result.get('chart_title')}")
    print(f"선택된 X축 라벨: {result.get('labels')}")
    print(f"선택된 Y축 데이터셋: {result.get('datasets')}")
    print("\n[생성된 초보 창업자 주의사항]:")
    for item in result.get("startup_precautions", []):
        print(f"- {item}")
        
    print("\n[SUCCESS] 모든 정규화 및 분석 엔진 검증 완료!")

if __name__ == "__main__":
    run_test()

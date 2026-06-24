import os
import pandas as pd
import glob
import zipfile

def normalize_excel(file_path: str) -> pd.DataFrame:
    """
    [범용 공공데이터 정규화 엔진]
    기관마다 제각각인 엑셀/CSV 파일(병합 셀, 상단 안내문구 행, 변칙 인코딩 등)을
    AI가 즉시 분석 가능한 깔끔한 DataFrame으로 정제하여 반환합니다.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] 파일이 존재하지 않습니다: {file_path}")
        return None

    file_ext = os.path.splitext(file_path)[-1].lower()
    df = None

    # 1. ZIP 파일 자동 압축 해제 및 대상 탐색
    if file_ext == ".zip":
        extract_dir = os.path.splitext(file_path)[0]
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            extracted_files = []
            for ext in ('*.csv', '*.xlsx', '*.xls'):
                extracted_files.extend(glob.glob(os.path.join(extract_dir, '**', ext), recursive=True))
            if extracted_files:
                print(f"[INFO] ZIP 파일 내에서 {os.path.basename(extracted_files[0])} 파일을 정규화합니다.")
                return normalize_excel(extracted_files[0])
        except Exception as e:
            print(f"[ERROR] ZIP 압축 해제 실패: {e}")
            return None

    # 2. 다양한 인코딩 방어 및 데이터 로드
    if file_ext in [".xlsx", ".xls"]:
        try:
            # 전체 데이터를 문자열 표 형태로 1차 로드 (헤더 탐지용)
            df = pd.read_excel(file_path, header=None)
        except Exception as e:
            print(f"[ERROR] Excel 파일 로드 실패: {e}")
            return None
    elif file_ext == ".csv":
        for enc in ["utf-8", "cp949", "euc-kr", "utf-8-sig"]:
            try:
                df = pd.read_csv(file_path, encoding=enc, header=None)
                break
            except:
                continue

    if df is None or df.empty:
        print("[ERROR] 데이터를 로드할 수 없거나 파일이 비어 있습니다.")
        return None

    # 3. 지능형 헤더 행(Table Header Row) 자동 탐지 및 상단 안내문구 스킵
    # 공공데이터 엑셀은 0~3행에 제목이나 안내문구가 들어가고, 실제 테이블 헤더는 그 아래에 있는 경우가 많음.
    # 각 행별 유효 문자열 개수(non-null, non-empty)를 측정하여 가장 컬럼 수가 많고 온전한 행을 헤더로 선정.
    best_header_idx = 0
    max_valid_cols = 0
    
    for idx in range(min(10, len(df))):
        row_vals = df.iloc[idx].dropna().astype(str).str.strip()
        valid_vals = [val for val in row_vals if val != "" and val != "nan"]
        if len(valid_vals) > max_valid_cols:
            max_valid_cols = len(valid_vals)
            best_header_idx = idx

    # 선정된 헤더 행으로 컬럼 설정
    headers = df.iloc[best_header_idx].astype(str).str.strip().tolist()
    # 컬럼명 중복 방지 및 비어있는 컬럼명 정리
    clean_headers = []
    for i, h in enumerate(headers):
        if h == "" or h == "nan" or h == "None":
            h = f"Unnamed_{i}"
        # 중복 검사
        orig_h = h
        count = 1
        while h in clean_headers:
            h = f"{orig_h}_{count}"
            count += 1
        clean_headers.append(h)
        
    df.columns = clean_headers
    
    # 헤더 이전의 상단 설명 행들과 헤더 행 자체를 데이터에서 제거
    df = df.iloc[best_header_idx + 1:].copy()
    
    # 4. 완전 공백 행 및 열 제거 (결측치 정제)
    df = df.dropna(how='all', subset=df.columns)
    df = df.reset_index(drop=True)
    
    # 문자열 컬럼의 앞뒤 공백 제거
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].astype(str).str.strip()

    print(f"[SUCCESS] 엑셀/CSV 데이터 정규화 완료 (탐지된 헤더 행: {best_header_idx})")
    return df


def process_excel(query: str):
    """
    Search for a matching Excel file in backend/data/ based on the query.
    Extract the first string column as labels, and first numeric column as data.
    """
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    
    if not os.path.exists(data_dir):
        return None
        
    # Find matching file
    files = glob.glob(os.path.join(data_dir, "*.*"))
    target_file = None
    for f in files:
        basename = os.path.basename(f)
        name_without_ext = os.path.splitext(basename)[0]
        # Very simple matching: if the filename is in the query, or query in filename
        if name_without_ext in query or query in name_without_ext:
            target_file = f
            break
            
    if not target_file:
        return None
        
    # Read the file
    try:
        if target_file.endswith(".csv"):
            df = pd.read_csv(target_file)
        else:
            df = pd.read_excel(target_file)
            
        if df.empty:
            return None
            
        # Find label column (first object/string column)
        label_col = None
        for col in df.columns:
            if df[col].dtype == 'object':
                label_col = col
                break
        
        # Find data column (first numeric column)
        data_col = None
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                data_col = col
                break
                
        if not label_col or not data_col:
            # Fallback if types are weird: take first column as label, second as data
            label_col = df.columns[0]
            data_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
            
        # Take top 5 rows
        top_df = df.head(5)
        
        labels = top_df[label_col].astype(str).tolist()
        data = top_df[data_col].tolist()
        
        # Clean numeric data (handle NaN)
        cleaned_data = []
        for val in data:
            try:
                cleaned_data.append(float(val))
            except:
                cleaned_data.append(0)
                
        title = os.path.splitext(os.path.basename(target_file))[0]
        
        return {
            "title": f"{title} 통계 요약",
            "summary": f"'{label_col}' 기준 '{data_col}' 차트입니다.",
            "chart": {
                "type": "bar",
                "labels": labels,
                "datasets": [
                    {
                        "label": data_col,
                        "data": cleaned_data,
                        "unit": ""
                    }
                ]
            },
            "source": f"로컬 공공데이터 ({os.path.basename(target_file)})"
        }
    except Exception as e:
        print(f"Excel Processing Error: {e}")
        return None

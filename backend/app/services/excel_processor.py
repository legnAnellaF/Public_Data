import os
import pandas as pd
import glob

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

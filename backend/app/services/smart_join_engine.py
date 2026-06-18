import pandas as pd
import os

class SmartJoinEngine:
    def __init__(self):
        self.entity_keywords = ["시도", "행정구역", "지역", "구분", "항목", "구군", "시군구", "도시", "지자체"]

    def _infer_entity_column(self, df: pd.DataFrame):
        """Finds the most likely categorical column to join on."""
        for kw in self.entity_keywords:
            for col in df.columns:
                if kw in str(col) and df[col].dtype == 'object':
                    return col
        # Fallback to the first categorical column
        for col in df.columns:
            if df[col].dtype == 'object':
                return col
        return None

    def _normalize_entity(self, val):
        """Normalizes region names (e.g. 서울특별시 -> 서울)."""
        val = str(val).strip()
        replacements = {
            "특별시": "", "광역시": "", "특별자치시": "", "특별자치도": "", "자치도": "", "남도": "남", "북도": "북"
        }
        if val in ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "제주"]:
            return val
        for old, new in replacements.items():
            val = val.replace(old, new)
        return val

    def join_datasets(self, file_paths: list, query: str):
        """
        Reads multiple CSV/Excel files and joins them on a common entity column.
        Returns the path to the newly merged CSV.
        """
        from app.services.dynamic_scraper import extract_keywords
        keywords = extract_keywords(query)
        if not keywords:
            return None

        dataframes = []
        
        for fp in file_paths:
            if not os.path.exists(fp):
                continue
                
            try:
                if fp.endswith('.csv'):
                    try:
                        df = pd.read_csv(fp, encoding='utf-8-sig')
                    except:
                        df = pd.read_csv(fp, encoding='cp949')
                else:
                    df = pd.read_excel(fp)
            except Exception as e:
                print(f"[SmartJoin] Failed to read {fp}: {e}")
                continue

            # Find entity column
            entity_col = self._infer_entity_column(df)
            if not entity_col:
                continue

            # Find matching numerical columns
            matched_cols = []
            file_name = os.path.basename(fp)
            
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    col_str = str(col)
                    
                    # 1. 컬럼명 자체에 키워드가 있는 경우
                    matched_kw = next((kw for kw in keywords if kw in col_str), None)
                    
                    # 2. 파일명에 키워드가 있는 경우
                    if not matched_kw:
                        # '현황', '전국' 등 너무 포괄적인 단어보다 핵심 명사를 우선시
                        core_kws = [k for k in keywords if k not in ["전국", "현황", "통계", "데이터"]]
                        matched_kw = next((kw for kw in core_kws if kw in file_name), None)
                        if not matched_kw:
                            matched_kw = next((kw for kw in keywords if kw in file_name), None)
                            
                    if matched_kw:
                        new_col_name = f"{matched_kw}_{col}"
                        df = df.rename(columns={col: new_col_name})
                        matched_cols.append(new_col_name)
                        break # 각 파일당 가장 먼저 발견된 수치형 칼럼 1개만 추출 (핵심 지표)

            if not matched_cols:
                continue

            # Normalize entity column
            df['__join_key'] = df[entity_col].apply(self._normalize_entity)
            
            # Group by join key and sum
            grouped = df.groupby('__join_key')[matched_cols].sum().reset_index()
            dataframes.append(grouped)

        if len(dataframes) < 2:
            print("[SmartJoin] Not enough matching dataframes to join.")
            if len(dataframes) == 1:
                # Just return the single file if we couldn't merge multiple
                return file_paths[0]
            return None

        # Merge all dataframes on __join_key
        merged_df = dataframes[0]
        for df in dataframes[1:]:
            merged_df = pd.merge(merged_df, df, on='__join_key', how='outer')

        # Clean up
        merged_df = merged_df.fillna(0)
        merged_df = merged_df.rename(columns={'__join_key': '통합분류항목'})

        output_path = os.path.join(os.path.expanduser("~"), "Desktop", "public_data_downloads", "merged_smart_join.csv")
        merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"[SmartJoin] Successfully joined data into {output_path}")
        
        return output_path

join_engine = SmartJoinEngine()

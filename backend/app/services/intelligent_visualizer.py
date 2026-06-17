import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IntelligentVisualizerEngine:
    def __init__(self) -> None:
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

    def _load_file(self, file_path: str):
        try:
            import pandas as pd
        except Exception as exc:
            logger.info("dynamic_visualizer pandas_unavailable error=%s", type(exc).__name__)
            return None

        path = Path(file_path)
        file_ext = path.suffix.lower()

        if file_ext == ".zip":
            extract_dir = Path(tempfile.mkdtemp(prefix="pdw_zip_"))
            try:
                with zipfile.ZipFile(path, "r") as zip_ref:
                    zip_ref.extractall(extract_dir)
                extracted_files: list[Path] = []
                for ext in ("*.csv", "*.xlsx", "*.xls"):
                    extracted_files.extend(extract_dir.rglob(ext))
                if extracted_files:
                    return self._load_file(str(extracted_files[0]))
            except Exception as exc:
                logger.warning("dynamic_visualizer zip_load_failed file=%s error=%s", file_path, type(exc).__name__)
            return None

        if file_ext in {".xlsx", ".xls"}:
            try:
                return pd.read_excel(path)
            except Exception as exc:
                logger.warning("dynamic_visualizer excel_load_failed file=%s error=%s", file_path, type(exc).__name__)
                return None

        if file_ext == ".csv":
            for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
                try:
                    return pd.read_csv(path, encoding=encoding)
                except Exception:
                    continue
            logger.warning("dynamic_visualizer csv_load_failed file=%s", file_path)
            return None

        logger.warning("dynamic_visualizer unsupported_file_type file=%s", file_path)
        return None

    def _infer_data_types(self, df: Any) -> tuple[list[str], list[str], list[str]]:
        import pandas as pd

        temporal_cols: list[str] = []
        numerical_cols: list[str] = []
        categorical_cols: list[str] = []

        for col in df.columns:
            col_name = str(col)
            valid_series = df[col].dropna()
            if valid_series.empty:
                continue

            sample_str = valid_series.astype(str).str.replace(r"[^0-9.\-]", "", regex=True)
            num_conv = pd.to_numeric(sample_str, errors="coerce")
            if len(valid_series) and num_conv.notna().sum() / len(valid_series) > 0.7:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors="coerce").fillna(0)
                numerical_cols.append(col_name)
                continue

            sample_text = valid_series.astype(str)
            if "날짜" in col_name or "일자" in col_name or "계약일" in col_name:
                temporal_cols.append(col_name)
            elif len(valid_series) and sample_text.str.contains(r"\d{4}-\d{2}-\d{2}|\d{8}", regex=True).sum() / len(valid_series) > 0.5:
                temporal_cols.append(col_name)
            else:
                categorical_cols.append(col_name)

        return temporal_cols, numerical_cols, categorical_cols

    def _select_optimal_axes(
        self,
        df: Any,
        temporal: list[str],
        numerical: list[str],
        categorical: list[str],
    ) -> tuple[str | None, list[str]]:
        invalid_y = ("번호", "순번", "id", "순위", "no", "연번", "연도")
        valid_numerical = [col for col in numerical if not any(item in col.lower() for item in invalid_y)]

        final_y_list: list[str] = []
        for keyword in self.y_priority_keywords:
            for col in valid_numerical:
                if keyword in col and col not in final_y_list:
                    final_y_list.append(col)
                if len(final_y_list) >= 3:
                    break
            if len(final_y_list) >= 3:
                break

        for col in valid_numerical:
            if len(final_y_list) >= 3:
                break
            if col not in final_y_list:
                final_y_list.append(col)

        valid_categorical = [col for col in categorical if not any(item in col.lower() for item in invalid_y)]
        final_x: str | None = None
        if temporal:
            final_x = temporal[0]
        elif valid_categorical:
            for col in valid_categorical:
                if 2 <= df[col].nunique() <= 100:
                    final_x = col
                    break
            final_x = final_x or valid_categorical[0]
        elif len(df.columns) > 0:
            final_x = str(df.columns[0])

        return final_x, final_y_list

    def _determine_strategy_and_calculate(
        self,
        df: Any,
        x: str,
        y_list: list[str],
        temporal_cols: list[str],
    ) -> tuple[str, str, list[str], list[dict[str, Any]]]:
        import pandas as pd

        unique_x_count = df[x].nunique()
        if x in temporal_cols:
            chart_type = "line"
        elif unique_x_count <= 5 and len(y_list) == 1:
            chart_type = "pie"
        elif unique_x_count <= 15 and len(y_list) == 1:
            chart_type = "horizontal_bar"
        else:
            chart_type = "bar"

        chart_title = f"{x}별 " + ", ".join(y_list) + " 분석"
        summary = df.groupby(x)[y_list].mean().reset_index()
        if chart_type != "line":
            summary = summary.sort_values(by=y_list[0], ascending=False).head(100)
        else:
            summary = summary.sort_values(by=x).head(100)

        labels = summary[x].astype(str).tolist()
        datasets = []
        for y_col in y_list:
            data_list = summary[y_col].round(1).tolist()
            datasets.append({
                "label": str(y_col),
                "data": [0 if pd.isna(value) else float(value) for value in data_list],
                "unit": "",
            })

        return chart_type, chart_title, labels, datasets

    def process(self, file_path: str) -> dict[str, Any] | None:
        df = self._load_file(file_path)
        if df is None or getattr(df, "empty", True):
            return None

        temporal, numerical, categorical = self._infer_data_types(df)
        x, y_list = self._select_optimal_axes(df, temporal, numerical, categorical)
        if not x or not y_list:
            logger.info("dynamic_visualizer insufficient_numeric_data file=%s", os.path.basename(file_path))
            return None

        chart_type, chart_title, labels, datasets = self._determine_strategy_and_calculate(df, x, y_list, temporal)
        return {
            "status": "success",
            "chart_type": chart_type,
            "chart_title": chart_title,
            "labels": labels,
            "datasets": datasets,
        }


engine = IntelligentVisualizerEngine()

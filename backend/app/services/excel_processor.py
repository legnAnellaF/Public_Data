from pathlib import Path
from typing import Any

from backend.app.services.intelligent_visualizer import engine


def process_tabular_file(file_path: str) -> dict[str, Any] | None:
    schema = engine.process(file_path)
    if not schema or schema.get("status") != "success":
        return None

    path = Path(file_path)
    return {
        "title": schema["chart_title"],
        "summary": f"'{path.name}' 파일에서 자동 추출한 수치 데이터입니다.",
        "chart": {
            "type": schema["chart_type"],
            "labels": schema["labels"],
            "datasets": schema["datasets"],
        },
        "source": {
            "name": f"다운로드 공공데이터 ({path.name})",
            "url": None,
            "updated_at": "dynamic",
            "is_mock": False,
        },
        "file_name": path.name,
    }


def process_excel(file_path: str) -> dict[str, Any] | None:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return None
    return process_tabular_file(str(path))

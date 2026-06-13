import json
from pathlib import Path

from backend.app.schemas.intent import IntentResult, SearchRequest
from backend.app.schemas.widget import WidgetResponse


ROOT_DIR = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = ROOT_DIR / "contracts"


def schema_for(model: type) -> dict:
    if hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    return model.schema()


def main() -> None:
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)
    exports = {
        "extension_request.schema.json": SearchRequest,
        "intent_result.schema.json": IntentResult,
        "widget_response.schema.json": WidgetResponse,
    }
    for filename, model in exports.items():
        path = CONTRACTS_DIR / filename
        path.write_text(
            json.dumps(schema_for(model), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()

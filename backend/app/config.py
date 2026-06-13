import os
from dataclasses import dataclass
from functools import lru_cache

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is listed, fallback keeps imports safe.
    load_dotenv = None


if load_dotenv is not None:
    load_dotenv()


DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_origins(value: str | None) -> list[str]:
    if not value:
        return DEFAULT_ALLOWED_ORIGINS.copy()
    cleaned = value.strip().strip("[]")
    origins = [item.strip() for item in cleaned.split(",") if item.strip()]
    return origins or DEFAULT_ALLOWED_ORIGINS.copy()


@dataclass(frozen=True)
class Settings:
    app_name: str
    version: str
    app_env: str
    mock_public_api: bool
    public_api_timeout_seconds: int
    public_api_cache_ttl_seconds: int
    public_data_service_key: str
    air_quality_api_base_url: str
    real_estate_api_base_url: str
    traffic_api_base_url: str
    weather_api_base_url: str
    economy_api_base_url: str
    allowed_origins: list[str]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    def base_url_for_category(self, category: str) -> str:
        return {
            "environment_air_quality": self.air_quality_api_base_url,
            "real_estate": self.real_estate_api_base_url,
            "traffic": self.traffic_api_base_url,
            "weather": self.weather_api_base_url,
            "economy": self.economy_api_base_url,
        }.get(category, "")


@lru_cache
def get_settings() -> Settings:
    return Settings(
        app_name=os.getenv("APP_NAME", "public-data-widget-backend"),
        version=os.getenv("APP_VERSION", "0.1.0"),
        app_env=os.getenv("APP_ENV", "development"),
        mock_public_api=_parse_bool(os.getenv("MOCK_PUBLIC_API"), True),
        public_api_timeout_seconds=_parse_int(os.getenv("PUBLIC_API_TIMEOUT_SECONDS"), 5),
        public_api_cache_ttl_seconds=_parse_int(os.getenv("PUBLIC_API_CACHE_TTL_SECONDS"), 300),
        public_data_service_key=os.getenv("PUBLIC_DATA_SERVICE_KEY", ""),
        air_quality_api_base_url=os.getenv("AIR_QUALITY_API_BASE_URL", ""),
        real_estate_api_base_url=os.getenv("REAL_ESTATE_API_BASE_URL", ""),
        traffic_api_base_url=os.getenv("TRAFFIC_API_BASE_URL", ""),
        weather_api_base_url=os.getenv("WEATHER_API_BASE_URL", ""),
        economy_api_base_url=os.getenv("ECONOMY_API_BASE_URL", ""),
        allowed_origins=_parse_origins(os.getenv("ALLOWED_ORIGINS")),
    )

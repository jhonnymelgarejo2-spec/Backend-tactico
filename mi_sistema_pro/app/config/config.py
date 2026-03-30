# app/config/config.py

import os


class Settings:
    SYSTEM_NAME: str = os.getenv("SYSTEM_NAME", "JHONNY_ELITE")
    SYSTEM_VERSION: str = os.getenv("SYSTEM_VERSION", "V17")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", "10000"))

    # Operación
    MINUTE_MIN_OPERABLE: int = int(os.getenv("MINUTE_MIN_OPERABLE", "15"))
    MINUTE_MAX_OPERABLE: int = int(os.getenv("MINUTE_MAX_OPERABLE", "88"))
    MAX_SIGNALS: int = int(os.getenv("MAX_SIGNALS", "6"))

    # API Football
    FOOTBALL_API_KEY: str = os.getenv("FOOTBALL_API_KEY", "").strip()
    FOOTBALL_API_URL: str = os.getenv(
        "FOOTBALL_API_URL",
        "https://v3.football.api-sports.io/fixtures?live=all",
    ).strip()
    FOOTBALL_STATISTICS_URL: str = os.getenv(
        "FOOTBALL_STATISTICS_URL",
        "https://v3.football.api-sports.io/fixtures/statistics",
    ).strip()

    HTTP_TIMEOUT_SECONDS: int = int(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
    STAT_REQUEST_SLEEP_MS: int = int(os.getenv("STAT_REQUEST_SLEEP_MS", "120"))
    MAX_SOURCE_DELAY_SECONDS: int = int(os.getenv("MAX_SOURCE_DELAY_SECONDS", "90"))

    # Defaults
    DEFAULT_PROB_REAL: float = float(os.getenv("DEFAULT_PROB_REAL", "0.75"))
    DEFAULT_PROB_IMPLICITA: float = float(os.getenv("DEFAULT_PROB_IMPLICITA", "0.54"))
    DEFAULT_ODD: float = float(os.getenv("DEFAULT_ODD", "1.85"))
    DEFAULT_MOMENTUM: str = os.getenv("DEFAULT_MOMENTUM", "MEDIO")

    # Demo / fallback
    USE_FALLBACK_IF_EMPTY: bool = os.getenv("USE_FALLBACK_IF_EMPTY", "true").lower() == "true"


settings = Settings()

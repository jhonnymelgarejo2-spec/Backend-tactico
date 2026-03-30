# app/config/config.py

import os


class Config:
    SYSTEM_NAME = "JHONNY_ELITE_PRO"
    SYSTEM_VERSION = "1.0.0"
    SYSTEM_MODE = "LIVE_SCAN"

    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "10000"))

    SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))
    PUBLISH_MAX_SIGNALS = int(os.getenv("PUBLISH_MAX_SIGNALS", "6"))
    SCAN_MAX_HOT_MATCHES = int(os.getenv("SCAN_MAX_HOT_MATCHES", "10"))

    MINUTE_MIN_OPERABLE = int(os.getenv("MINUTE_MIN_OPERABLE", "15"))
    MINUTE_MAX_OPERABLE = int(os.getenv("MINUTE_MAX_OPERABLE", "88"))

    DEFAULT_PROB_REAL = float(os.getenv("DEFAULT_PROB_REAL", "0.75"))
    DEFAULT_PROB_IMPLICITA = float(os.getenv("DEFAULT_PROB_IMPLICITA", "0.54"))
    DEFAULT_ODD = float(os.getenv("DEFAULT_ODD", "0.0"))
    DEFAULT_MOMENTUM = os.getenv("DEFAULT_MOMENTUM", "MEDIO")

    ODDS_PROVIDER = os.getenv("ODDS_PROVIDER", "odds_api_io").strip().lower()

    FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
    FOOTBALL_API_URL = os.getenv(
        "FOOTBALL_API_URL",
        "https://v3.football.api-sports.io/fixtures?live=all",
    ).strip()

    THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY", "").strip()
    ODDS_API_IO_KEY = os.getenv("ODDS_API_IO_KEY", "").strip()
    ODDS_API_IO_BASE_URL = os.getenv(
        "ODDS_API_IO_BASE_URL",
        "https://api.odds-api.io/v3",
    ).strip()

    HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))


config = Config()

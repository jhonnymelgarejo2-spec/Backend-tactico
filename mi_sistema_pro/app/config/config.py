import os


class Settings:
    SYSTEM_NAME = "MI_SISTEMA_PRO"
    SYSTEM_VERSION = "V1"

    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", "8000"))

    SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))
    MAX_SIGNALS = int(os.getenv("MAX_SIGNALS", "6"))

    MINUTE_MIN_OPERABLE = int(os.getenv("MINUTE_MIN_OPERABLE", "15"))
    MINUTE_MAX_OPERABLE = int(os.getenv("MINUTE_MAX_OPERABLE", "88"))

    DEFAULT_ODD = float(os.getenv("DEFAULT_ODD", "0.0"))
    DEFAULT_PROB_REAL = float(os.getenv("DEFAULT_PROB_REAL", "0.0"))
    DEFAULT_PROB_IMPLICITA = float(os.getenv("DEFAULT_PROB_IMPLICITA", "0.0"))

    ALLOWED_MARKETS = {
        "OVER_NEXT_15_DYNAMIC",
        "OVER_MATCH_DYNAMIC",
        "UNDER_MATCH_DYNAMIC",
    }

    FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY", "").strip()
    FOOTBALL_API_URL = os.getenv("FOOTBALL_API_URL", "").strip()

    ODDS_PROVIDER = os.getenv("ODDS_PROVIDER", "none").strip().lower()
    ODDS_API_IO_KEY = os.getenv("ODDS_API_IO_KEY", "").strip()
    THE_ODDS_API_KEY = os.getenv("THE_ODDS_API_KEY", "").strip()


settings = Settings()

# app/config/config.py

import os


class Settings:
    # =========================================================
    # IDENTIDAD
    # =========================================================
    SYSTEM_NAME: str = os.getenv("SYSTEM_NAME", "JHONNY_ELITE")
    SYSTEM_VERSION: str = os.getenv("SYSTEM_VERSION", "V17")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    PORT: int = int(os.getenv("PORT", "10000"))

    # =========================================================
    # OPERACION GENERAL
    # =========================================================
    MINUTE_MIN_OPERABLE: int = int(os.getenv("MINUTE_MIN_OPERABLE", "15"))
    MINUTE_MAX_OPERABLE: int = int(os.getenv("MINUTE_MAX_OPERABLE", "88"))
    MAX_SIGNALS: int = int(os.getenv("MAX_SIGNALS", "6"))
    MAX_HOT_MATCHES: int = int(os.getenv("MAX_HOT_MATCHES", "10"))

    # =========================================================
    # VENTANAS
    # =========================================================
    PREMIUM_WINDOW_1_START: int = int(os.getenv("PREMIUM_WINDOW_1_START", "25"))
    PREMIUM_WINDOW_1_END: int = int(os.getenv("PREMIUM_WINDOW_1_END", "45"))
    PREMIUM_WINDOW_2_START: int = int(os.getenv("PREMIUM_WINDOW_2_START", "60"))
    PREMIUM_WINDOW_2_END: int = int(os.getenv("PREMIUM_WINDOW_2_END", "75"))

    SECONDARY_WINDOW_1_START: int = int(os.getenv("SECONDARY_WINDOW_1_START", "15"))
    SECONDARY_WINDOW_1_END: int = int(os.getenv("SECONDARY_WINDOW_1_END", "24"))
    SECONDARY_WINDOW_2_START: int = int(os.getenv("SECONDARY_WINDOW_2_START", "76"))
    SECONDARY_WINDOW_2_END: int = int(os.getenv("SECONDARY_WINDOW_2_END", "85"))

    # =========================================================
    # FILTROS GLOBALES DE SENAL
    # =========================================================
    MIN_CONFIDENCE_TO_OBSERVE: float = float(os.getenv("MIN_CONFIDENCE_TO_OBSERVE", "60"))
    MIN_CONFIDENCE_TO_PUBLISH: float = float(os.getenv("MIN_CONFIDENCE_TO_PUBLISH", "75"))
    MIN_VALUE_TO_OBSERVE: float = float(os.getenv("MIN_VALUE_TO_OBSERVE", "0.50"))
    MIN_VALUE_TO_PUBLISH: float = float(os.getenv("MIN_VALUE_TO_PUBLISH", "1.00"))

    # =========================================================
    # CUOTAS OPERABLES
    # =========================================================
    ODD_MIN_OPERABLE: float = float(os.getenv("ODD_MIN_OPERABLE", "1.50"))
    ODD_MAX_OPERABLE: float = float(os.getenv("ODD_MAX_OPERABLE", "2.10"))

    # =========================================================
    # HOT MATCH
    # =========================================================
    HOT_MATCH_MIN_MINUTE: int = int(os.getenv("HOT_MATCH_MIN_MINUTE", "15"))
    HOT_MATCH_MAX_MINUTE: int = int(os.getenv("HOT_MATCH_MAX_MINUTE", "88"))
    HOT_MATCH_MIN_XG: float = float(os.getenv("HOT_MATCH_MIN_XG", "1.00"))
    HOT_MATCH_MIN_SHOTS: int = int(os.getenv("HOT_MATCH_MIN_SHOTS", "8"))
    HOT_MATCH_MIN_SOT: int = int(os.getenv("HOT_MATCH_MIN_SOT", "2"))
    HOT_MATCH_MIN_DANGEROUS_ATTACKS: int = int(os.getenv("HOT_MATCH_MIN_DANGEROUS_ATTACKS", "14"))

    # =========================================================
    # OVER NEXT 15
    # =========================================================
    OVER_NEXT15_MIN_MINUTE: int = int(os.getenv("OVER_NEXT15_MIN_MINUTE", "20"))
    OVER_NEXT15_MAX_MINUTE: int = int(os.getenv("OVER_NEXT15_MAX_MINUTE", "86"))
    OVER_NEXT15_MIN_XG: float = float(os.getenv("OVER_NEXT15_MIN_XG", "1.40"))
    OVER_NEXT15_MIN_SOT: int = int(os.getenv("OVER_NEXT15_MIN_SOT", "3"))
    OVER_NEXT15_MIN_DANGEROUS_ATTACKS: int = int(os.getenv("OVER_NEXT15_MIN_DANGEROUS_ATTACKS", "16"))
    OVER_NEXT15_MIN_GOAL10: float = float(os.getenv("OVER_NEXT15_MIN_GOAL10", "0.35"))

    # =========================================================
    # OVER MATCH
    # =========================================================
    OVER_MATCH_MIN_MINUTE: int = int(os.getenv("OVER_MATCH_MIN_MINUTE", "15"))
    OVER_MATCH_MAX_MINUTE: int = int(os.getenv("OVER_MATCH_MAX_MINUTE", "80"))
    OVER_MATCH_MIN_XG: float = float(os.getenv("OVER_MATCH_MIN_XG", "1.50"))
    OVER_MATCH_MIN_SOT: int = int(os.getenv("OVER_MATCH_MIN_SOT", "3"))
    OVER_MATCH_MIN_DANGEROUS_ATTACKS: int = int(os.getenv("OVER_MATCH_MIN_DANGEROUS_ATTACKS", "16"))

    # =========================================================
    # UNDER MATCH
    # =========================================================
    UNDER_MATCH_MIN_MINUTE: int = int(os.getenv("UNDER_MATCH_MIN_MINUTE", "65"))
    UNDER_MATCH_MAX_MINUTE: int = int(os.getenv("UNDER_MATCH_MAX_MINUTE", "88"))
    UNDER_MATCH_MAX_XG: float = float(os.getenv("UNDER_MATCH_MAX_XG", "1.10"))
    UNDER_MATCH_MAX_SOT: int = int(os.getenv("UNDER_MATCH_MAX_SOT", "2"))
    UNDER_MATCH_MAX_DANGEROUS_ATTACKS: int = int(os.getenv("UNDER_MATCH_MAX_DANGEROUS_ATTACKS", "14"))
    UNDER_MATCH_MAX_GOAL10: float = float(os.getenv("UNDER_MATCH_MAX_GOAL10", "0.30"))

    # =========================================================
    # RIESGO / PUBLICACION
    # =========================================================
    DEFAULT_RISK_SCORE: float = float(os.getenv("DEFAULT_RISK_SCORE", "5.0"))
    MAX_RISK_TO_PUBLISH: float = float(os.getenv("MAX_RISK_TO_PUBLISH", "7.2"))
    REQUIRE_ODDS_VALIDATION_TO_PUBLISH: bool = (
        os.getenv("REQUIRE_ODDS_VALIDATION_TO_PUBLISH", "true").lower() == "true"
    )

    # =========================================================
    # API FOOTBALL
    # =========================================================
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

    # =========================================================
    # DEFAULTS
    # =========================================================
    DEFAULT_PROB_REAL: float = float(os.getenv("DEFAULT_PROB_REAL", "0.75"))
    DEFAULT_PROB_IMPLICITA: float = float(os.getenv("DEFAULT_PROB_IMPLICITA", "0.54"))
    DEFAULT_ODD: float = float(os.getenv("DEFAULT_ODD", "1.85"))
    DEFAULT_MOMENTUM: str = os.getenv("DEFAULT_MOMENTUM", "MEDIO")

    # =========================================================
    # DEMO / FALLBACK
    # =========================================================
    USE_FALLBACK_IF_EMPTY: bool = os.getenv("USE_FALLBACK_IF_EMPTY", "true").lower() == "true"

    # =========================================================
    # HELPERS
    # =========================================================
    def is_premium_window(self, minute: int) -> bool:
        return (
            self.PREMIUM_WINDOW_1_START <= minute <= self.PREMIUM_WINDOW_1_END
            or self.PREMIUM_WINDOW_2_START <= minute <= self.PREMIUM_WINDOW_2_END
        )

    def is_secondary_window(self, minute: int) -> bool:
        return (
            self.SECONDARY_WINDOW_1_START <= minute <= self.SECONDARY_WINDOW_1_END
            or self.SECONDARY_WINDOW_2_START <= minute <= self.SECONDARY_WINDOW_2_END
        )

    def is_operable_minute(self, minute: int) -> bool:
        return self.MINUTE_MIN_OPERABLE <= minute <= self.MINUTE_MAX_OPERABLE

    def is_operable_odd(self, odd: float) -> bool:
        return self.ODD_MIN_OPERABLE <= odd <= self.ODD_MAX_OPERABLE


settings = Settings()

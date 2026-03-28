# config.py

"""
Configuración central de JHONNY_ELITE V16
----------------------------------------
Aquí viven los thresholds y reglas maestras del sistema.

Objetivo:
- evitar números mágicos repartidos por todo el proyecto
- facilitar calibración
- dejar una sola fuente de verdad para umbrales
"""


# =========================================================
# IDENTIDAD DEL SISTEMA
# =========================================================
SYSTEM_NAME = "JHONNY_ELITE"
SYSTEM_VERSION = "V16"
SYSTEM_MODE = "GOALS_ONLY"


# =========================================================
# MERCADOS OFICIALES
# =========================================================
MARKETS_ALLOWED = {
    "OVER_NEXT_15_DYNAMIC",
    "OVER_MATCH_DYNAMIC",
    "UNDER_MATCH_DYNAMIC",
}


# =========================================================
# REGLAS GLOBALES DE OPERACION
# =========================================================
MINUTE_MIN_OPERABLE = 15
MINUTE_MAX_OPERABLE = 88

MIN_CONFIDENCE_GLOBAL = 68.0
MIN_VALUE_GLOBAL = 1.0
MAX_RISK_SCORE_GLOBAL = 7.2

ODD_MIN_GLOBAL = 1.50
ODD_MAX_GLOBAL = 2.10

MIN_RANKING_SCORE_GLOBAL = 140.0


# =========================================================
# VENTANAS DE OPERACION
# =========================================================
WINDOW_PREMIUM_1_START = 25
WINDOW_PREMIUM_1_END = 45

WINDOW_PREMIUM_2_START = 60
WINDOW_PREMIUM_2_END = 85

WINDOW_SECONDARY_1_START = 15
WINDOW_SECONDARY_1_END = 24

WINDOW_SECONDARY_2_START = 46
WINDOW_SECONDARY_2_END = 59

WINDOW_SECONDARY_3_START = 86
WINDOW_SECONDARY_3_END = 88


# =========================================================
# OVER NEXT 15
# =========================================================
OVER_NEXT_15_MIN_CONFIDENCE = 72.0
OVER_NEXT_15_MIN_VALUE = 1.2
OVER_NEXT_15_MIN_MINUTE = 20
OVER_NEXT_15_MAX_MINUTE = 86
OVER_NEXT_15_MIN_TACTICAL_SCORE = 12.0
OVER_NEXT_15_MIN_GOAL_PROB_10 = 45.0
OVER_NEXT_15_MIN_ODD = 1.55


# =========================================================
# OVER MATCH
# =========================================================
OVER_MATCH_MIN_CONFIDENCE = 74.0
OVER_MATCH_MIN_VALUE = 1.2
OVER_MATCH_MIN_MINUTE = 15
OVER_MATCH_MAX_MINUTE = 79
OVER_MATCH_MIN_TACTICAL_SCORE = 12.0
OVER_MATCH_MIN_ODD = 1.55


# =========================================================
# UNDER MATCH
# =========================================================
UNDER_MATCH_MIN_CONFIDENCE = 76.0
UNDER_MATCH_MIN_VALUE = 1.5
UNDER_MATCH_MIN_MINUTE = 65
UNDER_MATCH_MAX_MINUTE = 88

UNDER_MATCH_MAX_XG = 1.35
UNDER_MATCH_MAX_SHOTS_ON_TARGET = 2
UNDER_MATCH_MAX_DANGEROUS_ATTACKS = 15
UNDER_MATCH_MAX_GOAL_PROB_10 = 40.0

UNDER_MATCH_STRICT_MAX_XG = 1.30
UNDER_MATCH_STRICT_MAX_SHOTS_ON_TARGET = 2
UNDER_MATCH_STRICT_MAX_DANGEROUS_ATTACKS = 15
UNDER_MATCH_STRICT_MAX_GOAL_PROB_10 = 40.0

UNDER_MATCH_MIN_ODD = 1.60


# =========================================================
# FILTROS DE VALUE
# =========================================================
VALUE_SCORE_MIN_WEAK = 4.0
VALUE_SCORE_MIN_MEDIUM = 6.0
VALUE_SCORE_MIN_STRONG = 8.0
VALUE_SCORE_MIN_ELITE = 10.0

EDGE_MIN_POSITIVE = 0.01
EDGE_MIN_STANDARD = 1.0
EDGE_MIN_STRICT = 8.0


# =========================================================
# FILTROS DE RIESGO
# =========================================================
RISK_LEVEL_BLOCKED = {"NO_APOSTAR"}
RISK_LEVEL_RESTRICTED = {"RIESGO_ALTO"}

RISK_SCORE_LOW_MAX = 4.5
RISK_SCORE_MEDIUM_MAX = 7.2
RISK_SCORE_HIGH_MAX = 8.5


# =========================================================
# IA / AJUSTE FINAL
# =========================================================
AI_CONFIDENCE_MIN = 58.0
AI_DECISION_SCORE_SOFT = 78.0
AI_DECISION_SCORE_STANDARD = 98.0
AI_DECISION_SCORE_STRONG = 125.0

AI_RECOMMENDATIONS_ALLOWED = {
    "APOSTAR_FUERTE",
    "APOSTAR",
    "APOSTAR_SUAVE",
    "OBSERVAR",
    "NO_APOSTAR",
}


# =========================================================
# RANKING / PUBLICACION
# =========================================================
SIGNAL_SCORE_MIN_NORMAL = 95.0
SIGNAL_SCORE_MIN_HIGH = 110.0
SIGNAL_SCORE_MIN_TOP = 170.0
SIGNAL_SCORE_MIN_ELITE = 230.0

RANKING_SCORE_MIN_TOP = 140.0
RANKING_SCORE_PUBLISH_2 = 240.0
RANKING_SCORE_PUBLISH_1 = 340.0

PUBLISH_MAX_SIGNALS = 6
PUBLISH_MAX_OVERS = 3
PUBLISH_MAX_UNDERS = 3


# =========================================================
# STAKE / BANKROLL
# =========================================================
STAKE_DEFAULT_PCT = 2.0
STAKE_MEDIUM_PCT = 3.2
STAKE_STRONG_PCT = 4.0
STAKE_ELITE_PCT = 4.9

MAX_OPERACIONES_DIA = 3
STOP_LOSS_CONSECUTIVO = 2


# =========================================================
# HISTORIAL / APRENDIZAJE
# =========================================================
HISTORY_DEFAULT_STAKE = 1.0
HISTORY_MAX_RETURNED_ITEMS = 100
HISTORY_STATS_RECENT_LIMIT = 50


# =========================================================
# FETCHERS / TIMEOUTS
# =========================================================
HTTP_TIMEOUT_SECONDS = 20
SCAN_MAX_HOT_MATCHES = 10


# =========================================================
# DEMO / FALLBACK
# =========================================================
DEFAULT_PROB_REAL = 0.75
DEFAULT_PROB_IMPLICITA = 0.54
DEFAULT_ODD = 1.85
DEFAULT_MOMENTUM = "MEDIO"


# =========================================================
# HELPERS OPCIONALES
# =========================================================
def is_premium_window(minute: int) -> bool:
    return (
        WINDOW_PREMIUM_1_START <= minute <= WINDOW_PREMIUM_1_END
        or WINDOW_PREMIUM_2_START <= minute <= WINDOW_PREMIUM_2_END
    )


def is_secondary_window(minute: int) -> bool:
    return (
        WINDOW_SECONDARY_1_START <= minute <= WINDOW_SECONDARY_1_END
        or WINDOW_SECONDARY_2_START <= minute <= WINDOW_SECONDARY_2_END
        or WINDOW_SECONDARY_3_START <= minute <= WINDOW_SECONDARY_3_END
    )


def is_operable_minute(minute: int) -> bool:
    return MINUTE_MIN_OPERABLE <= minute <= MINUTE_MAX_OPERABLE

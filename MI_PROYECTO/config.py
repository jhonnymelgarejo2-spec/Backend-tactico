# config.py

"""
Configuración central de JHONNY_ELITE V16
Versión calibrada para generación de señales (modo activo)
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
# REGLAS GLOBALES (AJUSTADAS 🔥)
# =========================================================
MINUTE_MIN_OPERABLE = 15
MINUTE_MAX_OPERABLE = 88

# 🔥 BAJADO para que empiece a generar señales
MIN_CONFIDENCE_GLOBAL = 40.0
MIN_VALUE_GLOBAL = 0.01
MAX_RISK_SCORE_GLOBAL = 8.5

ODD_MIN_GLOBAL = 1.40
ODD_MAX_GLOBAL = 2.50

MIN_RANKING_SCORE_GLOBAL = 80.0


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
# OVER NEXT 15 (CLAVE 🔥)
# =========================================================
OVER_NEXT_15_MIN_CONFIDENCE = 55.0
OVER_NEXT_15_MIN_VALUE = 0.01
OVER_NEXT_15_MIN_MINUTE = 20
OVER_NEXT_15_MAX_MINUTE = 88

# 🔥 bajado para activar señales
OVER_NEXT_15_MIN_TACTICAL_SCORE = 8.0
OVER_NEXT_15_MIN_GOAL_PROB_10 = 18.0
OVER_NEXT_15_MIN_ODD = 1.40


# =========================================================
# OVER MATCH
# =========================================================
OVER_MATCH_MIN_CONFIDENCE = 60.0
OVER_MATCH_MIN_VALUE = 0.01
OVER_MATCH_MIN_MINUTE = 15
OVER_MATCH_MAX_MINUTE = 85

OVER_MATCH_MIN_TACTICAL_SCORE = 8.0
OVER_MATCH_MIN_ODD = 1.40


# =========================================================
# UNDER MATCH
# =========================================================
UNDER_MATCH_MIN_CONFIDENCE = 60.0
UNDER_MATCH_MIN_VALUE = 0.01
UNDER_MATCH_MIN_MINUTE = 60
UNDER_MATCH_MAX_MINUTE = 88

UNDER_MATCH_MAX_XG = 1.8
UNDER_MATCH_MAX_SHOTS_ON_TARGET = 4
UNDER_MATCH_MAX_DANGEROUS_ATTACKS = 30
UNDER_MATCH_MAX_GOAL_PROB_10 = 55.0

UNDER_MATCH_STRICT_MAX_XG = 1.6
UNDER_MATCH_STRICT_MAX_SHOTS_ON_TARGET = 3
UNDER_MATCH_STRICT_MAX_DANGEROUS_ATTACKS = 25
UNDER_MATCH_STRICT_MAX_GOAL_PROB_10 = 50.0

UNDER_MATCH_MIN_ODD = 1.50


# =========================================================
# VALUE (SUAVIZADO)
# =========================================================
VALUE_SCORE_MIN_WEAK = 2.0
VALUE_SCORE_MIN_MEDIUM = 4.0
VALUE_SCORE_MIN_STRONG = 6.0
VALUE_SCORE_MIN_ELITE = 8.0

EDGE_MIN_POSITIVE = 0.01
EDGE_MIN_STANDARD = 0.5
EDGE_MIN_STRICT = 4.0


# =========================================================
# RIESGO (MENOS RESTRICTIVO)
# =========================================================
RISK_LEVEL_BLOCKED = {"NO_APOSTAR"}
RISK_LEVEL_RESTRICTED = set()

RISK_SCORE_LOW_MAX = 5.5
RISK_SCORE_MEDIUM_MAX = 7.5
RISK_SCORE_HIGH_MAX = 9.0


# =========================================================
# IA (SUAVIZADA)
# =========================================================
AI_CONFIDENCE_MIN = 45.0
AI_DECISION_SCORE_SOFT = 60.0
AI_DECISION_SCORE_STANDARD = 80.0
AI_DECISION_SCORE_STRONG = 100.0

AI_RECOMMENDATIONS_ALLOWED = {
    "APOSTAR_FUERTE",
    "APOSTAR",
    "APOSTAR_SUAVE",
    "OBSERVAR",
}


# =========================================================
# RANKING (BAJADO)
# =========================================================
SIGNAL_SCORE_MIN_NORMAL = 60.0
SIGNAL_SCORE_MIN_HIGH = 80.0
SIGNAL_SCORE_MIN_TOP = 120.0
SIGNAL_SCORE_MIN_ELITE = 160.0

RANKING_SCORE_MIN_TOP = 80.0
RANKING_SCORE_PUBLISH_2 = 140.0
RANKING_SCORE_PUBLISH_1 = 220.0

PUBLISH_MAX_SIGNALS = 6
PUBLISH_MAX_OVERS = 4
PUBLISH_MAX_UNDERS = 2


# =========================================================
# STAKE
# =========================================================
STAKE_DEFAULT_PCT = 2.0
STAKE_MEDIUM_PCT = 3.0
STAKE_STRONG_PCT = 4.0
STAKE_ELITE_PCT = 5.0

MAX_OPERACIONES_DIA = 6
STOP_LOSS_CONSECUTIVO = 3


# =========================================================
# HISTORIAL
# =========================================================
HISTORY_DEFAULT_STAKE = 1.0
HISTORY_MAX_RETURNED_ITEMS = 100
HISTORY_STATS_RECENT_LIMIT = 50


# =========================================================
# FETCHERS
# =========================================================
HTTP_TIMEOUT_SECONDS = 20
SCAN_MAX_HOT_MATCHES = 15


# =========================================================
# DEMO
# =========================================================
DEFAULT_PROB_REAL = 0.75
DEFAULT_PROB_IMPLICITA = 0.54
DEFAULT_ODD = 1.85
DEFAULT_MOMENTUM = "MEDIO"


# =========================================================
# HELPERS
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

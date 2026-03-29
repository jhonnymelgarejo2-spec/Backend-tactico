from typing import Dict, Any


# =========================================================
# HELPERS
# =========================================================
def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _upper(value: Any) -> str:
    return _safe_text(value).upper()


# =========================================================
# MOTOR DE GOL INMINENTE
# =========================================================
def evaluar_gol_inminente(partido: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detecta si hay probabilidad real de gol inminente.
    No predice resultado, solo intensidad ofensiva inmediata.
    """

    minuto = _safe_int(partido.get("minuto"), 0)

    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)

    pressure_score = _safe_float((partido.get("goal_pressure") or {}).get("pressure_score"), 0.0)

    predictor = partido.get("goal_predictor") or {}
    goal_prob_5 = _safe_float(predictor.get("goal_next_5_prob"), 0.0)
    goal_prob_10 = _safe_float(predictor.get("goal_next_10_prob"), 0.0)

    momentum = _upper(partido.get("momentum"))

    # =========================================================
    # SCORING
    # =========================================================
    score = 0.0

    score += xg * 12
    score += shots * 0.6
    score += shots_on_target * 5
    score += dangerous_attacks * 0.4
    score += pressure_score * 2.5
    score += goal_prob_5 * 0.5
    score += goal_prob_10 * 0.4

    if momentum == "MUY ALTO":
        score += 10
    elif momentum == "ALTO":
        score += 6

    if 70 <= minuto <= 85:
        score += 6
    elif 25 <= minuto <= 45:
        score += 4

    score = round(score, 2)

    # =========================================================
    # CLASIFICACIÓN
    # =========================================================
    gol_inminente = False
    nivel = "BAJO"
    confianza = 0.0
    razon = "Sin presión ofensiva clara"

    if score >= 95:
        gol_inminente = True
        nivel = "MUY_ALTO"
        confianza = 0.92
        razon = "Presión extrema + múltiples indicadores ofensivos"
    elif score >= 75:
        gol_inminente = True
        nivel = "ALTO"
        confianza = 0.82
        razon = "Alta probabilidad de gol por volumen ofensivo"
    elif score >= 55:
        gol_inminente = True
        nivel = "MEDIO"
        confianza = 0.72
        razon = "Contexto ofensivo favorable"
    elif score >= 40:
        nivel = "BAJO_MEDIO"
        confianza = 0.60
        razon = "Presión moderada sin confirmación clara"

    # =========================================================
    # OUTPUT
    # =========================================================
    return {
        "gol_inminente": gol_inminente,
        "gol_inminente_score": score,
        "gol_inminente_nivel": nivel,
        "gol_inminente_confianza": round(confianza, 2),
        "gol_inminente_razon": razon,
    }

from typing import Dict, Any


def _f(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _i(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def evaluar_gol_inminente(match: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    xg = _f(match.get("xG"), 0)
    shots = _i(match.get("shots"), 0)
    shots_on_target = _i(match.get("shots_on_target"), 0)
    dangerous_attacks = _i(match.get("dangerous_attacks"), 0)

    goal_predictor = match.get("goal_predictor", {}) or {}
    goal5 = _f(goal_predictor.get("goal_next_5_prob"), 0)
    goal10 = _f(goal_predictor.get("goal_next_10_prob"), 0)

    confidence = _f(signal.get("confidence"), 0)

    score = 0

    # Producción ofensiva real
    if xg >= 2.5:
        score += 25
    elif xg >= 1.8:
        score += 15

    if shots_on_target >= 5:
        score += 20
    elif shots_on_target >= 3:
        score += 10

    if dangerous_attacks >= 30:
        score += 20
    elif dangerous_attacks >= 20:
        score += 10

    # Predictor
    if goal5 >= 0.65:
        score += 20
    elif goal5 >= 0.50:
        score += 10

    if goal10 >= 0.75:
        score += 15
    elif goal10 >= 0.60:
        score += 8

    # Confianza
    if confidence >= 85:
        score += 10

    # Nivel
    if score >= 80:
        level = "CRITICO"
        reason = "Presión ofensiva extrema + alta probabilidad inmediata"
    elif score >= 55:
        level = "ALTO"
        reason = "Presión sostenida con buena ventana de gol"
    elif score >= 35:
        level = "MEDIO"
        reason = "Ataque presente pero no dominante"
    else:
        level = "BAJO"
        reason = "Sin condiciones reales de gol inmediato"

    return {
        "goal_imminent_score": round(score, 2),
        "goal_imminent_level": level,
        "goal_imminent_reason": reason,
    }

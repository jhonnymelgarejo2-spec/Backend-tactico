# goal_imminent_engine.py

from typing import Dict


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


def _u(value) -> str:
    return str(value or "").strip().upper()


def evaluar_gol_inminente(match: Dict) -> Dict:
    minuto = _i(match.get("minuto"), 0)
    ml = _i(match.get("marcador_local"), 0)
    mv = _i(match.get("marcador_visitante"), 0)
    diff = abs(ml - mv)

    xg = _f(match.get("xG"), 0)
    shots = _f(match.get("shots"), 0)
    shots_on_target = _f(match.get("shots_on_target"), 0)
    dangerous_attacks = _f(match.get("dangerous_attacks"), 0)
    momentum = _u(match.get("momentum"))

    goal_pressure = match.get("goal_pressure", {}) or {}
    goal_predictor = match.get("goal_predictor", {}) or {}
    chaos = match.get("chaos", {}) or {}

    pressure_score = _f(goal_pressure.get("pressure_score"), 0)
    predictor_score = _f(goal_predictor.get("predictor_score"), 0)
    goal5 = _f(goal_predictor.get("goal_next_5_prob"), 0)
    goal10 = _f(goal_predictor.get("goal_next_10_prob"), 0)
    chaos_score = _f(chaos.get("chaos_score"), 0)

    score = 0.0
    reasons = []

    # =========================
    # FACTORES QUE SUBEN SCORE
    # =========================
    if pressure_score >= 7:
        score += 18
        reasons.append("presion ofensiva alta")

    if predictor_score >= 5:
        score += 10
        reasons.append("predictor activo")

    if goal5 >= 0.50:
        score += 18
        reasons.append("alta ventana de gol a 5 min")
    elif goal5 >= 0.35:
        score += 10
        reasons.append("ventana media de gol a 5 min")

    if goal10 >= 0.65:
        score += 10
        reasons.append("continuidad ofensiva a 10 min")

    if xg >= 1.5:
        score += 12
        reasons.append("xG elevado")

    if shots_on_target >= 3:
        score += 10
        reasons.append("tiros a puerta suficientes")

    if dangerous_attacks >= 18:
        score += 10
        reasons.append("muchos ataques peligrosos")

    if momentum in ("ALTO", "MUY ALTO", "EXPLOSIVO", "CAOS"):
        score += 8
        reasons.append("momentum fuerte")

    if 70 <= minuto <= 88 and diff <= 1:
        score += 8
        reasons.append("tramo final con marcador abierto")

    if minuto >= 80 and diff == 0:
        score += 6
        reasons.append("empate tardio con alta sensibilidad")

    # =========================
    # FACTORES QUE BAJAN SCORE
    # =========================
    if minuto < 12:
        score -= 12
        reasons.append("tramo demasiado temprano")

    if shots_on_target == 0 and xg < 0.9:
        score -= 14
        reasons.append("sin produccion real")

    if dangerous_attacks < 8 and pressure_score < 5:
        score -= 8
        reasons.append("ritmo ofensivo flojo")

    if chaos_score >= 12 and pressure_score < 7:
        score -= 10
        reasons.append("caos sin direccion clara")

    if momentum == "BAJO":
        score -= 8
        reasons.append("momentum bajo")

    score = max(0, min(100, round(score, 2)))

    if score >= 80:
        level = "CRITICO"
    elif score >= 60:
        level = "ALTO"
    elif score >= 40:
        level = "MEDIO"
    else:
        level = "BAJO"

    return {
        "goal_imminent_score": score,
        "goal_imminent_level": level,
        "goal_imminent_reason": ", ".join(reasons) if reasons else "sin señales claras"
}

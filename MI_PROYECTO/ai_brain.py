from typing import Dict
from chaos_detector import detect_chaos
from goal_imminent_engine import evaluar_gol_inminente


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


# =========================================================
# LECTURA CONTEXTO PARTIDO
# =========================================================
def leer_contexto_partido(match: Dict) -> Dict:
    minuto = _i(match.get("minuto"), 0)
    ml = _i(match.get("marcador_local"), 0)
    mv = _i(match.get("marcador_visitante"), 0)
    diff = abs(ml - mv)

    xg = _f(match.get("xG"), 0)
    momentum = _u(match.get("momentum"))

    goal_pressure = match.get("goal_pressure", {}) or {}
    goal_predictor = match.get("goal_predictor", {}) or {}
    chaos = match.get("chaos", {}) or {}

    pressure_score = _f(goal_pressure.get("pressure_score"), 0)
    predictor_score = _f(goal_predictor.get("predictor_score"), 0)
    goal5 = _f(goal_predictor.get("goal_next_5_prob"), 0)
    goal10 = _f(goal_predictor.get("goal_next_10_prob"), 0)
    chaos_score = _f(chaos.get("chaos_score"), 0)

    shots_on_target = _f(match.get("shots_on_target"), 0)
    dangerous_attacks = _f(match.get("dangerous_attacks"), 0)

    if minuto >= 78 and xg < 1.1 and pressure_score < 5:
        return {"ai_state": "PARTIDO_MUERTO", "ai_score": 20, "ai_reason": "Sin impulso ofensivo"}

    if minuto >= 75 and diff >= 1 and pressure_score < 6:
        return {"ai_state": "CIERRE_TACTICO", "ai_score": 30, "ai_reason": "Gestión de resultado"}

    if dangerous_attacks >= 18 and shots_on_target == 0:
        return {"ai_state": "PRESION_FALSA", "ai_score": 35, "ai_reason": "Ataque sin peligro real"}

    if chaos_score >= 12 and xg < 1.2:
        return {"ai_state": "CAOS_PELIGROSO", "ai_score": 40, "ai_reason": "Caos sin dirección"}

    if chaos_score >= 9 and pressure_score >= 7 and (goal5 >= 0.55 or goal10 >= 0.70):
        return {"ai_state": "CAOS_UTIL", "ai_score": 75, "ai_reason": "Caos con ventana real"}

    if xg >= 1.5 and pressure_score >= 7 and predictor_score >= 5 and shots_on_target >= 2:
        return {"ai_state": "CONTROL_REAL", "ai_score": 82, "ai_reason": "Dominio ofensivo real"}

    return {"ai_state": "NEUTRO", "ai_score": 55, "ai_reason": "Contexto mixto"}


# =========================================================
# AJUSTE IA
# =========================================================
def evaluar_ajuste_para_senal(match: Dict, signal: Dict) -> Dict:
    lectura = leer_contexto_partido(match)
    chaos_read = detect_chaos(match)
    goal_read = evaluar_gol_inminente(match, signal)

    ai_state = lectura["ai_state"]
    ai_score = _f(lectura["ai_score"], 55)

    market = _u(signal.get("market"))
    confidence = _f(signal.get("confidence"), 0)

    ajuste = 0

    is_over = "OVER" in market or market == "NEXT_GOAL"
    is_hold = "RESULT_HOLDS" in market or "HOLD" in market

    if is_over:
        if ai_state in ("CONTROL_REAL", "CAOS_UTIL"):
            ajuste += 8
        elif ai_state in ("PRESION_FALSA", "CIERRE_TACTICO", "PARTIDO_MUERTO"):
            ajuste -= 12

        if goal_read["goal_imminent_level"] == "CRITICO":
            ajuste += 12
        elif goal_read["goal_imminent_level"] == "ALTO":
            ajuste += 7
        elif goal_read["goal_imminent_level"] == "BAJO":
            ajuste -= 8

    if is_hold:
        if ai_state in ("CIERRE_TACTICO", "PARTIDO_MUERTO"):
            ajuste += 7
        elif ai_state in ("CONTROL_REAL", "CAOS_UTIL"):
            ajuste -= 8

        if goal_read["goal_imminent_level"] in ("ALTO", "CRITICO"):
            ajuste -= 10

    if chaos_read["chaos_level"] == "MEDIO":
        ajuste -= chaos_read["chaos_confidence_penalty"]

    if chaos_read["chaos_level"] == "ALTO":
        ajuste -= chaos_read["chaos_confidence_penalty"] * 2

    adjusted_confidence = max(25, min(95, confidence + ajuste))

    return {
        "ai_state": ai_state,
        "ai_score": ai_score,
        "ai_reason": lectura["ai_reason"],
        "ai_confidence_adjustment": ajuste,
        "ai_confidence_final": round(adjusted_confidence, 2),
        "chaos_level": chaos_read["chaos_level"],
        "goal_imminent_score": goal_read["goal_imminent_score"],
        "goal_imminent_level": goal_read["goal_imminent_level"],
    }


# =========================================================
# DECISIÓN IA (NO VISUAL FINAL)
# =========================================================
def decision_final_ia(match: Dict, signal: Dict) -> Dict:
    lectura = evaluar_ajuste_para_senal(match, signal)

    signal_score = _f(signal.get("signal_score"), 0)
    value_score = _f(signal.get("value_score", 0), 0)
    risk_score = _f(signal.get("risk_score"), 0)
    ai_conf = _f(lectura.get("ai_confidence_final"), 0)
    goal_score = _f(lectura.get("goal_imminent_score"), 0)

    decision_score = (
        signal_score * 0.30 +
        ai_conf * 0.35 +
        value_score * 4.0 -
        risk_score * 3.2 +
        goal_score * 0.12
    )

    if lectura["chaos_level"] == "ALTO":
        decision_score -= 18

    decision_score = round(decision_score, 2)

    if decision_score >= 125 and risk_score <= 5:
        rec = "APOSTAR_FUERTE"
    elif decision_score >= 98 and risk_score <= 7:
        rec = "APOSTAR"
    elif decision_score >= 78:
        rec = "APOSTAR_SUAVE"
    elif decision_score >= 58:
        rec = "OBSERVAR"
    else:
        rec = "NO_APOSTAR"

    return {
        "ai_state": lectura["ai_state"],
        "ai_score": lectura["ai_score"],
        "ai_confidence_final": lectura["ai_confidence_final"],
        "ai_decision_score": decision_score,
        "ai_recommendation": rec,
        "goal_imminent_score": lectura["goal_imminent_score"],
        "goal_imminent_level": lectura["goal_imminent_level"],
    }

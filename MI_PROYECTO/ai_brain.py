# ai_brain.py

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

    shots = _f(match.get("shots"), 0)
    shots_on_target = _f(match.get("shots_on_target"), 0)
    dangerous_attacks = _f(match.get("dangerous_attacks"), 0)

    # 1. partido muerto
    if minuto >= 78 and xg < 1.1 and momentum in ("BAJO", "MEDIO") and pressure_score < 5:
        return {
            "ai_state": "PARTIDO_MUERTO",
            "ai_score": 20,
            "ai_reason": "Poco impulso ofensivo en tramo final"
        }

    # 2. cierre táctico
    if minuto >= 75 and diff >= 1 and momentum in ("BAJO", "MEDIO") and pressure_score < 6:
        return {
            "ai_state": "CIERRE_TACTICO",
            "ai_score": 30,
            "ai_reason": "El partido parece entrar en gestión de resultado"
        }

    # 3. presión falsa
    if dangerous_attacks >= 18 and shots_on_target == 0 and xg < 0.9:
        return {
            "ai_state": "PRESION_FALSA",
            "ai_score": 35,
            "ai_reason": "Mucho ataque aparente pero sin peligro real"
        }

    # 4. caos peligroso
    if chaos_score >= 12 and pressure_score < 6 and xg < 1.2:
        return {
            "ai_state": "CAOS_PELIGROSO",
            "ai_score": 40,
            "ai_reason": "Partido roto pero sin dirección ofensiva clara"
        }

    # 5. caos útil
    if chaos_score >= 9 and pressure_score >= 7 and (goal5 >= 0.55 or goal10 >= 0.70):
        return {
            "ai_state": "CAOS_UTIL",
            "ai_score": 75,
            "ai_reason": "Caos acompañado de presión y ventana real de gol"
        }

    # 6. control real
    if xg >= 1.5 and pressure_score >= 7 and predictor_score >= 5 and shots_on_target >= 2:
        return {
            "ai_state": "CONTROL_REAL",
            "ai_score": 82,
            "ai_reason": "Presión ofensiva respaldada por producción real"
        }

    # 7. partido trampa
    if minuto >= 80 and pressure_score >= 7 and goal5 < 0.35:
        return {
            "ai_state": "PARTIDO_TRAMPA",
            "ai_score": 18,
            "ai_reason": "Presión tardía poco confiable para entrar"
        }

    return {
        "ai_state": "NEUTRO",
        "ai_score": 55,
        "ai_reason": "Contexto mixto sin lectura extrema"
    }


def evaluar_ajuste_para_senal(match: Dict, signal: Dict) -> Dict:
    lectura = leer_contexto_partido(match)
    chaos_read = detect_chaos(match)
    goal_read = evaluar_gol_inminente(match)

    ai_state = lectura["ai_state"]
    ai_score = _f(lectura["ai_score"], 55)

    market = _u(signal.get("market"))
    confidence = _f(signal.get("confidence"), 0)

    ajuste = 0
    fit = "NEUTRO"
    fit_reason = "Sin ajuste especial"

    is_over = "OVER" in market or market == "NEXT_GOAL"
    is_hold = "RESULT_HOLDS" in market or "HOLD" in market

    # =========================================================
    # AJUSTE POR TIPO DE MERCADO
    # =========================================================
    if is_over:
        if ai_state in ("CONTROL_REAL", "CAOS_UTIL"):
            ajuste += 8
            fit = "ALINEADA"
            fit_reason = "La señal ofensiva encaja con la lectura IA"
        elif ai_state in ("PRESION_FALSA", "CIERRE_TACTICO", "PARTIDO_MUERTO", "PARTIDO_TRAMPA", "CAOS_PELIGROSO"):
            ajuste -= 12
            fit = "DESALINEADA"
            fit_reason = "La señal ofensiva no encaja con el contexto actual"

        if goal_read["goal_imminent_level"] == "CRITICO":
            ajuste += 12
            fit = "ALINEADA"
            fit_reason = "Ventana crítica de gol inminente"
        elif goal_read["goal_imminent_level"] == "ALTO":
            ajuste += 7
            fit = "ALINEADA"
            fit_reason = "Ventana alta de gol inminente"
        elif goal_read["goal_imminent_level"] == "BAJO":
            ajuste -= 8

    if is_hold:
        if ai_state in ("CIERRE_TACTICO", "PARTIDO_MUERTO"):
            ajuste += 7
            fit = "ALINEADA"
            fit_reason = "El hold encaja con ritmo controlado o cierre del partido"
        elif ai_state in ("CONTROL_REAL", "CAOS_UTIL"):
            ajuste -= 8
            fit = "DESALINEADA"
            fit_reason = "El hold choca con una lectura ofensiva fuerte"

        if goal_read["goal_imminent_level"] in ("ALTO", "CRITICO"):
            ajuste -= 10
            fit = "DESALINEADA"
            fit_reason = "El hold choca con una ventana real de gol"

    # =========================================================
    # AJUSTE POR CHAOS DETECTOR
    # =========================================================
    if chaos_read["chaos_level"] == "MEDIO":
        ajuste -= chaos_read["chaos_confidence_penalty"]
        if fit == "NEUTRO":
            fit = "RIESGO_MEDIO"
            fit_reason = f"Se detecta volatilidad: {chaos_read['chaos_reason']}"

    elif chaos_read["chaos_level"] == "ALTO":
        ajuste -= chaos_read["chaos_confidence_penalty"]
        fit = "RIESGO_ALTO"
        fit_reason = f"Partido caótico: {chaos_read['chaos_reason']}"

    adjusted_confidence = max(25, min(95, confidence + ajuste))

    return {
        "ai_state": ai_state,
        "ai_score": ai_score,
        "ai_reason": lectura["ai_reason"],
        "ai_fit": fit,
        "ai_fit_reason": fit_reason,
        "ai_confidence_adjustment": ajuste,
        "ai_confidence_final": round(adjusted_confidence, 2),
        "chaos_level": chaos_read["chaos_level"],
        "chaos_detector_score": chaos_read["chaos_detector_score"],
        "chaos_reason": chaos_read["chaos_reason"],
        "chaos_block_signal": chaos_read["chaos_block_signal"],
        "chaos_confidence_penalty": chaos_read["chaos_confidence_penalty"],
        "goal_imminent_score": goal_read["goal_imminent_score"],
        "goal_imminent_level": goal_read["goal_imminent_level"],
        "goal_imminent_reason": goal_read["goal_imminent_reason"],
    }


def decision_final_ia(match: Dict, signal: Dict) -> Dict:
    lectura = evaluar_ajuste_para_senal(match, signal)

    signal_score = _f(signal.get("signal_score"), 0)
    value_score = _f(signal.get("value_score", signal.get("value", 0)), 0)
    risk_score = _f(signal.get("risk_score"), 0)
    ai_conf = _f(lectura.get("ai_confidence_final"), 0)
    goal_imminent_score = _f(lectura.get("goal_imminent_score"), 0)

    decision_score = 0.0
    decision_score += signal_score * 0.30
    decision_score += ai_conf * 0.35
    decision_score += value_score * 4.0
    decision_score -= risk_score * 3.2
    decision_score += goal_imminent_score * 0.12

    if lectura["chaos_level"] == "MEDIO":
        decision_score -= 8

    if lectura["chaos_level"] == "ALTO":
        decision_score -= 18

    decision_score = round(decision_score, 2)

    if lectura["chaos_block_signal"] and lectura["ai_state"] not in ("CONTROL_REAL", "CAOS_UTIL"):
        final_decision = "NO_APOSTAR"
    elif decision_score >= 125 and risk_score <= 5 and lectura["chaos_level"] == "BAJO":
        final_decision = "APOSTAR_FUERTE"
    elif decision_score >= 98 and risk_score <= 7 and lectura["chaos_level"] in ("BAJO", "MEDIO"):
        final_decision = "APOSTAR"
    elif decision_score >= 78 and lectura["chaos_level"] != "ALTO":
        final_decision = "APOSTAR_SUAVE"
    elif decision_score >= 58:
        final_decision = "OBSERVAR"
    else:
        final_decision = "NO_APOSTAR"

    return {
        "ai_state": lectura["ai_state"],
        "ai_score": lectura["ai_score"],
        "ai_reason": lectura["ai_reason"],
        "ai_fit": lectura["ai_fit"],
        "ai_fit_reason": lectura["ai_fit_reason"],
        "ai_confidence_adjustment": lectura["ai_confidence_adjustment"],
        "ai_confidence_final": lectura["ai_confidence_final"],
        "ai_decision_score": decision_score,
        "ai_recommendation": final_decision,
        "chaos_level": lectura["chaos_level"],
        "chaos_detector_score": lectura["chaos_detector_score"],
        "chaos_reason": lectura["chaos_reason"],
        "chaos_block_signal": lectura["chaos_block_signal"],
        "chaos_confidence_penalty": lectura["chaos_confidence_penalty"],
        "goal_imminent_score": lectura["goal_imminent_score"],
        "goal_imminent_level": lectura["goal_imminent_level"],
        "goal_imminent_reason": lectura["goal_imminent_reason"],
    }

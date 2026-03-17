# signal_to_market_translator.py

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


def traducir_senal_a_mercado(match: Dict, ai_read: Dict) -> Dict:
    minuto = _i(match.get("minuto"), 0)
    ml = _i(match.get("marcador_local"), 0)
    mv = _i(match.get("marcador_visitante"), 0)
    diff = abs(ml - mv)

    xg = _f(match.get("xG"), 0)
    shots_on_target = _f(match.get("shots_on_target"), 0)
    dangerous_attacks = _f(match.get("dangerous_attacks"), 0)
    momentum = _u(match.get("momentum"))

    goal_pressure = match.get("goal_pressure", {}) or {}
    pressure_score = _f(goal_pressure.get("pressure_score"), 0)

    ai_state = _u(ai_read.get("ai_state"))
    chaos_level = _u(ai_read.get("chaos_level"))
    goal_level = _u(ai_read.get("goal_imminent_level"))
    goal_score = _f(ai_read.get("goal_imminent_score"), 0)
    ai_recommendation = _u(ai_read.get("ai_recommendation"))

    # Si la IA ya recomienda no apostar, bloquear
    if ai_recommendation == "NO_APOSTAR":
        return {
            "translated_market": "NO_BET",
            "translated_selection": "No entrar",
            "translator_reason": "La IA recomienda no apostar",
            "translator_confidence": 0
        }

    # Si el caos es alto, bloquear
    if chaos_level == "ALTO":
        return {
            "translated_market": "NO_BET",
            "translated_selection": "No entrar",
            "translator_reason": "Caos alto detectado",
            "translator_confidence": 0
        }

    # =========================================================
    # 1. NEXT GOAL
    # =========================================================
    if goal_level in ("CRITICO", "ALTO") and minuto >= 65 and diff <= 1:
        return {
            "translated_market": "NEXT_GOAL",
            "translated_selection": "Próximo gol en el partido",
            "translator_reason": "Ventana de gol inminente alta en tramo sensible",
            "translator_confidence": 88 if goal_level == "CRITICO" else 80
        }

    # =========================================================
    # 2. OVER PROXIMOS 15 MIN
    # =========================================================
    if (
        ai_state in ("CONTROL_REAL", "CAOS_UTIL")
        and goal_score >= 55
        and pressure_score >= 7
        and xg >= 1.3
        and shots_on_target >= 2
        and minuto >= 20
        and minuto <= 82
    ):
        return {
            "translated_market": "OVER_NEXT_15_DYNAMIC",
            "translated_selection": "Over próximos 15 min",
            "translator_reason": "Presión real + gol inminente + contexto ofensivo",
            "translator_confidence": 82
        }

    # =========================================================
    # 3. RESULTADO SE MANTIENE
    # =========================================================
    if (
        ai_state in ("CIERRE_TACTICO", "PARTIDO_MUERTO")
        and goal_level == "BAJO"
        and minuto >= 65
    ):
        return {
            "translated_market": "RESULT_HOLDS_NEXT_15",
            "translated_selection": "Se mantiene el resultado próximos 15 min",
            "translator_reason": "Partido controlado y baja probabilidad de gol inmediato",
            "translator_confidence": 78
        }

    # =========================================================
    # 4. HOLD DEFENSIVO POR CONTEXTO
    # =========================================================
    if (
        momentum in ("BAJO", "MEDIO")
        and dangerous_attacks < 14
        and shots_on_target <= 1
        and minuto >= 70
        and diff >= 1
    ):
        return {
            "translated_market": "RESULT_HOLDS_NEXT_15",
            "translated_selection": "Se mantiene el resultado próximos 15 min",
            "translator_reason": "Ritmo bajo y ventaja defendible",
            "translator_confidence": 74
        }

    # =========================================================
    # 5. NO BET POR CONTEXTO INSUFICIENTE
    # =========================================================
    return {
        "translated_market": "NO_BET",
        "translated_selection": "No entrar",
        "translator_reason": "No hay una ventaja táctica suficientemente clara para elegir mercado",
        "translator_confidence": 0
  }

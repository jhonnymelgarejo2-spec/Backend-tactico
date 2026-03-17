# core/context_engine.py

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


def evaluar_contexto_partido(match: Dict) -> Dict:
    minuto = _i(match.get("minuto"), 0)
    ml = _i(match.get("marcador_local"), 0)
    mv = _i(match.get("marcador_visitante"), 0)
    diff = ml - mv

    xg = _f(match.get("xG"), 0)
    shots_on_target = _f(match.get("shots_on_target"), 0)
    dangerous_attacks = _f(match.get("dangerous_attacks"), 0)
    momentum = _u(match.get("momentum"))

    pressure_score = _f((match.get("goal_pressure") or {}).get("pressure_score"), 0)
    predictor_score = _f((match.get("goal_predictor") or {}).get("predictor_score"), 0)
    chaos_score = _f((match.get("chaos") or {}).get("chaos_score"), 0)

    context_score = 50.0
    context_state = "NEUTRO"
    context_risk = "MEDIO"
    context_reason = "Contexto sin sesgo fuerte"
    supports_over = False
    supports_hold = False
    supports_next_goal = False

    # =====================================================
    # 1. EMPATE EN TRAMO CALIENTE
    # =====================================================
    if diff == 0 and 55 <= minuto <= 80:
        context_score += 10
        if momentum in ("ALTO", "MUY ALTO"):
            context_score += 6
        if pressure_score >= 7:
            context_score += 5
        if dangerous_attacks >= 18:
            context_score += 4
        if shots_on_target >= 3:
            context_score += 4

        context_state = "EMPATE_ABIERTO"
        context_reason = "Empate en tramo sensible con posibilidad de ruptura del marcador"
        supports_over = True
        supports_next_goal = True

    # =====================================================
    # 2. LOCAL NECESITA REACCIONAR
    # =====================================================
    elif diff < 0 and 45 <= minuto <= 82:
        context_score += 12
        if momentum in ("ALTO", "MUY ALTO"):
            context_score += 7
        if pressure_score >= 7:
            context_score += 5
        if predictor_score >= 5:
            context_score += 4
        if shots_on_target >= 2:
            context_score += 3

        context_state = "URGENCIA_LOCAL"
        context_reason = "El local va por debajo y el contexto favorece empuje ofensivo"
        supports_next_goal = True
        supports_over = True

    # =====================================================
    # 3. VISITANTE NECESITA REACCIONAR
    # =====================================================
    elif diff > 0 and 45 <= minuto <= 82:
        context_score += 9
        if chaos_score >= 8:
            context_score += 4
        if pressure_score >= 6:
            context_score += 3

        context_state = "VENTAJA_LOCAL_CONTROLABLE"
        context_reason = "El visitante puede verse obligado a arriesgar y abrir el partido"
        supports_over = True

    # =====================================================
    # 4. VENTAJA CORTA EN TRAMO FINAL
    # =====================================================
    if abs(diff) == 1 and 70 <= minuto <= 87:
        if momentum in ("BAJO", "MEDIO") and pressure_score < 6 and xg < 1.6:
            context_state = "CIERRE_DE_RESULTADO"
            context_score += 6
            context_reason = "Ventaja corta en tramo final con señales de administración"
            supports_hold = True
            supports_over = False
            supports_next_goal = False

    # =====================================================
    # 5. PARTIDO DEMASIADO ROTO
    # =====================================================
    if chaos_score >= 12:
        context_score += 3
        if pressure_score < 6 and shots_on_target <= 1:
            context_state = "CAOS_INESTABLE"
            context_reason = "Partido con volatilidad alta pero dirección poco confiable"
            context_risk = "ALTO"
            supports_over = False
            supports_hold = False
            supports_next_goal = False

    # =====================================================
    # 6. PARTIDO MUERTO
    # =====================================================
    if minuto >= 78 and xg < 1.1 and momentum in ("BAJO", "MEDIO") and pressure_score < 5:
        context_state = "PARTIDO_CERRADO"
        context_score = min(context_score, 52)
        context_reason = "Ritmo bajo en tramo final, contexto favorable al hold"
        context_risk = "BAJO"
        supports_hold = True
        supports_over = False
        supports_next_goal = False

    # =====================================================
    # 7. AJUSTE DE RIESGO GLOBAL
    # =====================================================
    if chaos_score >= 10:
        context_risk = "ALTO"
    elif context_score >= 72 and chaos_score < 8:
        context_risk = "BAJO"
    elif context_score >= 60:
        context_risk = "MEDIO"

    # =====================================================
    # 8. CLAMP FINAL
    # =====================================================
    context_score = max(1.0, min(100.0, round(context_score, 2)))

    return {
        "context_state": context_state,
        "context_score": context_score,
        "context_risk": context_risk,
        "context_supports_over": supports_over,
        "context_supports_hold": supports_hold,
        "context_supports_next_goal": supports_next_goal,
        "context_reason": context_reason
  }

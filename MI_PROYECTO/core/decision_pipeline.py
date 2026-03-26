from typing import Dict, Any, List, Optional


# =========================================================
# IMPORTS PRINCIPALES
# =========================================================
try:
    from signal_engine import generar_senal
except Exception:
    try:
        from engines.signal_engine import generar_senal
    except Exception as e:
        print(f"[PIPELINE] ERROR import generar_senal -> {e}")
        generar_senal = None

try:
    from ai_brain import evaluar_ajuste_ia
except Exception:
    evaluar_ajuste_ia = None

try:
    from context_engine import evaluar_contexto_partido
except Exception:
    evaluar_contexto_partido = None

try:
    from chaos_guardian import evaluar_chaos_partido
except Exception:
    evaluar_chaos_partido = None

try:
    from bankroll_manager import calcular_stake
except Exception:
    calcular_stake = None

try:
    from auto_balance_engine import aplicar_auto_balance
except Exception:
    aplicar_auto_balance = None

try:
    from player_impact_engine import evaluar_impacto_jugadores
except Exception:
    evaluar_impacto_jugadores = None

try:
    from tempo_engine import evaluar_tempo_partido
except Exception:
    evaluar_tempo_partido = None

try:
    from emotional_engine import evaluar_emocion_partido
except Exception:
    evaluar_emocion_partido = None

try:
    from pre_match_engine import evaluar_pre_match
except Exception:
    evaluar_pre_match = None


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


def _lower(value: Any) -> str:
    return _safe_text(value).lower()


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def _estado_partido_texto(estado_partido: Any) -> str:
    if isinstance(estado_partido, dict):
        return _upper(estado_partido.get("estado", ""))
    return _upper(estado_partido)


def _es_minuto_operable(minuto: int) -> bool:
    return 15 <= minuto <= 88


def _es_ventana_premium(minuto: int) -> bool:
    return (25 <= minuto <= 45) or (60 <= minuto <= 85)


def _es_ventana_secundaria(minuto: int) -> bool:
    return (15 <= minuto <= 24) or (46 <= minuto <= 59) or (86 <= minuto <= 88)


# =========================================================
# BASE DEL PARTIDO
# =========================================================
def _calcular_probabilidades_base(partido: Dict[str, Any]) -> Dict[str, float]:
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    minuto = _safe_int(partido.get("minuto"), 0)
    pressure_score = _safe_float((partido.get("goal_pressure") or {}).get("pressure_score"), 0.0)

    predictor = partido.get("goal_predictor") or {}
    goal5 = _safe_float(predictor.get("goal_next_5_prob"), 0.0)
    goal10 = _safe_float(predictor.get("goal_next_10_prob"), 0.0)

    prob_real = 0.52

    if xg >= 2.5:
        prob_real += 0.12
    elif xg >= 1.8:
        prob_real += 0.09
    elif xg >= 1.2:
        prob_real += 0.06
    elif xg >= 0.8:
        prob_real += 0.03

    if shots >= 12:
        prob_real += 0.05
    elif shots >= 8:
        prob_real += 0.03

    if shots_on_target >= 5:
        prob_real += 0.08
    elif shots_on_target >= 3:
        prob_real += 0.05
    elif shots_on_target >= 1:
        prob_real += 0.02

    if dangerous_attacks >= 25:
        prob_real += 0.06
    elif dangerous_attacks >= 18:
        prob_real += 0.04
    elif dangerous_attacks >= 12:
        prob_real += 0.02

    if pressure_score >= 8:
        prob_real += 0.05
    elif pressure_score >= 5:
        prob_real += 0.03

    prob_real += goal5 * 0.10
    prob_real += goal10 * 0.08

    if 70 <= minuto <= 85:
        prob_real += 0.03
    elif 25 <= minuto <= 45:
        prob_real += 0.02

    prob_real = _clamp(prob_real, 0.50, 0.92)

    return {
        "prob_real": round(prob_real, 4),
        "prob_implicita": 0.5405,
        "cuota": 1.85,
    }


def _asegurar_base_partido(partido: Dict[str, Any]) -> Dict[str, Any]:
    p = dict(partido or {})
    base_probs = _calcular_probabilidades_base(p)

    p.setdefault("id", "")
    p.setdefault("local", "Local")
    p.setdefault("visitante", "Visitante")
    p.setdefault("liga", "Liga desconocida")
    p.setdefault("pais", "Mundo")
    p.setdefault("minuto", 0)
    p.setdefault("marcador_local", 0)
    p.setdefault("marcador_visitante", 0)
    p.setdefault("xG", 0.0)
    p.setdefault("shots", 0)
    p.setdefault("shots_on_target", 0)
    p.setdefault("dangerous_attacks", 0)
    p.setdefault("momentum", "MEDIO")
    p.setdefault("estado_partido", "EN_JUEGO")
    p.setdefault("goal_pressure", {"pressure_score": 0.0})
    p.setdefault("goal_predictor", {
        "goal_next_5_prob": 0.0,
        "goal_next_10_prob": 0.0,
        "predictor_score": 0.0,
    })
    p.setdefault("chaos", {"chaos_score": 0.0})

    p["prob_real"] = _safe_float(p.get("prob_real"), base_probs["prob_real"])
    p["prob_implicita"] = _safe_float(p.get("prob_implicita"), base_probs["prob_implicita"])
    p["cuota"] = _safe_float(p.get("cuota"), base_probs["cuota"])

    return p


# =========================================================
# CAPAS DE CONTEXTO
# =========================================================
def _build_context_state(partido: Dict[str, Any]) -> Dict[str, Any]:
    minuto = _safe_int(partido.get("minuto"), 0)
    ml = _safe_int(partido.get("marcador_local"), 0)
    mv = _safe_int(partido.get("marcador_visitante"), 0)
    diff = abs(ml - mv)

    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    xg = _safe_float(partido.get("xG"), 0.0)
    momentum = _upper(partido.get("momentum"))
    pressure_score = _safe_float((partido.get("goal_pressure") or {}).get("pressure_score"), 0.0)
    chaos_score = _safe_float((partido.get("chaos") or {}).get("chaos_score"), 0.0)

    context_score = 50.0
    context_state = "NEUTRO"
    context_risk = "MEDIO"
    context_supports_hold = False
    context_supports_next_goal = False
    context_supports_over = False

    if diff == 0 and minuto >= 65:
        context_score += 10
        context_state = "EMPATE_ABIERTO"

    if diff == 1 and minuto >= 70:
        context_score += 12
        context_state = "CIERRE_DE_RESULTADO"

    if xg >= 1.6 or shots_on_target >= 3 or dangerous_attacks >= 18:
        context_score += 10
        context_supports_next_goal = True
        context_supports_over = True

    if momentum in ("ALTO", "MUY ALTO"):
        context_score += 7
        context_supports_next_goal = True

    if pressure_score >= 6:
        context_score += 6
        context_supports_next_goal = True

    if chaos_score >= 8:
        context_score += 4
        context_supports_over = True

    if (
        minuto >= 72 and
        diff <= 1 and
        xg < 1.5 and
        shots_on_target <= 2 and
        dangerous_attacks < 16
    ):
        context_supports_hold = True
        context_state = "PARTIDO_CERRADO"

    if context_supports_hold and not context_supports_next_goal:
        context_risk = "BAJO"
    elif context_supports_next_goal and xg >= 1.8:
        context_risk = "MEDIO"
    elif chaos_score >= 10:
        context_risk = "ALTO"

    return {
        "context_score": round(context_score, 2),
        "context_state": context_state,
        "context_risk": context_risk,
        "context_supports_hold": context_supports_hold,
        "context_supports_next_goal": context_supports_next_goal,
        "context_supports_over": context_supports_over,
        "context_reason": "Contexto calculado por marcador, minuto, xG, tiros y presión",
    }


def _build_emotion_state(partido: Dict[str, Any]) -> Dict[str, Any]:
    minuto = _safe_int(partido.get("minuto"), 0)
    ml = _safe_int(partido.get("marcador_local"), 0)
    mv = _safe_int(partido.get("marcador_visitante"), 0)
    diff = abs(ml - mv)
    momentum = _upper(partido.get("momentum"))
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)

    emocion_estado = "CONTROLADO"
    emocion_intensidad = 4
    emocion_razon = "Partido estable"

    if diff == 0 and minuto >= 65:
        emocion_estado = "EMPATE_TEMPRANO" if minuto < 75 else "EMPATE_TENSO"
        emocion_intensidad = 5
        emocion_razon = "Empate con posibilidad de ruptura"

    if diff == 1 and minuto >= 70:
        emocion_estado = "URGENTE"
        emocion_intensidad = 6
        emocion_razon = "Un equipo puede verse obligado a arriesgar"

    if momentum in ("ALTO", "MUY ALTO") and dangerous_attacks >= 18:
        emocion_estado = "PARTIDO_ABIERTO"
        emocion_intensidad = 7
        emocion_razon = "Ritmo ofensivo elevado"

    return {
        "emocion_estado": emocion_estado,
        "emocion_intensidad": emocion_intensidad,
        "emocion_razon": emocion_razon,
    }


def _build_tempo_state(partido: Dict[str, Any]) -> Dict[str, Any]:
    minuto = _safe_int(partido.get("minuto"), 0)
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)

    tempo_score = 0.0
    tempo_score += xg * 28
    tempo_score += shots * 2.2
    tempo_score += shots_on_target * 6.0
    tempo_score += dangerous_attacks * 0.9

    if minuto > 0:
        tempo_xg_per_min = round(xg / minuto, 4)
        tempo_shots_per_min = round(shots / minuto, 4)
        tempo_dangerous_per_min = round(dangerous_attacks / minuto, 4)
    else:
        tempo_xg_per_min = 0.0
        tempo_shots_per_min = 0.0
        tempo_dangerous_per_min = 0.0

    if tempo_score >= 75:
        tempo_state = "ACELERADO"
        tempo_reason = "xG por minuto alto y ritmo ofensivo sostenido"
    elif tempo_score >= 40:
        tempo_state = "NORMAL"
        tempo_reason = "Ritmo intermedio y producción razonable"
    else:
        tempo_state = "LENTO"
        tempo_reason = "Sin lectura de ritmo clara"

    return {
        "tempo_score": round(tempo_score, 2),
        "tempo_state": tempo_state,
        "tempo_reason": tempo_reason,
        "tempo_xg_per_min": tempo_xg_per_min,
        "tempo_shots_per_min": tempo_shots_per_min,
        "tempo_dangerous_per_min": tempo_dangerous_per_min,
    }


def _build_player_state(partido: Dict[str, Any]) -> Dict[str, Any]:
    local = _safe_text(partido.get("local"), "Local")
    visitante = _safe_text(partido.get("visitante"), "Visitante")

    return {
        "player_impact_score": 0.0,
        "player_impact_state": "DEBIL",
        "player_impact_diff": 0.0,
        "player_impact_adjustment": 0.0,
        "player_impact_probable_side": "EMPATE",
        "player_impact_reason": f"{local}: Sin datos de jugadores | {visitante}: Sin datos de jugadores",
        "home_player_summary": {
            "team": local,
            "available_count": 0,
            "starting_count": 0,
            "key_available": 0,
            "key_missing": 0,
            "fatigue_avg": 0.0,
            "attack_impact": 0.0,
            "player_score": 0.0,
            "player_reason": "Sin datos de jugadores",
        },
        "away_player_summary": {
            "team": visitante,
            "available_count": 0,
            "starting_count": 0,
            "key_available": 0,
            "key_missing": 0,
            "fatigue_avg": 0.0,
            "attack_impact": 0.0,
            "player_score": 0.0,
            "player_reason": "Sin datos de jugadores",
        },
        "home_attack_impact": 0.0,
        "away_attack_impact": 0.0,
        "home_fatigue_avg": 0.0,
        "away_fatigue_avg": 0.0,
    }


def _build_arbiter_state(partido: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "referee_score": -8.0,
        "referee_state": "NORMAL",
        "referee_reason": "Árbitro deja jugar mucho",
        "referee_total_fouls": 0,
        "referee_total_yellows": 0,
        "referee_total_reds": 0,
        "penalty_event_risk": 0.0,
        "puntacion_del_arbitro": -8.0,
    }


# =========================================================
# SCORING DE MERCADO
# =========================================================
def _market_bias(signal: Dict[str, Any]) -> Dict[str, Any]:
    market = _upper(signal.get("market"))
    estado = _estado_partido_texto(signal.get("estado_partido"))
    minuto = _safe_int(signal.get("minute"), 0)
    xg = _safe_float(signal.get("xG"), 0.0)
    shots_on_target = _safe_int(signal.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(signal.get("dangerous_attacks"), 0)
    goal_prob_5 = _safe_float(signal.get("goal_prob_5"), 0.0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)

    final_score = 0.0
    final_reason = "Sin lectura extra"

    if market == "NEXT_GOAL":
        final_score += goal_prob_5 * 0.60
        final_score += goal_prob_10 * 0.25
        final_score += xg * 12
        final_score += shots_on_target * 4
        final_score += dangerous_attacks * 0.40

        if estado in ("EXPLOSIVO", "CALIENTE", "CAOS"):
            final_score += 25

        if 25 <= minuto <= 84:
            final_score += 8

        final_reason = "Ventana ofensiva real para próximo gol"

    elif market == "OVER_NEXT_15_DYNAMIC":
        final_score += goal_prob_10 * 0.45
        final_score += xg * 10
        final_score += shots_on_target * 3.5
        final_score += dangerous_attacks * 0.30

        if estado in ("EXPLOSIVO", "CALIENTE", "CAOS"):
            final_score += 22

        if 20 <= minuto <= 86:
            final_score += 10

        final_reason = "Ventana ofensiva útil para los próximos 15 min"

    elif market == "OVER_MATCH_DYNAMIC":
        final_score += xg * 14
        final_score += shots_on_target * 3
        final_score += dangerous_attacks * 0.25

        if estado in ("EXPLOSIVO", "CALIENTE"):
            final_score += 18

        if minuto <= 80:
            final_score += 8

        final_reason = "Proyección de más goles en el resto del partido"

    elif market == "UNDER_MATCH_DYNAMIC":
        final_score += 65
        final_score -= xg * 12
        final_score -= shots_on_target * 4
        final_score -= dangerous_attacks * 0.35
        final_score -= goal_prob_10 * 0.35

        if estado in ("FRIO", "CONTROLADO", "MUERTO"):
            final_score += 18

        if minuto >= 60:
            final_score += 8

        final_reason = "El contexto final favorece cierre defensivo"

    elif market == "RESULT_HOLDS_NEXT_15":
        final_score += 58
        final_score -= xg * 10
        final_score -= shots_on_target * 4.5
        final_score -= dangerous_attacks * 0.35
        final_score -= goal_prob_5 * 0.50
        final_score -= goal_prob_10 * 0.20

        if estado in ("FRIO", "CONTROLADO", "MUERTO"):
            final_score += 16

        if minuto >= 70:
            final_score += 12

        if estado in ("EXPLOSIVO", "CALIENTE", "CAOS"):
            final_score -= 25

        final_reason = "Marcador con margen y ritmo apto para sostenerse"

    return {
        "final_market_score": round(final_score, 2),
        "final_market_reason": final_reason,
    }


def _final_outcome_bias(signal: Dict[str, Any]) -> Dict[str, Any]:
    market = _upper(signal.get("market"))
    ganador_probable = _upper(signal.get("ganador_probable"))
    resultado_probable = _safe_text(signal.get("resultado_probable"), "")
    total_goles_estimado = _safe_float(signal.get("total_goles_estimado"), 0.0)

    final_selection_recommended = signal.get("selection")
    final_outcome_state = "SIN_VENTAJA"
    final_outcome_reason = "Sin producción real"
    hold_result_score = 0.0
    next_goal_score = 0.0
    over_final_score = 0.0
    under_final_score = 0.0

    if market == "RESULT_HOLDS_NEXT_15":
        hold_result_score = 75.0
        final_outcome_state = "LECTURA_CONSERVADORA"
        final_outcome_reason = "Se mantiene la lectura del pipeline"

    if market == "NEXT_GOAL":
        next_goal_score = 78.0
        final_outcome_state = "VENTANA_DE_GOL"
        final_outcome_reason = "Alta probabilidad de otro gol cercano"

    if market == "OVER_MATCH_DYNAMIC":
        over_final_score = 74.0
        final_outcome_state = "SESGO_OVER"
        final_outcome_reason = "El modelo favorece más goles"

    if market == "UNDER_MATCH_DYNAMIC":
        under_final_score = 72.0
        final_outcome_state = "SESGO_UNDER"
        final_outcome_reason = "El modelo favorece cierre de marcador"

    if final_selection_recommended in (None, "", "None"):
        if market == "RESULT_HOLDS_NEXT_15":
            final_selection_recommended = "Se mantiene el resultado próximos 15 min"
        elif market == "NEXT_GOAL":
            final_selection_recommended = "Habrá gol (próximo)"
        elif market == "OVER_MATCH_DYNAMIC":
            final_selection_recommended = "Over partido"
        elif market == "UNDER_MATCH_DYNAMIC":
            final_selection_recommended = "Under partido"

    return {
        "final_selection_recommended": final_selection_recommended,
        "final_outcome_state": final_outcome_state,
        "final_outcome_reason": final_outcome_reason,
        "hold_result_score": round(hold_result_score, 2),
        "next_goal_score": round(next_goal_score, 2),
        "over_final_score": round(over_final_score, 2),
        "under_final_score": round(under_final_score, 2),
        "resultado_probable": resultado_probable,
        "ganador_probable": ganador_probable,
        "total_goles_estimado": round(total_goles_estimado, 2),
    }


# =========================================================
# IA
# =========================================================
def _build_ai_layer(partido: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    minute = _safe_int(partido.get("minuto"), 0)
    xg = _safe_float(partido.get("xG"), 0.0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    market = _upper(signal.get("market"))
    confidence = _safe_float(signal.get("confidence"), 0.0)
    estado = _estado_partido_texto(signal.get("estado_partido"))

    ai_score = 55.0
    ai_state = "NEUTRAL"
    ai_fit = "NEUTRAL"
    ai_fit_reason = "Sin ajuste especial"
    ai_reason = "Contexto mixto sin lectura extrema"
    ai_confidence_adjustment = 0.0
    ai_recommendation = "APOSTAR"

    if market in ("NEXT_GOAL", "OVER_NEXT_15_DYNAMIC") and xg >= 1.4 and shots_on_target >= 2:
        ai_score += 18
        ai_state = "CONTROL_REAL"
        ai_fit = "ALINEADA"
        ai_fit_reason = "Ventana alta de gol inminente"
        ai_reason = "Presión ofensiva respaldada por producción real"
        ai_confidence_adjustment += 7

    if market in ("UNDER_MATCH_DYNAMIC", "RESULT_HOLDS_NEXT_15") and minute >= 70 and xg < 1.4:
        ai_score += 14
        ai_state = "CONTROL_REAL"
        ai_fit = "ALINEADA"
        ai_fit_reason = "Cierre táctico / baja producción"
        ai_reason = "El partido parece entrar en gestión de resultado"
        ai_confidence_adjustment += 6

    if dangerous_attacks >= 18 and shots_on_target >= 3 and market == "RESULT_HOLDS_NEXT_15":
        ai_score -= 10
        ai_fit = "FORZADA"
        ai_reason = "Hay actividad ofensiva incompatible con sostener marcador"

    if estado in ("CAOS", "EXPLOSIVO") and market in ("UNDER_MATCH_DYNAMIC", "RESULT_HOLDS_NEXT_15"):
        ai_score -= 16
        ai_fit = "CONFLICTIVA"
        ai_reason = "Mercado poco alineado con el estado explosivo"

    if confidence < 66:
        ai_score -= 6

    ai_confidence_final = _clamp(confidence + ai_confidence_adjustment, 50.0, 95.0)

    if ai_score < 42:
        ai_recommendation = "OBSERVAR"

    return {
        "ai_score": round(ai_score, 2),
        "ai_decision_score": round(ai_score * 2.05, 2),
        "ai_state": ai_state,
        "ai_fit": ai_fit,
        "ai_fit_reason": ai_fit_reason,
        "ai_reason": ai_reason,
        "ai_confidence_adjustment": round(ai_confidence_adjustment, 2),
        "ai_confidence_final": round(ai_confidence_final, 2),
        "ai_recommendation": ai_recommendation,
    }


# =========================================================
# FILTROS
# =========================================================
def _build_dynamic_filters(signal: Dict[str, Any]) -> Dict[str, Any]:
    minute = _safe_int(signal.get("minute"), 0)
    market = _upper(signal.get("market"))
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    signal_score = _safe_float(signal.get("signal_score"), 0.0)
    estado = _estado_partido_texto(signal.get("estado_partido"))

    dynamic_context_min_score = 30
    dynamic_chaos_confidence_block = 68
    dynamic_min_confidence = 64
    dynamic_value_flex_mode = True

    antifake_ok = True
    value_filter_ok = True
    context_ok = True
    chaos_ok = True
    confianza_ok = True

    if minute < 15 or minute >= 89:
        context_ok = False

    if confidence < dynamic_min_confidence:
        confianza_ok = False

    if value < 0.50:
        value_filter_ok = False

    if market == "RESULT_HOLDS_NEXT_15" and tactical_score < 9:
        context_ok = False

    if market in ("NEXT_GOAL", "OVER_NEXT_15_DYNAMIC") and tactical_score < 8:
        context_ok = False

    if signal_score < 55:
        context_ok = False

    if risk_score > 8.2:
        antifake_ok = False

    if estado == "CAOS" and confidence < dynamic_chaos_confidence_block and market in ("UNDER_MATCH_DYNAMIC", "RESULT_HOLDS_NEXT_15"):
        chaos_ok = False

    publish_ready = all([antifake_ok, value_filter_ok, context_ok, chaos_ok, confianza_ok])

    return {
        "dynamic_context_min_score": dynamic_context_min_score,
        "dynamic_chaos_confidence_block": dynamic_chaos_confidence_block,
        "dynamic_min_confidence": dynamic_min_confidence,
        "dynamic_value_flex_mode": dynamic_value_flex_mode,
        "antifake_ok": antifake_ok,
        "value_filter_ok": value_filter_ok,
        "context_ok": context_ok,
        "chaos_ok": chaos_ok,
        "confianza_ok": confianza_ok,
        "publish_ready": publish_ready,
    }


def _build_operation_fields(signal: Dict[str, Any]) -> Dict[str, Any]:
    signal_rank = _upper(signal.get("signal_rank"))
    confidence = _safe_float(signal.get("confidence"), 0.0)
    ai_score = _safe_float(signal.get("ai_decision_score"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)

    stake_pct = 2.0
    stake_label = "NORMAL"

    if signal_rank == "ELITE" or (confidence >= 86 and ai_score >= 150 and value >= 10 and risk_score <= 4.8):
        stake_pct = 4.9
        stake_label = "FUERTE"
    elif signal_rank == "TOP" or (confidence >= 78 and value >= 5):
        stake_pct = 4.0
        stake_label = "FUERTE"
    elif confidence >= 71:
        stake_pct = 3.2
        stake_label = "MEDIO"

    stake_amount = round(stake_pct * 10, 1)

    return {
        "stake_pct": round(stake_pct, 1),
        "stake_amount": stake_amount,
        "stake_label": stake_label,
        "bankroll_mode": "NEUTRAL",
        "max_operaciones_dia": 3,
        "stop_loss_consecutivo": 2,
        "permitido_operar": True,
        "decision_ejecutiva": "SI",
        "decision_ia": "APOSTAR" if confidence >= 64 else "OBSERVAR",
    }


def _master_gate(partido: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    minute = _safe_int(partido.get("minuto"), 0)
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    signal_score = _safe_float(signal.get("signal_score"), 0.0)
    market = _upper(signal.get("market"))
    estado = _estado_partido_texto(signal.get("estado_partido"))

    blocked_reasons: List[str] = []

    if not _es_minuto_operable(minute):
        blocked_reasons.append("Fuera de ventana operable")

    if confidence < 64:
        blocked_reasons.append("Confianza por debajo del mínimo")

    if value < 0.50:
        blocked_reasons.append("Value insuficiente")

    if risk_score > 8.2:
        blocked_reasons.append("Riesgo operativo alto")

    if signal_score < 55:
        blocked_reasons.append("Signal score insuficiente")

    if market == "RESULT_HOLDS_NEXT_15" and estado in ("CAOS", "EXPLOSIVO") and confidence < 80:
        blocked_reasons.append("Mercado hold no coherente con estado explosivo")

    if market in ("NEXT_GOAL", "OVER_NEXT_15_DYNAMIC") and tactical_score < 8:
        blocked_reasons.append("Mercado ofensivo sin respaldo táctico suficiente")

    if market == "UNDER_MATCH_DYNAMIC" and minute < 22:
        blocked_reasons.append("Under partido demasiado temprano")

    publish_ready = len(blocked_reasons) == 0

    return {
        "publish_ready": publish_ready,
        "publish_blocked_reasons": blocked_reasons,
    }


# =========================================================
# RANKING
# =========================================================
def _ranking_layer(signal: Dict[str, Any]) -> Dict[str, Any]:
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    signal_score = _safe_float(signal.get("signal_score"), 0.0)
    ai_decision_score = _safe_float(signal.get("ai_decision_score"), 0.0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)
    market = _upper(signal.get("market"))
    minute = _safe_int(signal.get("minute"), 0)

    ranking_score_base = (
        ai_decision_score * 1.75 +
        signal_score * 1.30 +
        confidence * 1.15 +
        value * 2.60 +
        tactical_score * 0.70
    )

    ranking_penalty = risk_score * 8.5

    if minute >= 85:
        ranking_penalty += 8
    elif minute >= 80:
        ranking_penalty += 4

    if market == "RESULT_HOLDS_NEXT_15":
        ranking_penalty += 1.5

    ranking_score = round(ranking_score_base - ranking_penalty, 2)
    qualifies_for_top = ranking_score >= 120

    publish_rank = 3
    if ranking_score >= 320:
        publish_rank = 1
    elif ranking_score >= 220:
        publish_rank = 2

    return {
        "ranking_score_base": round(ranking_score_base, 2),
        "ranking_penalty": round(ranking_penalty, 2),
        "ranking_score": ranking_score,
        "qualifies_for_top": qualifies_for_top,
        "publish_rank": publish_rank,
    }


# =========================================================
# RAZONES
# =========================================================
def _build_reason_fields(partido: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    local = _safe_text(partido.get("local"), "Local")
    visitante = _safe_text(partido.get("visitante"), "Visitante")

    return {
        "razon_tactica": _safe_text(signal.get("reason"), "Lectura táctica del partido"),
        "razon_contexto": _safe_text(signal.get("context_reason"), "Contexto mixto sin lectura extrema"),
        "razon_ia": _safe_text(signal.get("ai_reason"), "Lectura IA general"),
        "razon_jugadores": f"{local}: Sin datos de jugadores | {visitante}: Sin datos de jugadores",
        "razon_ritmo": _safe_text(signal.get("tempo_reason"), "Sin lectura de ritmo clara"),
        "razon_emocional": _safe_text(signal.get("emocion_razon"), "Lectura emocional estable"),
        "razon_arbitral": _safe_text(signal.get("referee_reason"), "Árbitro deja jugar mucho"),
    }


# =========================================================
# FORMATO PUBLICO
# =========================================================
def _publicar_formato_final(partido: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    local = _safe_text(partido.get("local"), "Local")
    visitante = _safe_text(partido.get("visitante"), "Visitante")
    liga = _safe_text(partido.get("liga"), "Liga desconocida")
    pais = _safe_text(partido.get("pais"), "Mundo")
    ml = _safe_int(partido.get("marcador_local"), 0)
    mv = _safe_int(partido.get("marcador_visitante"), 0)
    minuto = _safe_int(partido.get("minuto"), 0)

    market = _safe_text(signal.get("mercado"))
    selection = _safe_text(signal.get("selection"))
    if not selection:
        selection = _safe_text(signal.get("apuesta"))

    return {
        "match_id": partido.get("id"),
        "home": local,
        "away": visitante,
        "league": liga,
        "liga": liga,
        "country": pais,
        "pais": pais,
        "partido": f"{local} vs {visitante}",
        "score": f"{ml}-{mv}",
        "minuto": minuto,
        "minute": minuto,
        "market": market,
        "mercado": market,
        "selection": selection,
        "apuesta": selection,
        "line": signal.get("linea"),
        "linea": signal.get("linea"),
        "odd": round(_safe_float(signal.get("cuota"), 1.85), 2),
        "cuota": round(_safe_float(signal.get("cuota"), 1.85), 2),
        "prob": round(_safe_float(signal.get("prob_real"), 0.0), 4),
        "prob_real": round(_safe_float(signal.get("prob_real"), 0.0), 4),
        "prob_real_pct": round(_safe_float(signal.get("prob_real"), 0.0) * 100, 2),
        "prob_implicita": round(_safe_float(signal.get("prob_implicita"), 0.0), 4),
        "confidence": round(_safe_float(signal.get("confianza"), 0.0), 2),
        "confianza": round(_safe_float(signal.get("confianza"), 0.0), 2),
        "value": round(_safe_float(signal.get("valor"), 0.0), 2),
        "valor": round(_safe_float(signal.get("valor"), 0.0), 2),
        "reason": _safe_text(signal.get("razon")),
        "tier": _safe_text(signal.get("tier")),
        "goal_prob_5": round(_safe_float(signal.get("goal_prob_5"), 0.0), 2),
        "goal_prob_10": round(_safe_float(signal.get("goal_prob_10"), 0.0), 2),
        "goal_prob_15": round(_safe_float(signal.get("goal_prob_15"), 0.0), 2),
        "estado_partido": signal.get("estado_partido"),
        "gol_inminente": signal.get("gol_inminente"),
        "resultado_probable": _safe_text(signal.get("resultado_probable")),
        "ganador_probable": _safe_text(signal.get("ganador_probable")),
        "doble_oportunidad_probable": _safe_text(signal.get("doble_oportunidad_probable")),
        "total_goles_estimado": round(_safe_float(signal.get("total_goles_estimado"), 0.0), 2),
        "linea_goles_probable": _safe_text(signal.get("linea_goles_probable")),
        "over_under_probable": _safe_text(signal.get("over_under_probable")),
        "confianza_prediccion": round(_safe_float(signal.get("confianza_prediccion"), 0.0), 2),
        "recomendacion_final": _safe_text(signal.get("recomendacion_final"), "APOSTAR"),
        "riesgo_operativo": _safe_text(signal.get("riesgo_operativo"), "MEDIO"),
        "xG": round(_safe_float(partido.get("xG"), 0.0), 2),
        "shots": _safe_int(partido.get("shots"), 0),
        "shots_on_target": _safe_int(partido.get("shots_on_target"), 0),
        "dangerous_attacks": _safe_int(partido.get("dangerous_attacks"), 0),
        "momentum": _safe_text(partido.get("momentum"), "MEDIO"),
    }


# =========================================================
# CALCULO DE SCORES BASE
# =========================================================
def _calcular_scores_core(signal: Dict[str, Any], partido: Dict[str, Any]) -> Dict[str, Any]:
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    minute = _safe_int(signal.get("minute"), _safe_int(partido.get("minuto"), 0))
    market = _upper(signal.get("market"))

    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    momentum = _upper(partido.get("momentum"))
    pressure_score = _safe_float((partido.get("goal_pressure") or {}).get("pressure_score"), 0.0)
    predictor_score = _safe_float((partido.get("goal_predictor") or {}).get("predictor_score"), 0.0)
    goal_prob_5 = _safe_float(signal.get("goal_prob_5"), 0.0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)
    goal_prob_15 = _safe_float(signal.get("goal_prob_15"), 0.0)
    chaos_score = _safe_float((partido.get("chaos") or {}).get("chaos_score"), 0.0)

    tactical_score = 0.0
    tactical_score += xg * 12.0
    tactical_score += shots * 0.50
    tactical_score += shots_on_target * 3.0
    tactical_score += dangerous_attacks * 0.18
    tactical_score += pressure_score * 1.8
    tactical_score += predictor_score * 1.4
    tactical_score -= chaos_score * 0.35

    if momentum == "MUY ALTO":
        tactical_score += 10
    elif momentum == "ALTO":
        tactical_score += 7
    elif momentum == "MEDIO":
        tactical_score += 3

    if _es_ventana_premium(minute):
        tactical_score += 8
    elif _es_ventana_secundaria(minute):
        tactical_score += 4

    goal_inminente_score = (
        (goal_prob_5 * 0.48) +
        (goal_prob_10 * 0.32) +
        (goal_prob_15 * 0.20)
    )

    if market in ("NEXT_GOAL", "OVER_NEXT_15_DYNAMIC"):
        goal_inminente_score += 8

    risk_score = 5.0

    if confidence >= 85:
        risk_score -= 1.4
    elif confidence >= 75:
        risk_score -= 0.9
    elif confidence < 62:
        risk_score += 1.2

    if value >= 10:
        risk_score -= 1.0
    elif value < 2:
        risk_score += 1.0

    if minute >= 86:
        risk_score += 1.3
    elif minute >= 80:
        risk_score += 0.7

    if market == "RESULT_HOLDS_NEXT_15" and (goal_prob_5 >= 35 or xg >= 1.8 or shots_on_target >= 4):
        risk_score += 2.2

    if market == "UNDER_MATCH_DYNAMIC" and (goal_prob_10 >= 55 or momentum in ("ALTO", "MUY ALTO")):
        risk_score += 1.4

    signal_score = 0.0
    signal_score += confidence * 1.20
    signal_score += value * 2.10
    signal_score += tactical_score * 0.85
    signal_score += goal_inminente_score * 0.70
    signal_score -= risk_score * 4.20

    tactical_score = round(_clamp(tactical_score, 0.0, 200.0), 2)
    goal_inminente_score = round(_clamp(goal_inminente_score, 0.0, 100.0), 2)
    risk_score = round(_clamp(risk_score, 1.0, 10.0), 2)
    signal_score = round(signal_score, 2)

    if signal_score >= 230:
        signal_rank = "ELITE"
    elif signal_score >= 170:
        signal_rank = "TOP"
    elif signal_score >= 110:
        signal_rank = "ALTA"
    else:
        signal_rank = "NORMAL"

    return {
        "tactical_score": tactical_score,
        "goal_inminente_score": goal_inminente_score,
        "risk_score": risk_score,
        "signal_score": signal_score,
        "signal_rank": signal_rank,
    }


# =========================================================
# PIPELINE CENTRAL
# =========================================================
def procesar_partido(partido: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        if not generar_senal:
            print("[PIPELINE] generar_senal no disponible")
            return None

        partido = _asegurar_base_partido(partido)

        minuto = _safe_int(partido.get("minuto"), 0)
        if not _es_minuto_operable(minuto):
            print(f"[PIPELINE] partido fuera de ventana -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

        base_signal = generar_senal(partido)
        if not base_signal:
            print(f"[PIPELINE] señal base vacía -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

        if _upper(base_signal.get("mercado")) == "SIN_SEÑAL" or _upper(base_signal.get("tier")) == "DESCARTAR":
            print(f"[PIPELINE] señal descartada por motor base -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

        signal = _publicar_formato_final(partido, base_signal)

        context_state = _build_context_state(partido)
        emotion_state = _build_emotion_state(partido)
        tempo_state = _build_tempo_state(partido)
        player_state = _build_player_state(partido)
        arbiter_state = _build_arbiter_state(partido)

        signal.update(context_state)
        signal.update(emotion_state)
        signal.update(tempo_state)
        signal.update(player_state)
        signal.update(arbiter_state)

        ai_layer = _build_ai_layer(partido, signal)
        signal.update(ai_layer)

        signal["adaptive_adjustment"] = "NEUTRAL"
        signal["confidence"] = round(_safe_float(ai_layer.get("ai_confidence_final"), signal.get("confidence", 0.0)), 2)
        signal["confianza"] = signal["confidence"]

        market_bias = _market_bias(signal)
        signal.update(market_bias)

        outcome_bias = _final_outcome_bias(signal)
        signal.update(outcome_bias)

        core_scores = _calcular_scores_core(signal, partido)
        signal.update(core_scores)

        dynamic_filters = _build_dynamic_filters(signal)
        signal.update(dynamic_filters)

        op_fields = _build_operation_fields(signal)
        signal.update(op_fields)

        master_gate = _master_gate(partido, signal)
        signal.update(master_gate)

        if not signal.get("publish_ready", False):
            print(f"[PIPELINE] RECHAZADO MASTER GATE -> {partido.get('local')} vs {partido.get('visitante')}")
            print(f"[PIPELINE] BLOQUEOS -> {signal.get('publish_blocked_reasons', [])}")
            return None

        ranking = _ranking_layer(signal)
        signal.update(ranking)

        if not signal.get("qualifies_for_top", False):
            print(f"[PIPELINE] FINAL DE RECHAZADO IA -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

        reason_fields = _build_reason_fields(partido, signal)
        signal.update(reason_fields)

        signal["signal_status"] = "OPEN"
        signal["motivo_operacion"] = "OK"
        signal["auto_balance_mode"] = "NEUTRAL"
        signal["auto_balance_reason"] = "Sin historial disponible"
        signal["auto_balance_recent_winrate"] = 0.0
        signal["auto_balance_recent_resolved"] = 0
        signal["chaos_block_signal"] = False
        signal["chaos_confidence_penalty"] = 0.0
        signal["chaos_detector_score"] = round(_safe_float((partido.get("chaos") or {}).get("chaos_score"), 0.0), 2)
        signal["chaos_level"] = (
            "ALTO" if signal["chaos_detector_score"] >= 10
            else "MEDIO" if signal["chaos_detector_score"] >= 6
            else "BAJO"
        )
        signal["chaos_reason"] = (
            "Partido estable"
            if signal["chaos_detector_score"] < 6
            else "Presencia de volatilidad"
        )
        signal["publish_ready"] = True

        signal["senal_id"] = str(partido.get("id"))
        signal["hora_generada"] = "00:00:00"

        return signal

    except Exception as e:
        print(f"[PIPELINE] ERROR procesar_partido -> {e}")
        return None

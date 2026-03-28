# pipeline_de_decisión.py

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
    from risk_engine import evaluar_riesgo
except Exception:
    try:
        from engines.risk_engine import evaluar_riesgo
    except Exception as e:
        print(f"[PIPELINE] ERROR import evaluar_riesgo -> {e}")
        evaluar_riesgo = None

try:
    from ai_brain import decision_final_ia
except Exception:
    try:
        from engines.ai_brain import decision_final_ia
    except Exception as e:
        print(f"[PIPELINE] ERROR import decision_final_ia -> {e}")
        decision_final_ia = None


# =========================================================
# IMPORTS THE ODDS API
# =========================================================
try:
    from core.odds_market_fetcher import obtener_odds_partido
except Exception:
    try:
        from odds_market_fetcher import obtener_odds_partido
    except Exception as e:
        print(f"[PIPELINE] ERROR import obtener_odds_partido -> {e}")
        obtener_odds_partido = None

try:
    from core.market_validation_engine import validar_mercado_con_odds
except Exception:
    try:
        from market_validation_engine import validar_mercado_con_odds
    except Exception as e:
        print(f"[PIPELINE] ERROR import validar_mercado_con_odds -> {e}")
        validar_mercado_con_odds = None


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
    context_supports_next_goal = False
    context_supports_over = False
    context_supports_under = False

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

    if minuto >= 62 and xg < 1.20 and shots_on_target <= 2 and dangerous_attacks < 16:
        context_supports_under = True
        if context_state == "NEUTRO":
            context_state = "PARTIDO_CERRADO"

    if context_supports_under and not context_supports_next_goal:
        context_risk = "BAJO"
    elif context_supports_next_goal and xg >= 1.8:
        context_risk = "MEDIO"
    elif chaos_score >= 10:
        context_risk = "ALTO"

    return {
        "context_score": round(context_score, 2),
        "context_state": context_state,
        "context_risk": context_risk,
        "context_supports_next_goal": context_supports_next_goal,
        "context_supports_over": context_supports_over,
        "context_supports_under": context_supports_under,
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
        emocion_estado = "EMPATE_TENSO" if minuto >= 75 else "EMPATE_ABIERTO"
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
    }


def _build_arbiter_state(partido: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "referee_score": -8.0,
        "referee_state": "NORMAL",
        "referee_reason": "Árbitro deja jugar mucho",
        "penalty_event_risk": 0.0,
    }


# =========================================================
# FORMATO PUBLICO / INTERNO
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

    cuota_base = round(_safe_float(signal.get("cuota"), 1.85), 2)
    prob_implicita_base = round(_safe_float(signal.get("prob_implicita"), 0.0), 4)
    value_base = round(_safe_float(signal.get("valor"), 0.0), 2)

    return {
        "match_id": partido.get("id"),
        "home": local,
        "away": visitante,
        "league": liga,
        "country": pais,
        "partido": f"{local} vs {visitante}",
        "score": f"{ml}-{mv}",
        "minute": minuto,
        "market": market,
        "selection": selection,
        "line": signal.get("linea"),
        "odd": cuota_base,
        "cuota": cuota_base,
        "prob": round(_safe_float(signal.get("prob_real"), 0.0), 4),
        "prob_real": round(_safe_float(signal.get("prob_real"), 0.0), 4),
        "prob_real_pct": round(_safe_float(signal.get("prob_real"), 0.0) * 100, 2),
        "prob_implicita": prob_implicita_base,
        "confidence": round(_safe_float(signal.get("confianza"), 0.0), 2),
        "value": value_base,
        "valor": value_base,
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
# SCORING BASE
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

    if market == "OVER_NEXT_15_DYNAMIC":
        goal_inminente_score += 8

    tactical_score = round(_clamp(tactical_score, 0.0, 200.0), 2)
    goal_inminente_score = round(_clamp(goal_inminente_score, 0.0, 100.0), 2)

    provisional_signal_score = (
        confidence * 1.20 +
        value * 2.10 +
        tactical_score * 0.85 +
        goal_inminente_score * 0.70
    )

    return {
        "tactical_score": tactical_score,
        "goal_inminente_score": goal_inminente_score,
        "signal_score": round(provisional_signal_score, 2),
    }


def _recalcular_signal_score(signal: Dict[str, Any]) -> Dict[str, Any]:
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    goal_inminente_score = _safe_float(signal.get("goal_inminente_score"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)
    ai_decision_score = _safe_float(signal.get("ai_decision_score"), 0.0)

    signal_score = 0.0
    signal_score += confidence * 1.20
    signal_score += value * 2.10
    signal_score += tactical_score * 0.85
    signal_score += goal_inminente_score * 0.70
    signal_score += ai_decision_score * 0.15
    signal_score -= risk_score * 4.20
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
        "signal_score": signal_score,
        "signal_rank": signal_rank,
    }


# =========================================================
# SCORING DE MERCADO / OUTCOME
# =========================================================
def _market_bias(signal: Dict[str, Any]) -> Dict[str, Any]:
    market = _upper(signal.get("market"))
    estado = _estado_partido_texto(signal.get("estado_partido"))
    minuto = _safe_int(signal.get("minute"), 0)
    xg = _safe_float(signal.get("xG"), 0.0)
    shots_on_target = _safe_int(signal.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(signal.get("dangerous_attacks"), 0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)

    final_score = 0.0
    final_reason = "Sin lectura extra"

    if market == "OVER_NEXT_15_DYNAMIC":
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
        final_score += 46
        final_score -= xg * 12
        final_score -= shots_on_target * 4
        final_score -= dangerous_attacks * 0.35
        final_score -= goal_prob_10 * 0.35
        if estado in ("FRIO", "CONTROLADO", "MUERTO"):
            final_score += 18
        if minuto >= 60:
            final_score += 8
        final_reason = "El contexto final favorece cierre defensivo"

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
    over_final_score = 0.0
    under_final_score = 0.0

    if market == "OVER_MATCH_DYNAMIC":
        over_final_score = 74.0
        final_outcome_state = "SESGO_OVER"
        final_outcome_reason = "El modelo favorece más goles"
    elif market == "OVER_NEXT_15_DYNAMIC":
        over_final_score = 71.0
        final_outcome_state = "SESGO_OVER"
        final_outcome_reason = "El modelo favorece gol en la siguiente ventana"
    elif market == "UNDER_MATCH_DYNAMIC":
        under_final_score = 64.0
        final_outcome_state = "SESGO_UNDER"
        final_outcome_reason = "El modelo favorece cierre de marcador"

    if final_selection_recommended in (None, "", "None"):
        if market == "OVER_MATCH_DYNAMIC":
            final_selection_recommended = "Over partido"
        elif market == "UNDER_MATCH_DYNAMIC":
            final_selection_recommended = "Under partido"
        elif market == "OVER_NEXT_15_DYNAMIC":
            final_selection_recommended = "Over próximos 15 min"

    return {
        "final_selection_recommended": final_selection_recommended,
        "final_outcome_state": final_outcome_state,
        "final_outcome_reason": final_outcome_reason,
        "over_final_score": round(over_final_score, 2),
        "under_final_score": round(under_final_score, 2),
        "resultado_probable": resultado_probable,
        "ganador_probable": ganador_probable,
        "total_goles_estimado": round(total_goles_estimado, 2),
    }


# =========================================================
# OPERACION / RANKING
# =========================================================
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
    }


def _master_gate(partido: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    minute = _safe_int(partido.get("minuto"), 0)
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)
    market = _upper(signal.get("market"))
    xg = _safe_float(signal.get("xG"), 0.0)
    shots_on_target = _safe_int(signal.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(signal.get("dangerous_attacks"), 0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)
    apto_para_entrar = bool(signal.get("apto_para_entrar", True))
    ai_recommendation = _upper(signal.get("ai_recommendation"))
    odds_data_available = bool(signal.get("odds_data_available", False))
    odds_validation_ok = bool(signal.get("odds_validation_ok", False))

    blocked_reasons: List[str] = []

    mercados_permitidos = {
        "OVER_NEXT_15_DYNAMIC",
        "OVER_MATCH_DYNAMIC",
        "UNDER_MATCH_DYNAMIC",
    }

    if market not in mercados_permitidos:
        blocked_reasons.append("Mercado no permitido por estrategia actual")

    if not _es_minuto_operable(minute):
        blocked_reasons.append("Fuera de ventana operable")

    if confidence < 68:
        blocked_reasons.append("Confianza por debajo del mínimo")

    if value < 1.0:
        blocked_reasons.append("Value insuficiente")

    if not apto_para_entrar:
        blocked_reasons.append("Motor de riesgo no aprueba la entrada")

    if risk_score > 7.2:
        blocked_reasons.append("Riesgo operativo alto")

    if ai_recommendation == "NO_APOSTAR":
        blocked_reasons.append("IA bloquea la señal")

    if odds_data_available and not odds_validation_ok:
        blocked_reasons.append(f"Validación de odds fallida: {_safe_text(signal.get('market_validation_reason'))}")

    if market == "UNDER_MATCH_DYNAMIC":
        if minute < 60:
            blocked_reasons.append("Under demasiado temprano")
        if xg >= 1.35:
            blocked_reasons.append("Under incoherente con xG alto")
        if shots_on_target >= 3:
            blocked_reasons.append("Under incoherente con tiros al arco")
        if dangerous_attacks >= 16:
            blocked_reasons.append("Under incoherente con ataques peligrosos")
        if goal_prob_10 >= 40:
            blocked_reasons.append("Under incoherente con probabilidad de gol")

    publish_ready = len(blocked_reasons) == 0

    return {
        "publish_ready": publish_ready,
        "publish_blocked_reasons": blocked_reasons,
    }


def _ranking_layer(signal: Dict[str, Any]) -> Dict[str, Any]:
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    signal_score = _safe_float(signal.get("signal_score"), 0.0)
    ai_decision_score = _safe_float(signal.get("ai_decision_score"), 0.0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)
    market = _upper(signal.get("market"))
    minute = _safe_int(signal.get("minute"), 0)
    xg = _safe_float(signal.get("xG"), 0.0)
    shots_on_target = _safe_int(signal.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(signal.get("dangerous_attacks"), 0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)

    ranking_score_base = (
        ai_decision_score * 1.70 +
        signal_score * 1.35 +
        confidence * 1.10 +
        value * 2.00 +
        tactical_score * 0.75
    )

    ranking_penalty = risk_score * 9.0

    if minute >= 85:
        ranking_penalty += 8
    elif minute >= 80:
        ranking_penalty += 4

    if market == "UNDER_MATCH_DYNAMIC":
        if xg >= 1.30:
            ranking_penalty += 18
        if shots_on_target >= 3:
            ranking_penalty += 12
        if dangerous_attacks >= 16:
            ranking_penalty += 12
        if goal_prob_10 >= 40:
            ranking_penalty += 12

    ranking_score = round(ranking_score_base - ranking_penalty, 2)
    qualifies_for_top = ranking_score >= 140

    publish_rank = 3
    if ranking_score >= 340:
        publish_rank = 1
    elif ranking_score >= 240:
        publish_rank = 2

    return {
        "ranking_score_base": round(ranking_score_base, 2),
        "ranking_penalty": round(ranking_penalty, 2),
        "ranking_score": ranking_score,
        "qualifies_for_top": qualifies_for_top,
        "publish_rank": publish_rank,
    }


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

        if _upper(signal.get("market")) not in {
            "OVER_NEXT_15_DYNAMIC",
            "OVER_MATCH_DYNAMIC",
            "UNDER_MATCH_DYNAMIC",
        }:
            print(f"[PIPELINE] mercado no permitido -> {signal.get('market')}")
            return None

        # Defaults odds
        signal["odds_data_available"] = False
        signal["odds_validation_ok"] = False
        signal["market_validation_reason"] = "Sin validación externa"
        signal["odds_selected_bookmaker"] = ""
        signal["odds_selected_line"] = 0.0
        signal["odds_selected_price"] = 0.0
        signal["odds_implied_probability"] = 0.0
        signal["market_edge_with_odds"] = 0.0
        signal["odds_side"] = ""
        signal["market_validation_codes"] = []

        # Contexto auxiliar
        signal.update(_build_context_state(partido))
        signal.update(_build_emotion_state(partido))
        signal.update(_build_tempo_state(partido))
        signal.update(_build_player_state(partido))
        signal.update(_build_arbiter_state(partido))

        # Sesgos
        signal.update(_market_bias(signal))
        signal.update(_final_outcome_bias(signal))

        # Scores base
        signal.update(_calcular_scores_core(signal, partido))

        # Riesgo oficial
        if evaluar_riesgo:
            try:
                risk_data = evaluar_riesgo(partido, signal)
                if isinstance(risk_data, dict):
                    signal.update(risk_data)
            except Exception as e:
                print(f"[PIPELINE] ERROR evaluar_riesgo -> {e}")

        signal.setdefault("risk_score", 5.5)
        signal.setdefault("risk_level", "MEDIO")
        signal.setdefault("apto_para_entrar", True)
        signal.setdefault("motivos_riesgo", [])

        # IA oficial
        if decision_final_ia:
            try:
                brain = decision_final_ia(partido, signal)
                if isinstance(brain, dict):
                    signal.update(brain)
                    signal["confidence"] = round(
                        _safe_float(brain.get("ai_confidence_final"), signal.get("confidence", 0.0)),
                        2
                    )
            except Exception as e:
                print(f"[PIPELINE] ERROR decision_final_ia -> {e}")

        signal.setdefault("ai_state", "NEUTRO")
        signal.setdefault("ai_score", 55.0)
        signal.setdefault("ai_reason", "Contexto mixto sin lectura extrema")
        signal.setdefault("ai_fit", "NEUTRO")
        signal.setdefault("ai_fit_reason", "Sin ajuste especial")
        signal.setdefault("ai_confidence_adjustment", 0.0)
        signal.setdefault("ai_confidence_final", _safe_float(signal.get("confidence"), 0.0))
        signal.setdefault("ai_decision_score", 0.0)
        signal.setdefault("ai_recommendation", "OBSERVAR")

        # Signal score final antes de odds
        signal.update(_recalcular_signal_score(signal))

        # Operación
        signal.update(_build_operation_fields(signal))
        signal["decision_ia"] = _upper(signal.get("ai_recommendation", "OBSERVAR"))

        # =========================================================
        # VALIDACION CON THE ODDS API
        # =========================================================
        if obtener_odds_partido and validar_mercado_con_odds:
            try:
                odds_payload = obtener_odds_partido(
                    local=_safe_text(partido.get("local")),
                    visitante=_safe_text(partido.get("visitante")),
                    league=_safe_text(partido.get("liga")),
                    country=_safe_text(partido.get("pais")),
                )

                odds_validation = validar_mercado_con_odds(signal, odds_payload)
                if isinstance(odds_validation, dict):
                    signal.update(odds_validation)

                # =====================================================
                # SI EXISTEN ODDS REALES, REEMPLAZAR CUOTA FIJA 1.85
                # =====================================================
                if signal.get("odds_data_available", False):
                    real_price = _safe_float(signal.get("odds_selected_price"), 0.0)
                    real_imp = _safe_float(signal.get("odds_implied_probability"), 0.0)
                    real_edge = _safe_float(signal.get("market_edge_with_odds"), 0.0)

                    if real_price > 0:
                        signal["odd"] = round(real_price, 2)
                        signal["cuota"] = round(real_price, 2)

                    if real_imp > 0:
                        signal["prob_implicita"] = round(real_imp, 4)

                    # usar edge real de mercado como value mostrado
                    if real_edge != 0:
                        signal["value"] = round(real_edge, 2)
                        signal["valor"] = round(real_edge, 2)

                    # recalcular signal score con value real si aplica
                    signal.update(_recalcular_signal_score(signal))

            except Exception as e:
                print(f"[PIPELINE] ERROR validación odds -> {e}")

        # Gate final
        signal.update(_master_gate(partido, signal))

        if not signal.get("publish_ready", False):
            print(f"[PIPELINE] RECHAZADO MASTER GATE -> {partido.get('local')} vs {partido.get('visitante')}")
            print(f"[PIPELINE] BLOQUEOS -> {signal.get('publish_blocked_reasons', [])}")
            return None

        # Ranking
        signal.update(_ranking_layer(signal))

        if not signal.get("qualifies_for_top", False):
            print(f"[PIPELINE] FINAL RECHAZADO POR RANKING -> {partido.get('local')} vs {partido.get('visitante')}")
            return None

        # Razones finales
        signal.update(_build_reason_fields(partido, signal))

        signal["signal_status"] = "OPEN"
        signal["motivo_operacion"] = "OK"
        signal["senal_id"] = str(partido.get("id"))
        signal["hora_generada"] = "00:00:00"

        return signal

    except Exception as e:
        print(f"[PIPELINE] ERROR procesar_partido -> {e}")
        return None

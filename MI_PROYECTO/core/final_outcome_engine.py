from typing import Any, Dict


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


def _safe_upper(value: Any, default: str = "") -> str:
    return _safe_text(value, default).upper()


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


# =========================================================
# EXTRACTORES
# =========================================================
def _get_estado_partido(senal: Dict[str, Any]) -> str:
    estado_obj = senal.get("estado_partido") or {}
    if isinstance(estado_obj, dict):
        return _safe_upper(estado_obj.get("estado"), "NEUTRO")
    return _safe_upper(estado_obj, "NEUTRO")


def _get_goal_inminente_obj(senal: Dict[str, Any]) -> Dict[str, Any]:
    obj = senal.get("gol_inminente") or {}
    if isinstance(obj, dict):
        return obj
    return {}


def _get_context_state(senal: Dict[str, Any]) -> str:
    return _safe_upper(
        senal.get("context_state", senal.get("contexto_estado", "NEUTRO")),
        "NEUTRO",
    )


def _get_market(senal: Dict[str, Any]) -> str:
    return _safe_upper(senal.get("market", senal.get("mercado", "")))


def _get_selection(senal: Dict[str, Any]) -> str:
    return _safe_text(senal.get("selection", senal.get("apuesta", "")))


# =========================================================
# SCORE DE DESENLACE
# =========================================================
def _build_hold_result_score(partido: Dict[str, Any], senal: Dict[str, Any]) -> float:
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    score_text = _safe_text(senal.get("score", "0-0"))
    confidence = _safe_float(senal.get("confidence", 0.0))
    tactical_score = _safe_float(senal.get("tactical_score", 0.0))
    risk_score = _safe_float(senal.get("risk_score", 5.0))
    chaos_score = _safe_float(senal.get("chaos_score", 0.0))
    tempo_score = _safe_float(senal.get("tempo_score", 0.0))
    goal_score = _safe_float(senal.get("goal_inminente_score", 0.0))
    context_score = _safe_float(senal.get("context_score", 50.0))
    context_state = _get_context_state(senal)
    estado = _get_estado_partido(senal)

    try:
        home_goals, away_goals = score_text.split("-")
        diff = abs(_safe_int(home_goals, 0) - _safe_int(away_goals, 0))
        total_goals = _safe_int(home_goals, 0) + _safe_int(away_goals, 0)
    except Exception:
        diff = 0
        total_goals = 0

    score = 45.0
    score += confidence * 0.22
    score += tactical_score * 0.25
    score += context_score * 0.20
    score -= risk_score * 4.0
    score -= chaos_score * 2.5
    score -= goal_score * 0.45

    if minute >= 70:
        score += 5.0
    if minute >= 78:
        score += 4.0
    if minute >= 84:
        score += 3.0

    if diff >= 2:
        score += 8.0
    elif diff == 1:
        score += 4.0
    else:
        score -= 2.0

    if total_goals >= 4:
        score -= 3.0

    if tempo_score >= 80:
        score -= 6.0
    elif tempo_score >= 65:
        score -= 3.0
    elif tempo_score <= 20:
        score += 5.0

    if estado in {"FRIO", "CONTROLADO", "MUERTO"}:
        score += 6.0
    elif estado in {"CALIENTE", "EXPLOSIVO", "CAOS"}:
        score -= 6.0

    if context_state in {"CIERRE_DE_RESULTADO", "VENTANA_LOCAL_CONTROLABLE", "VENTANA_VISITANTE_CONTROLABLE"}:
        score += 10.0
    elif context_state in {"EMPATE_ABIERTO", "PARTIDO_ROTO", "FINAL_CAOTICO"}:
        score -= 10.0

    return round(_clamp(score, 0.0, 100.0), 2)


def _build_next_goal_score(partido: Dict[str, Any], senal: Dict[str, Any]) -> float:
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    tactical_score = _safe_float(senal.get("tactical_score", 0.0))
    goal_score = _safe_float(senal.get("goal_inminente_score", 0.0))
    tempo_score = _safe_float(senal.get("tempo_score", 0.0))
    chaos_score = _safe_float(senal.get("chaos_score", 0.0))
    risk_score = _safe_float(senal.get("risk_score", 5.0))
    confidence = _safe_float(senal.get("confidence", 0.0))
    estado = _get_estado_partido(senal)
    context_state = _get_context_state(senal)
    gi = _get_goal_inminente_obj(senal)

    goal_prob_5 = _safe_float(senal.get("goal_prob_5", gi.get("goal_prob_5", 0.0)))
    goal_prob_10 = _safe_float(senal.get("goal_prob_10", gi.get("goal_prob_10", 0.0)))
    dangerous = _safe_float(partido.get("dangerous_attacks", 0.0))
    shots_on_target = _safe_float(partido.get("shots_on_target", 0.0))
    xg = _safe_float(partido.get("xG", 0.0))

    score = 10.0
    score += goal_score * 0.75
    score += goal_prob_5 * 0.35
    score += goal_prob_10 * 0.28
    score += tactical_score * 0.20
    score += tempo_score * 0.18
    score += confidence * 0.10
    score += dangerous * 0.25
    score += shots_on_target * 2.2
    score += xg * 10.0
    score -= risk_score * 2.2

    if minute < 20:
        score -= 6.0
    elif 25 <= minute <= 45:
        score += 4.0
    elif 60 <= minute <= 78:
        score += 7.0
    elif minute > 85:
        score -= 5.0

    if estado in {"CALIENTE", "EXPLOSIVO", "CAOS"}:
        score += 8.0
    elif estado in {"FRIO", "MUERTO"}:
        score -= 10.0

    if context_state in {"PARTIDO_ROTO", "GOL_TARDIO_PROBABLE", "EMPATE_ABIERTO"}:
        score += 9.0
    elif context_state in {"CIERRE_DE_RESULTADO"}:
        score -= 7.0

    if chaos_score >= 7.0:
        score -= 4.0

    return round(_clamp(score, 0.0, 100.0), 2)


def _build_over_final_score(partido: Dict[str, Any], senal: Dict[str, Any]) -> float:
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    xg = _safe_float(partido.get("xG", 0.0))
    tactical_score = _safe_float(senal.get("tactical_score", 0.0))
    goal_score = _safe_float(senal.get("goal_inminente_score", 0.0))
    tempo_score = _safe_float(senal.get("tempo_score", 0.0))
    confidence = _safe_float(senal.get("confidence", 0.0))
    dangerous = _safe_float(partido.get("dangerous_attacks", 0.0))
    shots = _safe_float(partido.get("shots", 0.0))
    shots_on_target = _safe_float(partido.get("shots_on_target", 0.0))
    estado = _get_estado_partido(senal)
    context_state = _get_context_state(senal)

    score = 12.0
    score += xg * 11.0
    score += tactical_score * 0.18
    score += goal_score * 0.55
    score += tempo_score * 0.22
    score += dangerous * 0.18
    score += shots * 0.45
    score += shots_on_target * 2.0
    score += confidence * 0.08

    if 25 <= minute <= 45:
        score += 3.0
    if 60 <= minute <= 80:
        score += 5.0

    if estado in {"EXPLOSIVO", "CALIENTE"}:
        score += 7.0
    elif estado in {"FRIO", "MUERTO"}:
        score -= 9.0

    if context_state in {"PARTIDO_ROTO", "GOL_TARDIO_PROBABLE", "EMPATE_ABIERTO"}:
        score += 6.0
    elif context_state in {"CIERRE_DE_RESULTADO"}:
        score -= 6.0

    return round(_clamp(score, 0.0, 100.0), 2)


def _build_under_final_score(partido: Dict[str, Any], senal: Dict[str, Any], hold_score: float) -> float:
    tempo_score = _safe_float(senal.get("tempo_score", 0.0))
    goal_score = _safe_float(senal.get("goal_inminente_score", 0.0))
    estado = _get_estado_partido(senal)
    context_state = _get_context_state(senal)

    score = 25.0
    score += hold_score * 0.55
    score -= tempo_score * 0.18
    score -= goal_score * 0.30

    if estado in {"FRIO", "CONTROLADO", "MUERTO"}:
        score += 8.0
    elif estado in {"EXPLOSIVO", "CALIENTE"}:
        score -= 8.0

    if context_state in {"CIERRE_DE_RESULTADO", "VENTANA_LOCAL_CONTROLABLE", "VENTANA_VISITANTE_CONTROLABLE"}:
        score += 8.0
    elif context_state in {"PARTIDO_ROTO", "EMPATE_ABIERTO"}:
        score -= 7.0

    return round(_clamp(score, 0.0, 100.0), 2)


def _build_draw_final_score(partido: Dict[str, Any], senal: Dict[str, Any]) -> float:
    score_text = _safe_text(senal.get("score", "0-0"))
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    context_state = _get_context_state(senal)
    hold_score = _safe_float(senal.get("hold_result_score", 0.0))
    goal_score = _safe_float(senal.get("goal_inminente_score", 0.0))

    try:
        home_goals, away_goals = score_text.split("-")
        hg = _safe_int(home_goals, 0)
        ag = _safe_int(away_goals, 0)
    except Exception:
        hg = 0
        ag = 0

    score = 8.0

    if hg == ag:
        score += 35.0
    elif abs(hg - ag) == 1:
        score += 8.0

    if minute >= 70:
        score += 6.0

    if context_state == "EMPATE_ABIERTO":
        score += 14.0
    elif context_state == "CIERRE_DE_RESULTADO":
        score -= 8.0

    score += hold_score * 0.12
    score -= goal_score * 0.20

    return round(_clamp(score, 0.0, 100.0), 2)


def _build_home_win_score(partido: Dict[str, Any], senal: Dict[str, Any]) -> float:
    score_text = _safe_text(senal.get("score", "0-0"))
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    context_state = _get_context_state(senal)
    hold_score = _safe_float(senal.get("hold_result_score", 0.0))

    try:
        home_goals, away_goals = score_text.split("-")
        hg = _safe_int(home_goals, 0)
        ag = _safe_int(away_goals, 0)
    except Exception:
        hg = 0
        ag = 0

    score = 15.0
    if hg > ag:
        score += 28.0
    elif hg == ag:
        score += 6.0

    if minute >= 70:
        score += 4.0

    if context_state in {"CONTROL_LOCAL", "VENTANA_LOCAL_CONTROLABLE", "CIERRE_DE_RESULTADO"}:
        score += 10.0

    score += hold_score * 0.18
    return round(_clamp(score, 0.0, 100.0), 2)


def _build_away_win_score(partido: Dict[str, Any], senal: Dict[str, Any]) -> float:
    score_text = _safe_text(senal.get("score", "0-0"))
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    context_state = _get_context_state(senal)
    hold_score = _safe_float(senal.get("hold_result_score", 0.0))

    try:
        home_goals, away_goals = score_text.split("-")
        hg = _safe_int(home_goals, 0)
        ag = _safe_int(away_goals, 0)
    except Exception:
        hg = 0
        ag = 0

    score = 15.0
    if ag > hg:
        score += 28.0
    elif hg == ag:
        score += 6.0

    if minute >= 70:
        score += 4.0

    if context_state in {"CONTROL_VISITANTE", "VENTANA_VISITANTE_CONTROLABLE", "CIERRE_DE_RESULTADO"}:
        score += 10.0

    score += hold_score * 0.18
    return round(_clamp(score, 0.0, 100.0), 2)


# =========================================================
# CLASIFICADOR DE ESCENARIO
# =========================================================
def _clasificar_escenario(partido: Dict[str, Any], senal: Dict[str, Any]) -> Dict[str, Any]:
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    tactical_score = _safe_float(senal.get("tactical_score", 0.0))
    goal_score = _safe_float(senal.get("goal_inminente_score", 0.0))
    tempo_score = _safe_float(senal.get("tempo_score", 0.0))
    risk_score = _safe_float(senal.get("risk_score", 5.0))
    estado = _get_estado_partido(senal)
    context_state = _get_context_state(senal)
    score_text = _safe_text(senal.get("score", "0-0"))

    try:
        home_goals, away_goals = score_text.split("-")
        diff = abs(_safe_int(home_goals, 0) - _safe_int(away_goals, 0))
        empate = _safe_int(home_goals, 0) == _safe_int(away_goals, 0)
    except Exception:
        diff = 0
        empate = True

    escenario = "SIN_VENTAJA"
    razon = "Sin patrón fuerte detectado"

    if minute >= 70 and diff >= 1 and goal_score <= 45 and tempo_score <= 40:
        escenario = "CIERRE_DE_RESULTADO"
        razon = "Marcador con margen y ritmo contenido"
    elif minute >= 70 and empate and goal_score >= 55:
        escenario = "EMPATE_ABIERTO"
        razon = "Empate con opciones reales de ruptura"
    elif goal_score >= 65 and tactical_score >= 30:
        escenario = "GOL_TARDIO_PROBABLE"
        razon = "Presión ofensiva real y ventana de gol activa"
    elif estado in {"EXPLOSIVO", "CAOS"} and tempo_score >= 70:
        escenario = "PARTIDO_ROTO"
        razon = "Partido de ida y vuelta con alta volatilidad"
    elif context_state in {"VENTANA_LOCAL_CONTROLABLE", "CONTROL_LOCAL"}:
        escenario = "CONTROL_LOCAL"
        razon = "Contexto favorece control local"
    elif context_state in {"VENTANA_VISITANTE_CONTROLABLE", "CONTROL_VISITANTE"}:
        escenario = "CONTROL_VISITANTE"
        razon = "Contexto favorece control visitante"
    elif risk_score >= 7:
        escenario = "FINAL_CAOTICO"
        razon = "Riesgo alto y desenlace poco limpio"

    return {
        "final_outcome_state": escenario,
        "final_outcome_reason": razon,
    }


# =========================================================
# SELECTOR DE MERCADO SEGURO
# =========================================================
def _elegir_mercado_seguro(partido: Dict[str, Any], senal: Dict[str, Any]) -> Dict[str, Any]:
    minute = _safe_int(partido.get("minuto", senal.get("minute", 0)), 0)
    hold_score = _safe_float(senal.get("hold_result_score", 0.0))
    next_goal_score = _safe_float(senal.get("next_goal_score", 0.0))
    over_score = _safe_float(senal.get("over_final_score", 0.0))
    under_score = _safe_float(senal.get("under_final_score", 0.0))
    confidence = _safe_float(senal.get("confidence", 0.0))
    value = _safe_float(senal.get("value", 0.0))
    risk_score = _safe_float(senal.get("risk_score", 10.0))
    escenario = _safe_upper(senal.get("final_outcome_state", "SIN_VENTAJA"))

    selected_market = _get_market(senal)
    selected_selection = _get_selection(senal)
    decision = _safe_upper(senal.get("ai_recommendation", senal.get("recomendacion_final", "OBSERVAR")), "OBSERVAR")
    reason = "Se mantiene la lectura del pipeline"

    if risk_score > 7.5:
        return {
            "final_market_recommended": "NO_APOSTAR",
            "final_selection_recommended": "No operar",
            "final_decision_recommended": "NO_APOSTAR",
            "final_market_reason": "Riesgo operativo demasiado alto",
        }

    if confidence < 64 or value < 1.5:
        return {
            "final_market_recommended": "NO_APOSTAR",
            "final_selection_recommended": "No operar",
            "final_decision_recommended": "NO_APOSTAR",
            "final_market_reason": "Confianza o value insuficiente",
        }

    if minute >= 70:
        if hold_score >= 68 and hold_score >= next_goal_score + 8:
            selected_market = "RESULT_HOLDS_NEXT_15"
            selected_selection = "Se mantiene el resultado próximos 15 min"
            decision = "APOSTAR"
            reason = "El final del partido favorece la conservación del marcador"

        elif next_goal_score >= 70 and next_goal_score >= hold_score + 6:
            selected_market = "NEXT_GOAL"
            selected_selection = "Habrá gol (próximo)"
            decision = "APOSTAR_FUERTE" if next_goal_score >= 80 else "APOSTAR"
            reason = "Hay presión real y ventana de gol en el tramo final"

        elif over_score >= 72 and over_score >= under_score + 8:
            selected_market = "OVER_MATCH_DYNAMIC"
            selected_selection = "Más goles en el partido"
            decision = "APOSTAR"
            reason = "El contexto final favorece más goles"

        elif under_score >= 70 and under_score >= over_score + 8:
            selected_market = "UNDER_MATCH_DYNAMIC"
            selected_selection = "No habrá muchos más goles"
            decision = "APOSTAR_SUAVE"
            reason = "El contexto final favorece cierre defensivo"

    else:
        if escenario in {"GOL_TARDIO_PROBABLE", "PARTIDO_ROTO"} and next_goal_score >= 68:
            selected_market = "NEXT_GOAL"
            selected_selection = "Habrá gol (próximo)"
            decision = "APOSTAR"
            reason = "El partido muestra patrón ofensivo utilizable"
        elif escenario == "CIERRE_DE_RESULTADO" and hold_score >= 66:
            selected_market = "RESULT_HOLDS_NEXT_15"
            selected_selection = "Se mantiene el resultado próximos 15 min"
            decision = "APOSTAR_SUAVE"
            reason = "El partido favorece estabilidad táctica"

    return {
        "final_market_recommended": selected_market,
        "final_selection_recommended": selected_selection,
        "final_decision_recommended": decision,
        "final_market_reason": reason,
    }


# =========================================================
# API PRINCIPAL
# =========================================================
def evaluar_desenlace_final(partido: Dict[str, Any], senal: Dict[str, Any]) -> Dict[str, Any]:
    escenario = _clasificar_escenario(partido, senal)

    hold_score = _build_hold_result_score(partido, senal)
    senal_temp = dict(senal)
    senal_temp.update(escenario)
    senal_temp["hold_result_score"] = hold_score

    next_goal_score = _build_next_goal_score(partido, senal_temp)
    senal_temp["next_goal_score"] = next_goal_score

    over_final_score = _build_over_final_score(partido, senal_temp)
    under_final_score = _build_under_final_score(partido, senal_temp, hold_score)
    draw_final_score = _build_draw_final_score(partido, senal_temp)
    home_win_score = _build_home_win_score(partido, senal_temp)
    away_win_score = _build_away_win_score(partido, senal_temp)

    senal_temp["over_final_score"] = over_final_score
    senal_temp["under_final_score"] = under_final_score
    senal_temp["draw_final_score"] = draw_final_score
    senal_temp["home_win_score"] = home_win_score
    senal_temp["away_win_score"] = away_win_score

    market_pick = _elegir_mercado_seguro(partido, senal_temp)

    resultado_probable = "EMPATE"
    max_result_score = max(draw_final_score, home_win_score, away_win_score)
    if max_result_score == home_win_score:
        resultado_probable = "LOCAL"
    elif max_result_score == away_win_score:
        resultado_probable = "VISITANTE"

    total_goals_bias = "UNDER"
    if over_final_score > under_final_score:
        total_goals_bias = "OVER"

    return {
        "final_outcome_state": escenario["final_outcome_state"],
        "final_outcome_reason": escenario["final_outcome_reason"],

        "hold_result_score": hold_score,
        "next_goal_score": next_goal_score,
        "over_final_score": over_final_score,
        "under_final_score": under_final_score,
        "draw_final_score": draw_final_score,
        "home_win_score": home_win_score,
        "away_win_score": away_win_score,

        "prob_mantener_resultado": round(hold_score, 2),
        "prob_proximo_gol": round(next_goal_score, 2),
        "prob_over_final": round(over_final_score, 2),
        "prob_under_final": round(under_final_score, 2),
        "prob_empate_final": round(draw_final_score, 2),
        "prob_local_final": round(home_win_score, 2),
        "prob_visitante_final": round(away_win_score, 2),

        "resultado_final_probable": resultado_probable,
        "total_goles_bias": total_goals_bias,

        "final_market_recommended": market_pick["final_market_recommended"],
        "final_selection_recommended": market_pick["final_selection_recommended"],
        "final_decision_recommended": market_pick["final_decision_recommended"],
        "final_market_reason": market_pick["final_market_reason"],
    }


def aplicar_desenlace_final_a_senal(senal: Dict[str, Any], final_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(final_data, dict):
        return senal

    updated = dict(senal)
    updated.update(final_data)

    # No pisa a la fuerza lo anterior, pero sí mejora cuando la lectura final es fuerte.
    final_market = _safe_upper(final_data.get("final_market_recommended", ""))
    final_selection = _safe_text(final_data.get("final_selection_recommended", ""))
    final_decision = _safe_upper(final_data.get("final_decision_recommended", ""))
    final_reason = _safe_text(final_data.get("final_market_reason", ""))

    hold_score = _safe_float(final_data.get("hold_result_score", 0.0))
    next_goal_score = _safe_float(final_data.get("next_goal_score", 0.0))
    over_score = _safe_float(final_data.get("over_final_score", 0.0))
    under_score = _safe_float(final_data.get("under_final_score", 0.0))

    strongest = max(hold_score, next_goal_score, over_score, under_score)

    if strongest >= 70 and final_market and final_market != "NO_APOSTAR":
        updated["market"] = final_market
        updated["selection"] = final_selection
        updated["recomendacion_final"] = final_decision
        updated["ai_recommendation"] = final_decision
        updated["reason_final_outcome"] = final_reason

    if final_market == "NO_APOSTAR":
        # No bloqueamos brutalmente. Solo bajamos prioridad.
        updated["publish_ready"] = bool(updated.get("publish_ready", True))
        updated["publish_rank"] = int(updated.get("publish_rank", 1) or 1) + 2
        updated["reason_final_outcome"] = final_reason

    return updated

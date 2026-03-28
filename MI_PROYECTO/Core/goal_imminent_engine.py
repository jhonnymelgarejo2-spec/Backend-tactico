from typing import Dict, Any, List

try:
    from history_store import cargar_historial
except Exception:
    try:
        from core.history_store import cargar_historial
    except Exception:
        cargar_historial = None


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


def _es_over_market(signal: Dict[str, Any]) -> bool:
    market = _upper(signal.get("market"))
    selection = _upper(signal.get("selection"))

    over_keywords = [
        "OVER",
        "NEXT_GOAL",
        "GOAL",
    ]
    return any(k in market or k in selection for k in over_keywords)


def _es_under_market(signal: Dict[str, Any]) -> bool:
    market = _upper(signal.get("market"))
    selection = _upper(signal.get("selection"))
    return "UNDER" in market or "UNDER" in selection


def _obtener_historial_partido(match_id: str) -> List[Dict[str, Any]]:
    if not cargar_historial:
        return []

    try:
        historial = cargar_historial()
        if not isinstance(historial, list):
            return []
        return [
            item for item in historial
            if _safe_text(item.get("match_id")) == _safe_text(match_id)
        ]
    except Exception:
        return []


def _obtener_ultimo_registro(match_id: str) -> Dict[str, Any]:
    registros = _obtener_historial_partido(match_id)
    if not registros:
        return {}

    registros.sort(
        key=lambda x: _safe_int(x.get("minute"), 0),
        reverse=True
    )
    return registros[0]


def _parse_score(score_text: str) -> int:
    try:
        a, b = str(score_text).split("-")
        return _safe_int(a, 0) + _safe_int(b, 0)
    except Exception:
        return 0


def _nueva_fase_ofensiva_real(partido: Dict[str, Any], signal: Dict[str, Any]) -> bool:
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    pressure_score = _safe_float((partido.get("goal_pressure") or {}).get("pressure_score"), 0.0)
    predictor_score = _safe_float((partido.get("goal_predictor") or {}).get("predictor_score"), 0.0)
    confidence = _safe_float(signal.get("confidence"), 0.0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)
    tempo_state = _upper(signal.get("tempo_state"))
    context_state = _upper(signal.get("context_state"))

    puntos = 0

    if xg >= 2.4:
        puntos += 2
    elif xg >= 1.8:
        puntos += 1

    if shots >= 14:
        puntos += 1

    if shots_on_target >= 5:
        puntos += 2
    elif shots_on_target >= 3:
        puntos += 1

    if dangerous_attacks >= 28:
        puntos += 2
    elif dangerous_attacks >= 20:
        puntos += 1

    if pressure_score >= 8:
        puntos += 1

    if predictor_score >= 8:
        puntos += 1

    if goal_prob_10 >= 65:
        puntos += 2
    elif goal_prob_10 >= 50:
        puntos += 1

    if confidence >= 88:
        puntos += 1

    if tempo_state == "ACELERADO":
        puntos += 1

    if context_state in ("EMPATE_ABIERTO", "PARTIDO_ABIERTO"):
        puntos += 1

    return puntos >= 5


def evaluar_post_goal_cooldown(partido: Dict[str, Any], signal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Bloquea señales recicladas o reentradas sucias después de:
    - un gol reciente
    - una señal previa del mismo partido
    - una oportunidad que probablemente ya se consumió

    No intenta adivinar resultado. Solo reduce reentradas falsas.
    """

    minute = _safe_int(partido.get("minuto"), 0)
    match_id = _safe_text(
        signal.get("match_id") or signal.get("senal_id") or partido.get("id")
    )

    market = _safe_text(signal.get("market"))
    selection = _safe_text(signal.get("selection"))
    current_score = f"{_safe_int(partido.get('marcador_local'), 0)}-{_safe_int(partido.get('marcador_visitante'), 0)}"
    current_goals = _parse_score(current_score)

    xg = _safe_float(partido.get("xG"), 0.0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    confidence = _safe_float(signal.get("confidence"), 0.0)

    result = {
        "post_goal_cooldown_block": False,
        "post_goal_cooldown_reason": "OK",
        "post_goal_cooldown_level": "NORMAL",
        "post_goal_cooldown_minutes_left": 0,
        "post_goal_requires_reset": False,
        "post_goal_same_market_block": False,
        "post_goal_recent_goal_block": False,
        "post_goal_recycled_signal_block": False,
    }

    if not match_id:
        return result

    ultimo = _obtener_ultimo_registro(match_id)
    if not ultimo:
        return result

    last_minute = _safe_int(ultimo.get("minute"), 0)
    last_market = _safe_text(ultimo.get("market"))
    last_selection = _safe_text(ultimo.get("selection"))
    last_score = _safe_text(ultimo.get("score"), "0-0")
    last_goals = _parse_score(last_score)

    minutes_since_last_signal = max(0, minute - last_minute)
    hubo_gol_reciente = current_goals > last_goals
    mismo_mercado = _upper(market) == _upper(last_market)
    misma_seleccion = _upper(selection) == _upper(last_selection)

    # =========================================================
    # 1. GOL RECIENTE -> ENFRIAR PARTIDO
    # =========================================================
    if hubo_gol_reciente and minutes_since_last_signal <= 6:
        result["post_goal_cooldown_block"] = True
        result["post_goal_recent_goal_block"] = True
        result["post_goal_requires_reset"] = True
        result["post_goal_cooldown_level"] = "ALTO"
        result["post_goal_cooldown_minutes_left"] = max(0, 6 - minutes_since_last_signal)
        result["post_goal_cooldown_reason"] = (
            "Gol reciente detectado: esperar nueva fase antes de volver a entrar"
        )
        return result

    # =========================================================
    # 2. MISMO MERCADO + MISMA IDEA MUY PRONTO = RECICLADA
    # =========================================================
    if mismo_mercado and misma_seleccion and minutes_since_last_signal <= 8:
        result["post_goal_cooldown_block"] = True
        result["post_goal_same_market_block"] = True
        result["post_goal_recycled_signal_block"] = True
        result["post_goal_cooldown_level"] = "MEDIO"
        result["post_goal_cooldown_minutes_left"] = max(0, 8 - minutes_since_last_signal)
        result["post_goal_cooldown_reason"] = (
            "Señal reciclada: mismo mercado y misma selección demasiado pronto"
        )
        return result

    # =========================================================
    # 3. OVER DESPUÉS DE PARTIDO YA EXPLOTADO
    # =========================================================
    if _es_over_market(signal):
        partido_explotado = current_goals >= 3 and minute >= 60
        sin_nueva_fase = not _nueva_fase_ofensiva_real(partido, signal)

        if partido_explotado and sin_nueva_fase:
            result["post_goal_cooldown_block"] = True
            result["post_goal_recycled_signal_block"] = True
            result["post_goal_requires_reset"] = True
            result["post_goal_cooldown_level"] = "MEDIO"
            result["post_goal_cooldown_reason"] = (
                "Partido ya explotado sin nueva fase ofensiva clara"
            )
            return result

    # =========================================================
    # 4. UNDER MUY PRONTO DESPUÉS DE GOL O CAOS
    # =========================================================
    if _es_under_market(signal):
        if hubo_gol_reciente and minutes_since_last_signal <= 8:
            result["post_goal_cooldown_block"] = True
            result["post_goal_recent_goal_block"] = True
            result["post_goal_cooldown_level"] = "ALTO"
            result["post_goal_cooldown_minutes_left"] = max(0, 8 - minutes_since_last_signal)
            result["post_goal_cooldown_reason"] = (
                "Under bloqueado: gol reciente cambia totalmente el contexto"
            )
            return result

        if xg >= 1.8 or shots_on_target >= 4 or dangerous_attacks >= 22:
            result["post_goal_cooldown_block"] = True
            result["post_goal_recycled_signal_block"] = True
            result["post_goal_cooldown_level"] = "MEDIO"
            result["post_goal_cooldown_reason"] = (
                "Under bloqueado: el partido sigue demasiado vivo para cierre inmediato"
            )
            return result

    # =========================================================
    # 5. REENTRADA DEMASIADO PRONTA SOLO SI NO HAY FASE NUEVA PREMIUM
    # =========================================================
    if minutes_since_last_signal <= 5:
        fase_premium = _nueva_fase_ofensiva_real(partido, signal) and confidence >= 90

        if not fase_premium:
            result["post_goal_cooldown_block"] = True
            result["post_goal_requires_reset"] = True
            result["post_goal_cooldown_level"] = "MEDIO"
            result["post_goal_cooldown_minutes_left"] = max(0, 5 - minutes_since_last_signal)
            result["post_goal_cooldown_reason"] = (
                "Muy pronto para reentrar y no hay nueva fase premium"
            )
            return result

    return result

# post_goal_cooldown_engine.py

from typing import Dict, Any


MATCH_MEMORY: Dict[str, Dict[str, Any]] = {}

DEFAULT_GOAL_COOLDOWN_MINUTES = 6
DEFAULT_SAME_MARKET_COOLDOWN_MINUTES = 8
DEFAULT_MINUTES_BETWEEN_SIGNALS = 4


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
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


def _match_id(partido: Dict[str, Any]) -> str:
    mid = _safe_text(partido.get("id"))
    if mid:
        return mid

    local = _safe_text(partido.get("local"), "LOCAL")
    visitante = _safe_text(partido.get("visitante"), "VISITANTE")
    return f"{local}__{visitante}"


def _score_tuple(partido: Dict[str, Any]) -> tuple[int, int]:
    return (
        _safe_int(partido.get("marcador_local"), 0),
        _safe_int(partido.get("marcador_visitante"), 0),
    )


def _state_for(match_id: str) -> Dict[str, Any]:
    if match_id not in MATCH_MEMORY:
        MATCH_MEMORY[match_id] = {
            "last_score": None,
            "last_seen_minute": None,
            "last_goal_minute": None,
            "cooldown_until": None,
            "last_published_market": "",
            "last_published_selection": "",
            "last_published_minute": None,
            "last_signal_minute": None,
        }
    return MATCH_MEMORY[match_id]


def _is_over_market(market: str) -> bool:
    market = _upper(market)
    return market in {"OVER_NEXT_15_DYNAMIC", "OVER_MATCH_DYNAMIC"}


def _is_under_market(market: str) -> bool:
    return _upper(market) == "UNDER_MATCH_DYNAMIC"


def evaluar_post_gol_y_reentrada(
    partido: Dict[str, Any],
    signal: Dict[str, Any] | None = None,
    goal_cooldown_minutes: int = DEFAULT_GOAL_COOLDOWN_MINUTES,
    same_market_cooldown_minutes: int = DEFAULT_SAME_MARKET_COOLDOWN_MINUTES,
    min_minutes_between_signals: int = DEFAULT_MINUTES_BETWEEN_SIGNALS,
) -> Dict[str, Any]:
    """
    Evalúa:
    1. si hubo cambio reciente de marcador
    2. si el partido está en cooldown post-gol
    3. si la señal actual es una reentrada demasiado rápida
    4. si se está repitiendo el mismo mercado demasiado pronto
    """

    match_id = _match_id(partido)
    state = _state_for(match_id)

    minute = _safe_int(partido.get("minuto"), 0)
    score_now = _score_tuple(partido)
    score_prev = state.get("last_score")

    market = _upper((signal or {}).get("market"))
    selection = _safe_text((signal or {}).get("selection"))
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    xg = float(partido.get("xG", 0) or 0)

    score_changed_now = False
    recent_goal_detected = False
    cooldown_active = False
    same_market_reentry = False
    too_fast_reentry = False
    new_phase_confirmed = False
    block_signal = False

    reasons: list[str] = []

    if score_prev is not None and score_prev != score_now:
        score_changed_now = True
        state["last_goal_minute"] = minute
        state["cooldown_until"] = minute + goal_cooldown_minutes

    last_goal_minute = state.get("last_goal_minute")
    cooldown_until = state.get("cooldown_until")

    if last_goal_minute is not None:
        if minute - _safe_int(last_goal_minute, -999) <= goal_cooldown_minutes:
            recent_goal_detected = True

    if cooldown_until is not None and minute <= _safe_int(cooldown_until, -999):
        cooldown_active = True

    last_signal_minute = state.get("last_signal_minute")
    if last_signal_minute is not None:
        if minute - _safe_int(last_signal_minute, -999) < min_minutes_between_signals:
            too_fast_reentry = True

    last_market = _upper(state.get("last_published_market"))
    last_market_minute = state.get("last_published_minute")
    if market and last_market == market and last_market_minute is not None:
        if minute - _safe_int(last_market_minute, -999) <= same_market_cooldown_minutes:
            same_market_reentry = True

    # Confirmación de nueva fase real:
    # solo permite pensar en nueva entrada si reaparece producción fuerte
    # después del gol/cooldown.
    if dangerous_attacks >= 18 and shots_on_target >= 2 and xg >= 1.4:
        new_phase_confirmed = True

    if score_changed_now:
        reasons.append("Cambio reciente de marcador: posible señal reciclada")

    if cooldown_active:
        reasons.append("Cooldown post-gol activo")

    if too_fast_reentry:
        reasons.append("Reentrada demasiado rápida en el mismo partido")

    if same_market_reentry:
        reasons.append("Mismo mercado repetido demasiado pronto")

    # Bloqueo principal
    if cooldown_active and not new_phase_confirmed:
        block_signal = True

    if same_market_reentry and recent_goal_detected:
        block_signal = True

    if too_fast_reentry:
        block_signal = True

    # Ajustes por tipo de mercado
    if _is_over_market(market):
        if recent_goal_detected and not new_phase_confirmed:
            block_signal = True
            if "Post-gol sin nueva fase ofensiva confirmada" not in reasons:
                reasons.append("Post-gol sin nueva fase ofensiva confirmada")

    if _is_under_market(market):
        # under inmediatamente después de un gol reciente suele ser mala lectura
        if recent_goal_detected and minute - _safe_int(last_goal_minute, minute) <= 4:
            block_signal = True
            reasons.append("Under demasiado pronto después de un gol")

    anti_trap_reason = "OK"
    if block_signal:
        anti_trap_reason = " | ".join(reasons) if reasons else "Bloqueo anti-trampa"

    return {
        "anti_trap_match_id": match_id,
        "anti_trap_score_changed_now": score_changed_now,
        "anti_trap_recent_goal": recent_goal_detected,
        "anti_trap_cooldown_active": cooldown_active,
        "anti_trap_same_market_reentry": same_market_reentry,
        "anti_trap_too_fast_reentry": too_fast_reentry,
        "anti_trap_new_phase_confirmed": new_phase_confirmed,
        "anti_trap_block_signal": block_signal,
        "anti_trap_reason": anti_trap_reason,
        "anti_trap_goal_cooldown_minutes": goal_cooldown_minutes,
        "anti_trap_same_market_cooldown_minutes": same_market_cooldown_minutes,
        "anti_trap_last_goal_minute": last_goal_minute,
        "anti_trap_cooldown_until": cooldown_until,
    }


def registrar_senal_publicada(partido: Dict[str, Any], signal: Dict[str, Any]) -> None:
    match_id = _match_id(partido)
    state = _state_for(match_id)

    minute = _safe_int(partido.get("minuto"), 0)
    score_now = _score_tuple(partido)

    state["last_published_market"] = _upper(signal.get("market"))
    state["last_published_selection"] = _safe_text(signal.get("selection"))
    state["last_published_minute"] = minute
    state["last_signal_minute"] = minute
    state["last_score"] = score_now
    state["last_seen_minute"] = minute


def registrar_snapshot_partido(partido: Dict[str, Any]) -> None:
    match_id = _match_id(partido)
    state = _state_for(match_id)

    minute = _safe_int(partido.get("minuto"), 0)
    score_now = _score_tuple(partido)

    state["last_score"] = score_now
    state["last_seen_minute"] = minute


def limpiar_memoria_partido(match_id: str) -> None:
    MATCH_MEMORY.pop(_safe_text(match_id), None)
def evaluar_post_goal_cooldown(
    partido: Dict[str, Any],
    signal: Dict[str, Any] | None = None,
    goal_cooldown_minutes: int = DEFAULT_GOAL_COOLDOWN_MINUTES,
    same_market_cooldown_minutes: int = DEFAULT_SAME_MARKET_COOLDOWN_MINUTES,
    min_minutes_between_signals: int = DEFAULT_MINUTES_BETWEEN_SIGNALS,
) -> Dict[str, Any]:
    data = evaluar_post_gol_y_reentrada(
        partido=partido,
        signal=signal,
        goal_cooldown_minutes=goal_cooldown_minutes,
        same_market_cooldown_minutes=same_market_cooldown_minutes,
        min_minutes_between_signals=min_minutes_between_signals,
    )

    return {
        "post_goal_cooldown_block": bool(data.get("anti_trap_block_signal", False)),
        "post_goal_cooldown_reason": data.get("anti_trap_reason", "OK"),
        "post_goal_cooldown_level": (
            "ALTO" if data.get("anti_trap_block_signal", False)
            else "NORMAL"
        ),
        "post_goal_cooldown_minutes_left": max(
            0,
            _safe_int(data.get("anti_trap_cooldown_until"), 0) - _safe_int(partido.get("minuto"), 0)
        ) if data.get("anti_trap_cooldown_until") is not None else 0,
        "post_goal_requires_reset": bool(data.get("anti_trap_score_changed_now", False)),
        "post_goal_same_market_block": bool(data.get("anti_trap_same_market_reentry", False)),
        "post_goal_recent_goal_block": bool(data.get("anti_trap_recent_goal", False)),
        "post_goal_recycled_signal_block": bool(data.get("anti_trap_too_fast_reentry", False)),
        "anti_trap_match_id": data.get("anti_trap_match_id"),
        "anti_trap_score_changed_now": bool(data.get("anti_trap_score_changed_now", False)),
        "anti_trap_recent_goal": bool(data.get("anti_trap_recent_goal", False)),
        "anti_trap_cooldown_active": bool(data.get("anti_trap_cooldown_active", False)),
        "anti_trap_same_market_reentry": bool(data.get("anti_trap_same_market_reentry", False)),
        "anti_trap_too_fast_reentry": bool(data.get("anti_trap_too_fast_reentry", False)),
        "anti_trap_new_phase_confirmed": bool(data.get("anti_trap_new_phase_confirmed", False)),
        "anti_trap_block_signal": bool(data.get("anti_trap_block_signal", False)),
        "anti_trap_reason": data.get("anti_trap_reason", "OK"),
        "anti_trap_goal_cooldown_minutes": _safe_int(data.get("anti_trap_goal_cooldown_minutes"), DEFAULT_GOAL_COOLDOWN_MINUTES),
        "anti_trap_same_market_cooldown_minutes": _safe_int(data.get("anti_trap_same_market_cooldown_minutes"), DEFAULT_SAME_MARKET_COOLDOWN_MINUTES),
        "anti_trap_last_goal_minute": data.get("anti_trap_last_goal_minute"),
        "anti_trap_cooldown_until": data.get("anti_trap_cooldown_until"),
    }

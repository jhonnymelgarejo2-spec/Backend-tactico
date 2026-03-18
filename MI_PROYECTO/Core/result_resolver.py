from typing import Dict


# =========================================================
# HELPERS
# =========================================================
def _safe_upper(value) -> str:
    return str(value or "").strip().upper()


def _to_int(value, default=0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _parse_score(score_str: str):
    try:
        home, away = score_str.split("-")
        return int(home), int(away)
    except Exception:
        return 0, 0


# =========================================================
# CORE RESOLVER
# =========================================================
def resolver_resultado_senal(match: Dict, signal: Dict) -> str:
    """
    Devuelve:
    - WIN
    - LOSS
    - VOID
    """

    market = _safe_upper(signal.get("market"))
    selection = _safe_upper(signal.get("selection"))

    home_goals = _to_int(match.get("marcador_local", 0))
    away_goals = _to_int(match.get("marcador_visitante", 0))
    total_goals = home_goals + away_goals

    final_score = f"{home_goals}-{away_goals}"

    # Score al momento de la señal
    initial_score = signal.get("score", "0-0")
    init_home, init_away = _parse_score(initial_score)
    init_total = init_home + init_away

    resultado_probable = _safe_upper(signal.get("resultado_probable"))
    ganador_probable = _safe_upper(signal.get("ganador_probable"))
    over_under_probable = _safe_upper(signal.get("over_under_probable"))

    # =====================================================
    # 1. RESULT_HOLDS_NEXT_15
    # =====================================================
    if "RESULT_HOLDS" in market or "HOLD" in market:
        # gana si el marcador no cambió
        if final_score == initial_score:
            return "WIN"
        return "LOSS"

    # =====================================================
    # 2. NEXT_GOAL / GOAL
    # =====================================================
    if "NEXT_GOAL" in market or market == "GOAL":
        if total_goals > init_total:
            return "WIN"
        return "LOSS"

    # =====================================================
    # 3. OVER MATCH / OVER DINÁMICO
    # =====================================================
    if "OVER" in market and signal.get("line") is not None:
        try:
            line = float(signal.get("line"))
        except Exception:
            return "VOID"

        if total_goals > line:
            return "WIN"
        return "LOSS"

    # =====================================================
    # 4. UNDER MATCH
    # =====================================================
    if "UNDER" in market and signal.get("line") is not None:
        try:
            line = float(signal.get("line"))
        except Exception:
            return "VOID"

        if total_goals < line:
            return "WIN"
        return "LOSS"

    # =====================================================
    # 5. DOBLE OPORTUNIDAD
    # =====================================================
    if "DOBLE" in market or "DOUBLE" in market:
        if "1X" in selection or "LOCAL_O_EMPATE" in selection:
            return "WIN" if home_goals >= away_goals else "LOSS"

        if "X2" in selection or "EMPATE_O_VISITANTE" in selection:
            return "WIN" if away_goals >= home_goals else "LOSS"

        if "12" in selection or "LOCAL_O_VISITANTE" in selection:
            return "WIN" if home_goals != away_goals else "LOSS"

    # =====================================================
    # 6. GANADOR
    # =====================================================
    if "WINNER" in market or "GANADOR" in market:
        if ganador_probable == "LOCAL":
            return "WIN" if home_goals > away_goals else "LOSS"
        if ganador_probable == "VISITANTE":
            return "WIN" if away_goals > home_goals else "LOSS"
        if ganador_probable == "EMPATE":
            return "WIN" if home_goals == away_goals else "LOSS"

    # =====================================================
    # 7. RESULTADO EXACTO
    # =====================================================
    if "CORRECT_SCORE" in market or "RESULTADO" in market:
        if resultado_probable == _safe_upper(final_score):
            return "WIN"
        return "LOSS"

    # =====================================================
    # 8. OVER/UNDER PROBABLE (fallback inteligente)
    # =====================================================
    if over_under_probable:
        if "OVER 2.5" in over_under_probable:
            return "WIN" if total_goals > 2.5 else "LOSS"
        if "UNDER 2.5" in over_under_probable:
            return "WIN" if total_goals < 2.5 else "LOSS"
        if "OVER 3.5" in over_under_probable:
            return "WIN" if total_goals > 3.5 else "LOSS"
        if "UNDER 3.5" in over_under_probable:
            return "WIN" if total_goals < 3.5 else "LOSS"

    # =====================================================
    # DEFAULT
    # =====================================================
    return "VOID"

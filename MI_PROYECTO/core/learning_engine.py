from typing import Dict


def _safe_float(value, default=0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_str(value, default="") -> str:
    try:
        return str(value if value is not None else default).strip().upper()
    except Exception:
        return default


def _parse_score(score_text: str) -> tuple[int, int]:
    try:
        if not score_text or "-" not in str(score_text):
            return 0, 0
        a, b = str(score_text).split("-", 1)
        return _safe_int(a, 0), _safe_int(b, 0)
    except Exception:
        return 0, 0


def _market_contains(signal: Dict, text: str) -> bool:
    market = _safe_str(signal.get("market"))
    return text in market


def _selection_contains(signal: Dict, text: str) -> bool:
    selection = _safe_str(signal.get("selection"))
    return text in selection


def _get_final_score(match: Dict) -> tuple[int, int]:
    home_goals = _safe_int(match.get("marcador_local"), 0)
    away_goals = _safe_int(match.get("marcador_visitante"), 0)

    if "goals" in match and isinstance(match.get("goals"), dict):
        goals = match.get("goals") or {}
        home_goals = _safe_int(goals.get("home"), home_goals)
        away_goals = _safe_int(goals.get("away"), away_goals)

    return home_goals, away_goals


def _get_signal_score(signal: Dict) -> tuple[int, int]:
    score_at_signal = signal.get("score_at_signal") or signal.get("score") or "0-0"
    return _parse_score(score_at_signal)


def resolver_resultado_senal(match: Dict, signal: Dict) -> str:
    """
    Devuelve:
    - WIN
    - LOSS
    - VOID
    """
    if not isinstance(match, dict) or not isinstance(signal, dict):
        return "VOID"

    final_home, final_away = _get_final_score(match)
    signal_home, signal_away = _get_signal_score(signal)

    final_total = final_home + final_away
    signal_total = signal_home + signal_away

    market = _safe_str(signal.get("market"))
    selection = _safe_str(signal.get("selection"))
    line = signal.get("line")

    # =========================================================
    # 1. NEXT GOAL
    # =========================================================
    if market == "NEXT_GOAL":
        if final_total > signal_total:
            return "WIN"
        return "LOSS"

    # =========================================================
    # 2. RESULT_HOLDS_NEXT_15 / HOLD
    # Si el marcador final queda igual al marcador de la señal
    # =========================================================
    if "RESULT_HOLDS" in market or "HOLD" in market:
        if final_home == signal_home and final_away == signal_away:
            return "WIN"
        return "LOSS"

    # =========================================================
    # 3. OVER mercados
    # =========================================================
    if "OVER" in market:
        target_line = _safe_float(line, None)

        if target_line is None:
            # fallback simple si no viene línea
            if final_total > signal_total:
                return "WIN"
            return "LOSS"

        if final_total > target_line:
            return "WIN"
        return "LOSS"

    # =========================================================
    # 4. UNDER mercados
    # =========================================================
    if "UNDER" in market:
        target_line = _safe_float(line, None)

        if target_line is None:
            return "VOID"

        if final_total < target_line:
            return "WIN"
        return "LOSS"

    # =========================================================
    # 5. OVER/UNDER por selección textual
    # =========================================================
    if "OVER" in selection:
        target_line = _safe_float(line, None)
        if target_line is None:
            return "VOID"
        if final_total > target_line:
            return "WIN"
        return "LOSS"

    if "UNDER" in selection:
        target_line = _safe_float(line, None)
        if target_line is None:
            return "VOID"
        if final_total < target_line:
            return "WIN"
        return "LOSS"

    # =========================================================
    # 6. 1X2 / ganador probable
    # =========================================================
    if market in ("MATCH_WINNER", "1X2", "FULLTIME_RESULT"):
        if final_home > final_away and ("LOCAL" in selection or selection == "1"):
            return "WIN"
        if final_home == final_away and ("EMPATE" in selection or selection == "X"):
            return "WIN"
        if final_away > final_home and ("VISITANTE" in selection or selection == "2"):
            return "WIN"
        return "LOSS"

    # =========================================================
    # 7. DOUBLE CHANCE
    # =========================================================
    if market in ("DOUBLE_CHANCE", "DOBLE_OPORTUNIDAD"):
        if final_home > final_away:
            real = "1"
        elif final_home == final_away:
            real = "X"
        else:
            real = "2"

        if selection in ("1X", "LOCAL_O_EMPATE", "LOCAL/EMPATE") and real in ("1", "X"):
            return "WIN"
        if selection in ("X2", "EMPATE_O_VISITANTE", "EMPATE/VISITANTE") and real in ("X", "2"):
            return "WIN"
        if selection in ("12", "LOCAL_O_VISITANTE", "LOCAL/VISITANTE") and real in ("1", "2"):
            return "WIN"
        return "LOSS"

    # =========================================================
    # 8. BOTH TEAMS TO SCORE
    # =========================================================
    if market in ("BTTS", "BOTH_TEAMS_TO_SCORE"):
        both_scored = final_home > 0 and final_away > 0

        if selection in ("YES", "SI", "SÍ", "BTTS SI", "BTTS YES"):
            return "WIN" if both_scored else "LOSS"

        if selection in ("NO", "BTTS NO"):
            return "WIN" if not both_scored else "LOSS"

        return "VOID"

    # =========================================================
    # 9. EXACT SCORE
    # =========================================================
    if market in ("EXACT_SCORE", "MARCADOR_EXACTO"):
        expected = str(signal.get("selection") or "").strip()
        final_score = f"{final_home}-{final_away}"
        if expected == final_score:
            return "WIN"
        return "LOSS"

    # =========================================================
    # 10. TEAM TO SCORE NEXT / TEAM TO SCORE
    # =========================================================
    if market in ("TEAM_TO_SCORE_NEXT", "TEAM_TO_SCORE"):
        home_delta = final_home - signal_home
        away_delta = final_away - signal_away

        if "LOCAL" in selection or selection in ("HOME", "1"):
            if home_delta > 0 and away_delta <= 0:
                return "WIN"
            if home_delta <= 0:
                return "LOSS"

        if "VISITANTE" in selection or selection in ("AWAY", "2"):
            if away_delta > 0 and home_delta <= 0:
                return "WIN"
            if away_delta <= 0:
                return "LOSS"

        return "LOSS"

    # =========================================================
    # 11. FALLBACK SIMPLE
    # Si no reconoce el mercado, intenta por la selección
    # =========================================================
    if "SE MANTIENE EL RESULTADO" in selection:
        if final_home == signal_home and final_away == signal_away:
            return "WIN"
        return "LOSS"

    if "HABRÁ GOL" in selection or "PROXIMO GOL" in selection or "PRÓXIMO GOL" in selection:
        if final_total > signal_total:
            return "WIN"
        return "LOSS"

    return "VOID"

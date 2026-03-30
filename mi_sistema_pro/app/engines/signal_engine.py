# app/engines/signal_engine.py

from typing import Dict, Any, Optional

from app.config.config import settings
from app.utils.helpers import safe_float, safe_int, safe_text, clamp


# =========================================================
# HELPERS
# =========================================================
def _is_operable_minute(minuto: int) -> bool:
    return settings.MINUTE_MIN_OPERABLE <= minuto <= settings.MINUTE_MAX_OPERABLE


def _calc_value(prob_real: float, prob_implicita: float) -> float:
    return round((prob_real - prob_implicita) * 100, 2)


def _base_confidence(match: Dict[str, Any]) -> float:
    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    shots = safe_int(match.get("shots"), 0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    momentum = safe_text(match.get("momentum"), "MEDIO").upper()

    pressure_score = safe_float((match.get("goal_pressure") or {}).get("pressure_score"), 0.0)
    predictor_score = safe_float((match.get("goal_predictor") or {}).get("predictor_score"), 0.0)
    goal5 = safe_float((match.get("goal_predictor") or {}).get("goal_next_5_prob"), 0.0)
    goal10 = safe_float((match.get("goal_predictor") or {}).get("goal_next_10_prob"), 0.0)
    chaos_score = safe_float((match.get("chaos") or {}).get("chaos_score"), 0.0)

    confidence = 50.0

    if momentum == "MUY ALTO":
        confidence += 14
    elif momentum == "ALTO":
        confidence += 10
    elif momentum == "MEDIO":
        confidence += 5

    if xg >= 2.5:
        confidence += 14
    elif xg >= 1.8:
        confidence += 10
    elif xg >= 1.2:
        confidence += 7
    elif xg >= 0.8:
        confidence += 4

    if shots >= 12:
        confidence += 5
    elif shots >= 8:
        confidence += 3

    if shots_on_target >= 5:
        confidence += 7
    elif shots_on_target >= 3:
        confidence += 4
    elif shots_on_target >= 1:
        confidence += 2

    if dangerous_attacks >= 28:
        confidence += 6
    elif dangerous_attacks >= 18:
        confidence += 4
    elif dangerous_attacks >= 10:
        confidence += 2

    if pressure_score >= 8:
        confidence += 5
    elif pressure_score >= 5:
        confidence += 3

    if predictor_score >= 8:
        confidence += 4
    elif predictor_score >= 5:
        confidence += 2

    if goal5 >= 0.50:
        confidence += 5
    elif goal5 >= 0.30:
        confidence += 2

    if goal10 >= 0.60:
        confidence += 4
    elif goal10 >= 0.35:
        confidence += 2

    if chaos_score >= 8:
        confidence += 2

    if 15 <= minuto <= 35:
        confidence += 3
    elif 36 <= minuto <= 75:
        confidence += 6
    elif 76 <= minuto <= 88:
        confidence += 5

    return round(clamp(confidence, 35.0, 95.0), 2)


def _detect_match_state(match: Dict[str, Any]) -> Dict[str, Any]:
    minuto = safe_int(match.get("minuto"), 0)
    ml = safe_int(match.get("marcador_local"), 0)
    mv = safe_int(match.get("marcador_visitante"), 0)
    diff = abs(ml - mv)

    xg = safe_float(match.get("xG"), 0.0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    momentum = safe_text(match.get("momentum"), "MEDIO").upper()
    pressure_score = safe_float((match.get("goal_pressure") or {}).get("pressure_score"), 0.0)
    chaos_score = safe_float((match.get("chaos") or {}).get("chaos_score"), 0.0)
    goal10 = safe_float((match.get("goal_predictor") or {}).get("goal_next_10_prob"), 0.0)

    state = "NEUTRO"
    reason = "Lectura mixta"

    if minuto >= 85 and xg < 1.0 and shots_on_target <= 1 and momentum in ("BAJO", "MEDIO"):
        state = "MUERTO"
        reason = "Ritmo bajo y poco peligro real"

    elif xg >= 1.8 and shots_on_target >= 3 and dangerous_attacks >= 18:
        state = "EXPLOSIVO"
        reason = "Presión ofensiva fuerte"

    elif chaos_score >= 8 and pressure_score >= 6:
        state = "CAOS_UTIL"
        reason = "Partido roto con presión útil"

    elif minuto >= 65 and diff == 0 and (goal10 >= 0.30 or dangerous_attacks >= 16):
        state = "EMPATE_ABIERTO"
        reason = "Empate con riesgo de ruptura"

    elif minuto >= 65 and xg < 1.2 and shots_on_target <= 2 and dangerous_attacks < 14:
        state = "CERRADO"
        reason = "Partido con tendencia a cierre"

    return {
        "match_state": state,
        "match_state_reason": reason,
    }


def _signal_rank(signal_score: float) -> str:
    if signal_score >= 160:
        return "ELITE"
    if signal_score >= 120:
        return "TOP"
    if signal_score >= 90:
        return "ALTA"
    return "NORMAL"


def _base_signal_payload(
    match: Dict[str, Any],
    market: str,
    selection: str,
    line: float,
    confidence: float,
    value: float,
    signal_score: float,
    reason: str,
) -> Dict[str, Any]:
    prob_real = safe_float(match.get("prob_real"), 0.0)
    prob_implicita = safe_float(match.get("prob_implicita"), 0.0)
    cuota = safe_float(match.get("cuota"), 0.0)

    return {
        "match_id": safe_text(match.get("id")),
        "partido": f"{safe_text(match.get('local'))} vs {safe_text(match.get('visitante'))}",
        "market": market,
        "selection": selection,
        "line": line,
        "odd": cuota,
        "cuota": cuota,
        "prob_real": prob_real,
        "prob_implicita": prob_implicita,
        "confidence": confidence,
        "value": value,
        "valor": value,
        "risk_score": 5.0,
        "signal_score": signal_score,
        "signal_rank": _signal_rank(signal_score),
        "recomendacion_final": "OBSERVAR",
        "publish_ready": False,
        "reason": reason,
    }


# =========================================================
# BUILDERS
# =========================================================
def _build_over_next_15(match: Dict[str, Any], confidence: float, value: float, state: str, state_reason: str) -> Optional[Dict[str, Any]]:
    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    goal10 = safe_float((match.get("goal_predictor") or {}).get("goal_next_10_prob"), 0.0)

    score = confidence

    if xg >= 1.5:
        score += 8
    if shots_on_target >= 4:
        score += 7
    if dangerous_attacks >= 18:
        score += 6
    if goal10 >= 0.35:
        score += 6
    if state in ("EXPLOSIVO", "CAOS_UTIL", "EMPATE_ABIERTO"):
        score += 8

    score = round(clamp(score, 35.0, 95.0), 2)

    if minuto < 20 or minuto > 86:
        return None

    if xg >= 1.4 and shots_on_target >= 3 and dangerous_attacks >= 16:
        signal_score = round(score * 1.1 + value * 2.0, 2)
        return _base_signal_payload(
            match=match,
            market="OVER_NEXT_15_DYNAMIC",
            selection="Over próximos 15 min",
            line=0.5,
            confidence=score,
            value=value,
            signal_score=signal_score,
            reason=f"Presión ofensiva real | {state_reason}",
        )

    return None


def _build_under_match(match: Dict[str, Any], confidence: float, value: float, state: str, state_reason: str) -> Optional[Dict[str, Any]]:
    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    goal10 = safe_float((match.get("goal_predictor") or {}).get("goal_next_10_prob"), 0.0)
    total_goals = safe_int(match.get("marcador_local"), 0) + safe_int(match.get("marcador_visitante"), 0)

    score = confidence

    if minuto >= 65:
        score += 6
    if xg < 1.1:
        score += 8
    elif xg < 1.3:
        score += 4

    if shots_on_target <= 2:
        score += 6
    if dangerous_attacks < 14:
        score += 5
    if goal10 < 0.25:
        score += 5
    if state in ("CERRADO", "MUERTO"):
        score += 8

    if total_goals >= 3:
        score -= 14

    score = round(clamp(score, 35.0, 95.0), 2)

    if minuto < 65:
        return None

    if xg < 1.1 and shots_on_target <= 2 and dangerous_attacks < 14 and goal10 < 0.30:
        signal_score = round(score * 1.1 + value * 2.0, 2)
        return _base_signal_payload(
            match=match,
            market="UNDER_MATCH_DYNAMIC",
            selection="Under partido",
            line=max(2.5, total_goals + 0.5),
            confidence=score,
            value=value,
            signal_score=signal_score,
            reason=f"Cierre de partido | {state_reason}",
        )

    return None


def _build_over_match(match: Dict[str, Any], confidence: float, value: float, state: str, state_reason: str) -> Optional[Dict[str, Any]]:
    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    total_goals = safe_int(match.get("marcador_local"), 0) + safe_int(match.get("marcador_visitante"), 0)

    score = confidence

    if xg >= 1.6:
        score += 8
    if shots_on_target >= 3:
        score += 5
    if dangerous_attacks >= 18:
        score += 5
    if state in ("EXPLOSIVO", "CAOS_UTIL", "EMPATE_ABIERTO"):
        score += 7
    if total_goals <= 2:
        score += 4

    score = round(clamp(score, 35.0, 95.0), 2)

    if minuto < 15 or minuto > 80:
        return None

    if xg >= 1.5 and shots_on_target >= 3:
        signal_score = round(score * 1.1 + value * 2.0, 2)
        return _base_signal_payload(
            match=match,
            market="OVER_MATCH_DYNAMIC",
            selection="Over partido",
            line=max(1.5, total_goals + 0.5),
            confidence=score,
            value=value,
            signal_score=signal_score,
            reason=f"Proyección de más goles | {state_reason}",
        )

    return None


# =========================================================
# API PRINCIPAL
# =========================================================
def generate_signal(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    minuto = safe_int(match.get("minuto"), 0)
    if not _is_operable_minute(minuto):
        return None

    prob_real = safe_float(match.get("prob_real"), 0.0)
    prob_implicita = safe_float(match.get("prob_implicita"), 0.0)
    value = _calc_value(prob_real, prob_implicita)
    confidence = _base_confidence(match)

    state_info = _detect_match_state(match)
    state = safe_text(state_info.get("match_state"))
    state_reason = safe_text(state_info.get("match_state_reason"))

    candidates = []

    over_next = _build_over_next_15(match, confidence, value, state, state_reason)
    if over_next:
        candidates.append(over_next)

    under_match = _build_under_match(match, confidence, value, state, state_reason)
    if under_match:
        candidates.append(under_match)

    over_match = _build_over_match(match, confidence, value, state, state_reason)
    if over_match:
        candidates.append(over_match)

    if not candidates:
        return None

    candidates.sort(
        key=lambda s: (
            safe_float(s.get("signal_score"), 0.0),
            safe_float(s.get("confidence"), 0.0),
            safe_float(s.get("value"), 0.0),
        ),
        reverse=True,
    )

    best = candidates[0]
    best["match_state"] = state
    best["match_state_reason"] = state_reason
    best["minute"] = minuto
    best["score"] = f"{safe_int(match.get('marcador_local'))}-{safe_int(match.get('marcador_visitante'))}"
    best["league"] = safe_text(match.get("liga"))
    best["country"] = safe_text(match.get("pais"))
    best["home"] = safe_text(match.get("local"))
    best["away"] = safe_text(match.get("visitante"))
    best["xG"] = safe_float(match.get("xG"), 0.0)
    best["shots"] = safe_int(match.get("shots"), 0)
    best["shots_on_target"] = safe_int(match.get("shots_on_target"), 0)
    best["dangerous_attacks"] = safe_int(match.get("dangerous_attacks"), 0)
    best["momentum"] = safe_text(match.get("momentum"))
    best["odds_data_available"] = False
    best["odds_validation_ok"] = False
    best["source"] = safe_text(match.get("source"))
    best["time_fresh"] = bool(match.get("time_fresh", True))
    best["source_delay_seconds"] = safe_int(match.get("source_delay_seconds"), 0)

    return best

from typing import Dict, Any


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _upper(value: Any) -> str:
    return _safe_text(value).upper()


def _line_close(a: float, b: float, tolerance: float = 0.26) -> bool:
    return abs(a - b) <= tolerance


def _pick_best_market(signal: Dict[str, Any], odds_payload: Dict[str, Any]) -> Dict[str, Any]:
    signal_line = _safe_float(signal.get("line"), 0.0)
    markets = odds_payload.get("markets") or []

    if not markets:
        return {}

    best = None
    best_diff = 9999.0

    for item in markets:
        odds_line = _safe_float(item.get("line"), 0.0)
        diff = abs(odds_line - signal_line)

        if best is None or diff < best_diff:
            best = item
            best_diff = diff

    return best or {}


def validar_mercado_con_odds(signal: Dict[str, Any], odds_payload: Dict[str, Any]) -> Dict[str, Any]:
    market = _upper(signal.get("market"))
    value = _safe_float(signal.get("value"), 0.0)
    confidence = _safe_float(signal.get("confidence"), 0.0)
    signal_line = _safe_float(signal.get("line"), 0.0)
    prob_real = _safe_float(signal.get("prob_real"), _safe_float(signal.get("prob"), 0.0))

    result = {
        "odds_validation_ok": False,
        "odds_data_available": False,
        "market_validation_reason": "Sin validación externa",
        "odds_selected_bookmaker": "",
        "odds_selected_line": 0.0,
        "odds_selected_price": 0.0,
        "odds_implied_probability": 0.0,
        "market_edge_with_odds": 0.0,
        "odds_side": "",
    }

    if market not in ("OVER_MATCH_DYNAMIC", "UNDER_MATCH_DYNAMIC", "OVER_NEXT_15_DYNAMIC"):
        result["market_validation_reason"] = "Mercado no soportado por validador externo"
        return result

    if not odds_payload or not odds_payload.get("odds_data_available", False):
        result["market_validation_reason"] = _safe_text(
            odds_payload.get("error") if isinstance(odds_payload, dict) else "",
            "Sin datos externos"
        )
        return result

    result["odds_data_available"] = True

    best = _pick_best_market(signal, odds_payload)
    if not best:
        result["market_validation_reason"] = "No se encontró línea compatible"
        return result

    odds_line = _safe_float(best.get("line"), 0.0)
    bookmaker = _safe_text(best.get("bookmaker"), "")
    over_price = _safe_float(best.get("over_price"), 0.0)
    under_price = _safe_float(best.get("under_price"), 0.0)

    selected_price = 0.0
    side = ""

    if market in ("OVER_MATCH_DYNAMIC", "OVER_NEXT_15_DYNAMIC"):
        selected_price = over_price
        side = "OVER"
    elif market == "UNDER_MATCH_DYNAMIC":
        selected_price = under_price
        side = "UNDER"

    result["odds_selected_bookmaker"] = bookmaker
    result["odds_selected_line"] = odds_line
    result["odds_selected_price"] = selected_price
    result["odds_side"] = side

    if selected_price <= 0:
        result["market_validation_reason"] = "No hay cuota válida para el lado elegido"
        return result

    implied_probability = round(1.0 / selected_price, 4)
    edge = round((prob_real - implied_probability) * 100, 2)

    result["odds_implied_probability"] = implied_probability
    result["market_edge_with_odds"] = edge

    blocked_reasons = []

    if selected_price < 1.50 or selected_price > 2.10:
        blocked_reasons.append("Cuota fuera del rango operativo")

    if market in ("OVER_MATCH_DYNAMIC", "UNDER_MATCH_DYNAMIC"):
        if signal_line > 0 and odds_line > 0 and not _line_close(signal_line, odds_line):
            blocked_reasons.append("Línea del sistema y línea de mercado no coinciden")

    if prob_real <= 0:
        blocked_reasons.append("Probabilidad real inválida")

    if edge <= 0:
        blocked_reasons.append("No hay edge real contra la cuota")

    if confidence < 68:
        blocked_reasons.append("Confianza insuficiente para validación externa")

    if value < 1.0:
        blocked_reasons.append("Value interno insuficiente")

    if market == "UNDER_MATCH_DYNAMIC":
        xg = _safe_float(signal.get("xG"), 0.0)
        shots_on_target = _safe_float(signal.get("shots_on_target"), 0.0)
        dangerous_attacks = _safe_float(signal.get("dangerous_attacks"), 0.0)
        goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)

        if selected_price < 1.60:
            blocked_reasons.append("Under mal pagado para el riesgo")
        if xg >= 1.35:
            blocked_reasons.append("Under contradicho por xG alto")
        if shots_on_target >= 3:
            blocked_reasons.append("Under contradicho por tiros al arco")
        if dangerous_attacks >= 16:
            blocked_reasons.append("Under contradicho por ataques peligrosos")
        if goal_prob_10 >= 40:
            blocked_reasons.append("Under contradicho por probabilidad de gol")

    if market == "OVER_MATCH_DYNAMIC":
        tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
        if selected_price < 1.55:
            blocked_reasons.append("Over mal pagado")
        if tactical_score < 12:
            blocked_reasons.append("Over sin respaldo táctico suficiente")

    if market == "OVER_NEXT_15_DYNAMIC":
        tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
        goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)

        if selected_price < 1.55:
            blocked_reasons.append("Over próximo 15 mal pagado")
        if tactical_score < 12:
            blocked_reasons.append("Over próximo 15 sin respaldo táctico")
        if goal_prob_10 < 45:
            blocked_reasons.append("Over próximo 15 sin probabilidad de gol suficiente")

    result["odds_validation_ok"] = len(blocked_reasons) == 0
    result["market_validation_reason"] = (
        "OK" if result["odds_validation_ok"] else " | ".join(blocked_reasons)
    )

    return result

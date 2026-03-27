from typing import Dict, Any, List


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
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
    market = _upper(signal.get("market"))
    signal_line = _safe_float(signal.get("line"), 0.0)
    markets = odds_payload.get("markets") or []

    if not markets:
        return {}

    # Para OVER_MATCH_DYNAMIC y UNDER_MATCH_DYNAMIC usamos la línea más cercana
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

    if market not in ("OVER_MATCH_DYNAMIC", "UNDER_MATCH_DYNAMIC", "OVER_NEXT_15_DYNAMIC"):
        return {
            "odds_validation_ok": False,
            "odds_data_available": False,
            "market_validation_reason": "Mercado no soportado por validador externo",
            "odds_selected_bookmaker": "",
            "odds_selected_line": 0.0,
            "odds_selected_price": 0.0,
            "odds_implied_probability": 0.0,
            "market_edge_with_odds": 0.0,
        }

    if not odds_payload.get("odds_data_available", False):
        return {
            "odds_validation_ok": False,
            "odds_data_available": False,
            "market_validation_reason": odds_payload.get("error", "Sin datos externos"),
            "odds_selected_bookmaker": "",
            "odds_selected_line": 0.0,
            "odds_selected_price": 0.0,
            "odds_implied_probability": 0.0,
            "market_edge_with_odds": 0.0,
        }

    best = _pick_best_market(signal, odds_payload)
    if not best:
        return {
            "odds_validation_ok": False,
            "odds_data_available": True,
            "market_validation_reason": "No se encontró línea compatible",
            "odds_selected_bookmaker": "",
            "odds_selected_line": 0.0,
            "odds_selected_price": 0.0,
            "odds_implied_probability": 0.0,
            "market_edge_with_odds": 0.0,
        }

    odds_line = _safe_float(best.get("line"), 0.0)
    bookmaker = _safe_text(best.get("bookmaker"), "")
    over_price = _safe_float(best.get("over_price"), 0.0)
    under_price = _safe_float(best.get("under_price"), 0.0)

    selected_price = 0.0
    if market in ("OVER_MATCH_DYNAMIC", "OVER_NEXT_15_DYNAMIC"):
        selected_price = over_price
    elif market == "UNDER_MATCH_DYNAMIC":
        selected_price = under_price

    if selected_price <= 0:
        return {
            "odds_validation_ok": False,
            "odds_data_available": True,
            "market_validation_reason": "No hay cuota válida para el lado elegido",
            "odds_selected_bookmaker": bookmaker,
            "odds_selected_line": odds_line,
            "odds_selected_price": 0.0,
            "odds_implied_probability": 0.0,
            "market_edge_with_odds": 0.0,
        }

    implied_probability = round(1.0 / selected_price, 4)
    prob_real = _safe_float(signal.get("prob_real"), 0.0)
    edge = round((prob_real - implied_probability) * 100, 2)

    blocked_reasons = []

    if selected_price < 1.50 or selected_price > 2.10:
        blocked_reasons.append("Cuota fuera del rango operativo")

    if market in ("OVER_MATCH_DYNAMIC", "UNDER_MATCH_DYNAMIC"):
        if signal_line > 0 and not _line_close(signal_line, odds_line):
            blocked_reasons.append("Línea del sistema y línea de mercado no coinciden")

    if edge <= 0:
        blocked_reasons.append("No hay edge real contra la cuota")

    if market == "UNDER_MATCH_DYNAMIC" and selected_price < 1.60:
        blocked_reasons.append("Under mal pagado para el riesgo")

    if confidence < 68:
        blocked_reasons.append("Confianza insuficiente para validación externa")

    if value < 1.0:
        blocked_reasons.append("Value interno insuficiente")

    return {
        "odds_validation_ok": len(blocked_reasons) == 0,
        "odds_data_available": True,
        "market_validation_reason": "OK" if len(blocked_reasons) == 0 else " | ".join(blocked_reasons),
        "odds_selected_bookmaker": bookmaker,
        "odds_selected_line": odds_line,
        "odds_selected_price": selected_price,
        "odds_implied_probability": implied_probability,
        "market_edge_with_odds": edge,
    }

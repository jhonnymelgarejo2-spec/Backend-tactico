# market_validation_engine.py

from typing import Dict, Any, List
import config


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


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _upper(value: Any) -> str:
    return _safe_text(value).upper()


def _line_close(a: float, b: float, tolerance: float = 0.26) -> bool:
    return abs(a - b) <= tolerance


# =========================================================
# SELECCION DEL MEJOR MERCADO
# =========================================================
def _pick_best_market(signal: Dict[str, Any], odds_payload: Dict[str, Any]) -> Dict[str, Any]:
    signal_line = _safe_float(signal.get("line"), 0.0)
    markets = odds_payload.get("markets") or []

    if not markets:
        return {}

    market_type = _upper(signal.get("market"))
    candidates: List[Dict[str, Any]] = []

    for item in markets:
        odds_line = _safe_float(item.get("line"), 0.0)
        over_price = _safe_float(item.get("over_price"), 0.0)
        under_price = _safe_float(item.get("under_price"), 0.0)

        if market_type in ("OVER_MATCH_DYNAMIC", "OVER_NEXT_15_DYNAMIC"):
            selected_price = over_price
        else:
            selected_price = under_price

        if selected_price <= 0:
            continue

        diff = abs(odds_line - signal_line)
        in_range = config.ODD_MIN_GLOBAL <= selected_price <= config.ODD_MAX_GLOBAL

        candidates.append({
            "raw": item,
            "line_diff": diff,
            "selected_price": selected_price,
            "in_range": in_range,
        })

    if not candidates:
        return {}

    # Preferimos:
    # 1) línea cercana
    # 2) cuota dentro de rango
    # 3) menor distancia total
    candidates.sort(
        key=lambda x: (
            0 if x["in_range"] else 1,
            x["line_diff"],
            abs(x["selected_price"] - config.DEFAULT_ODD)
        )
    )

    return candidates[0]["raw"]


# =========================================================
# VALIDACIONES COMUNES
# =========================================================
def _validate_common_rules(
    signal: Dict[str, Any],
    market: str,
    odds_line: float,
    selected_price: float,
    implied_probability: float,
    edge: float,
) -> List[str]:
    blocked_reasons: List[str] = []

    signal_line = _safe_float(signal.get("line"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    confidence = _safe_float(signal.get("confidence"), 0.0)
    prob_real = _safe_float(signal.get("prob_real"), _safe_float(signal.get("prob"), 0.0))

    if selected_price < config.ODD_MIN_GLOBAL or selected_price > config.ODD_MAX_GLOBAL:
        blocked_reasons.append("Cuota fuera del rango operativo")

    if market in ("OVER_MATCH_DYNAMIC", "UNDER_MATCH_DYNAMIC"):
        if signal_line > 0 and odds_line > 0 and not _line_close(signal_line, odds_line):
            blocked_reasons.append("Línea del sistema y línea de mercado no coinciden")

    if prob_real <= 0:
        blocked_reasons.append("Probabilidad real inválida")

    if implied_probability <= 0:
        blocked_reasons.append("Probabilidad implícita inválida")

    if edge <= 0:
        blocked_reasons.append("No hay edge real contra la cuota")

    if confidence < config.MIN_CONFIDENCE_GLOBAL:
        blocked_reasons.append("Confianza insuficiente para validación externa")

    if value < config.MIN_VALUE_GLOBAL:
        blocked_reasons.append("Value interno insuficiente")

    return blocked_reasons


# =========================================================
# VALIDACIONES POR MERCADO
# =========================================================
def _validate_under_rules(signal: Dict[str, Any], selected_price: float) -> List[str]:
    blocked_reasons: List[str] = []

    xg = _safe_float(signal.get("xG"), 0.0)
    shots_on_target = _safe_float(signal.get("shots_on_target"), 0.0)
    dangerous_attacks = _safe_float(signal.get("dangerous_attacks"), 0.0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)
    minute = _safe_float(signal.get("minute"), 0.0)

    if selected_price < config.UNDER_MATCH_MIN_ODD:
        blocked_reasons.append("Under mal pagado para el riesgo")

    if minute < config.UNDER_MATCH_MIN_MINUTE:
        blocked_reasons.append("Under demasiado temprano")

    if xg >= config.UNDER_MATCH_MAX_XG:
        blocked_reasons.append("Under contradicho por xG alto")

    if shots_on_target > config.UNDER_MATCH_MAX_SHOTS_ON_TARGET:
        blocked_reasons.append("Under contradicho por tiros al arco")

    if dangerous_attacks >= config.UNDER_MATCH_MAX_DANGEROUS_ATTACKS:
        blocked_reasons.append("Under contradicho por ataques peligrosos")

    if goal_prob_10 >= config.UNDER_MATCH_MAX_GOAL_PROB_10:
        blocked_reasons.append("Under contradicho por probabilidad de gol")

    return blocked_reasons


def _validate_over_match_rules(signal: Dict[str, Any], selected_price: float) -> List[str]:
    blocked_reasons: List[str] = []

    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    minute = _safe_float(signal.get("minute"), 0.0)

    if selected_price < config.OVER_MATCH_MIN_ODD:
        blocked_reasons.append("Over mal pagado")

    if tactical_score < config.OVER_MATCH_MIN_TACTICAL_SCORE:
        blocked_reasons.append("Over sin respaldo táctico suficiente")

    if minute > config.OVER_MATCH_MAX_MINUTE:
        blocked_reasons.append("Over match demasiado tardío")

    return blocked_reasons


def _validate_over_next15_rules(signal: Dict[str, Any], selected_price: float) -> List[str]:
    blocked_reasons: List[str] = []

    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0.0)
    minute = _safe_float(signal.get("minute"), 0.0)

    if selected_price < config.OVER_NEXT_15_MIN_ODD:
        blocked_reasons.append("Over próximo 15 mal pagado")

    if tactical_score < config.OVER_NEXT_15_MIN_TACTICAL_SCORE:
        blocked_reasons.append("Over próximo 15 sin respaldo táctico")

    if goal_prob_10 < config.OVER_NEXT_15_MIN_GOAL_PROB_10:
        blocked_reasons.append("Over próximo 15 sin probabilidad de gol suficiente")

    if minute < config.OVER_NEXT_15_MIN_MINUTE or minute > config.OVER_NEXT_15_MAX_MINUTE:
        blocked_reasons.append("Over próximo 15 fuera de ventana operable")

    return blocked_reasons


# =========================================================
# VALIDADOR PRINCIPAL
# =========================================================
def validar_mercado_con_odds(signal: Dict[str, Any], odds_payload: Dict[str, Any]) -> Dict[str, Any]:
    market = _upper(signal.get("market"))
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
        "market_validation_codes": [],
    }

    if market not in config.MARKETS_ALLOWED:
        result["market_validation_reason"] = "Mercado no soportado por validador externo"
        result["market_validation_codes"] = ["MARKET_NOT_SUPPORTED"]
        return result

    if not isinstance(odds_payload, dict) or not odds_payload.get("odds_data_available", False):
        result["market_validation_reason"] = _safe_text(
            odds_payload.get("error") if isinstance(odds_payload, dict) else "",
            "Sin datos externos"
        )
        result["market_validation_codes"] = ["NO_ODDS_DATA"]
        return result

    result["odds_data_available"] = True

    best = _pick_best_market(signal, odds_payload)
    if not best:
        result["market_validation_reason"] = "No se encontró línea compatible"
        result["market_validation_codes"] = ["NO_COMPATIBLE_LINE"]
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
        result["market_validation_codes"] = ["INVALID_SELECTED_PRICE"]
        return result

    implied_probability = round(1.0 / selected_price, 4)
    edge = round((prob_real - implied_probability) * 100, 2)

    result["odds_implied_probability"] = implied_probability
    result["market_edge_with_odds"] = edge

    blocked_reasons: List[str] = []
    blocked_codes: List[str] = []

    # Reglas comunes
    common_blocks = _validate_common_rules(
        signal=signal,
        market=market,
        odds_line=odds_line,
        selected_price=selected_price,
        implied_probability=implied_probability,
        edge=edge,
    )
    blocked_reasons.extend(common_blocks)

    # Mapear códigos básicos
    code_map = {
        "Cuota fuera del rango operativo": "ODDS_OUT_OF_RANGE",
        "Línea del sistema y línea de mercado no coinciden": "LINE_MISMATCH",
        "Probabilidad real inválida": "INVALID_REAL_PROBABILITY",
        "Probabilidad implícita inválida": "INVALID_IMPLIED_PROBABILITY",
        "No hay edge real contra la cuota": "NO_REAL_EDGE",
        "Confianza insuficiente para validación externa": "LOW_CONFIDENCE",
        "Value interno insuficiente": "LOW_INTERNAL_VALUE",
    }
    blocked_codes.extend([code_map[r] for r in common_blocks if r in code_map])

    # Reglas por mercado
    if market == "UNDER_MATCH_DYNAMIC":
        specific = _validate_under_rules(signal, selected_price)
        blocked_reasons.extend(specific)
        specific_map = {
            "Under mal pagado para el riesgo": "UNDER_BAD_PRICE",
            "Under demasiado temprano": "UNDER_TOO_EARLY",
            "Under contradicho por xG alto": "UNDER_XG_TOO_HIGH",
            "Under contradicho por tiros al arco": "UNDER_SOT_TOO_HIGH",
            "Under contradicho por ataques peligrosos": "UNDER_DANGEROUS_TOO_HIGH",
            "Under contradicho por probabilidad de gol": "UNDER_GOAL_PROB_TOO_HIGH",
        }
        blocked_codes.extend([specific_map[r] for r in specific if r in specific_map])

    elif market == "OVER_MATCH_DYNAMIC":
        specific = _validate_over_match_rules(signal, selected_price)
        blocked_reasons.extend(specific)
        specific_map = {
            "Over mal pagado": "OVER_BAD_PRICE",
            "Over sin respaldo táctico suficiente": "OVER_LOW_TACTICAL_SUPPORT",
            "Over match demasiado tardío": "OVER_TOO_LATE",
        }
        blocked_codes.extend([specific_map[r] for r in specific if r in specific_map])

    elif market == "OVER_NEXT_15_DYNAMIC":
        specific = _validate_over_next15_rules(signal, selected_price)
        blocked_reasons.extend(specific)
        specific_map = {
            "Over próximo 15 mal pagado": "NEXT15_BAD_PRICE",
            "Over próximo 15 sin respaldo táctico": "NEXT15_LOW_TACTICAL_SUPPORT",
            "Over próximo 15 sin probabilidad de gol suficiente": "NEXT15_LOW_GOAL_PROB",
            "Over próximo 15 fuera de ventana operable": "NEXT15_OUTSIDE_WINDOW",
        }
        blocked_codes.extend([specific_map[r] for r in specific if r in specific_map])

    # Resultado final
    # quitar duplicados conservando orden
    seen = set()
    dedup_reasons = []
    for r in blocked_reasons:
        if r not in seen:
            seen.add(r)
            dedup_reasons.append(r)

    seen_codes = set()
    dedup_codes = []
    for c in blocked_codes:
        if c not in seen_codes:
            seen_codes.add(c)
            dedup_codes.append(c)

    result["odds_validation_ok"] = len(dedup_reasons) == 0
    result["market_validation_codes"] = dedup_codes
    result["market_validation_reason"] = (
        "OK" if result["odds_validation_ok"] else " | ".join(dedup_reasons)
    )

    return result

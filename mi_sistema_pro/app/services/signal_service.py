from typing import Dict, Any, Optional, List

from app.engines.signal_engine import generate_signal
from app.odds.odds_service import obtener_odds_partido
from app.utils.helpers import safe_float, safe_text


def _pick_best_market_for_signal(signal: Dict[str, Any], odds_payload: Dict[str, Any]) -> Dict[str, Any]:
    markets = odds_payload.get("markets") or []
    market_name = safe_text(signal.get("market")).upper()

    if not markets:
        return {}

    candidates: List[Dict[str, Any]] = []

    for item in markets:
        line = safe_float(item.get("line"), 0.0)
        over_price = safe_float(item.get("over_price"), 0.0)
        under_price = safe_float(item.get("under_price"), 0.0)

        selected_price = 0.0
        side = ""

        if market_name in ("OVER_NEXT_15_DYNAMIC", "OVER_MATCH_DYNAMIC"):
            selected_price = over_price
            side = "OVER"
        elif market_name == "UNDER_MATCH_DYNAMIC":
            selected_price = under_price
            side = "UNDER"

        if selected_price <= 0:
            continue

        candidates.append({
            "bookmaker": safe_text(item.get("bookmaker")),
            "line": line,
            "price": selected_price,
            "side": side,
            "raw": item,
        })

    if not candidates:
        return {}

    candidates.sort(key=lambda x: x["price"])
    return candidates[0]


def _apply_odds_to_signal(signal: Dict[str, Any], odds_payload: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(signal)

    enriched["odds_source"] = safe_text(odds_payload.get("odds_source"), "none")
    enriched["odds_data_available"] = bool(odds_payload.get("odds_data_available", False))
    enriched["odds_error"] = safe_text(odds_payload.get("error"), "")
    enriched["odds_selected_bookmaker"] = ""
    enriched["odds_selected_line"] = 0.0
    enriched["odds_selected_price"] = 0.0
    enriched["odds_side"] = ""
    enriched["odds_validation_ok"] = False

    if not enriched["odds_data_available"]:
        return enriched

    best = _pick_best_market_for_signal(enriched, odds_payload)
    if not best:
        return enriched

    selected_price = safe_float(best.get("price"), 0.0)
    if selected_price <= 0:
        return enriched

    implied_probability = round(1.0 / selected_price, 4)
    prob_real = safe_float(enriched.get("prob_real"), 0.0)
    value = round((prob_real - implied_probability) * 100, 2)

    enriched["odd"] = selected_price
    enriched["cuota"] = selected_price
    enriched["prob_implicita"] = implied_probability
    enriched["value"] = value
    enriched["valor"] = value

    enriched["odds_selected_bookmaker"] = safe_text(best.get("bookmaker"))
    enriched["odds_selected_line"] = safe_float(best.get("line"), 0.0)
    enriched["odds_selected_price"] = selected_price
    enriched["odds_side"] = safe_text(best.get("side"))
    enriched["odds_validation_ok"] = True

    confidence = safe_float(enriched.get("confidence"), 0.0)
    enriched["signal_score"] = round(confidence * 1.1 + value * 2.0, 2)

    if enriched["signal_score"] >= 160:
        enriched["signal_rank"] = "ELITE"
    elif enriched["signal_score"] >= 120:
        enriched["signal_rank"] = "TOP"
    elif enriched["signal_score"] >= 90:
        enriched["signal_rank"] = "ALTA"
    else:
        enriched["signal_rank"] = "NORMAL"

    enriched["publish_ready"] = confidence >= 68 and value > 1 and enriched["odds_validation_ok"]
    enriched["recomendacion_final"] = "APOSTAR" if enriched["publish_ready"] else "OBSERVAR"

    return enriched


def process_match_signal(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    signal = generate_signal(match)
    if not signal:
        return None

    try:
        odds_payload = obtener_odds_partido(
            local=safe_text(match.get("local")),
            visitante=safe_text(match.get("visitante")),
            league=safe_text(match.get("liga")),
            country=safe_text(match.get("pais")),
        )
    except Exception as e:
        odds_payload = {
            "ok": False,
            "error": f"ODDS_SERVICE_CRASH: {e}",
            "odds_source": "none",
            "odds_data_available": False,
            "markets": [],
        }

    return _apply_odds_to_signal(signal, odds_payload)

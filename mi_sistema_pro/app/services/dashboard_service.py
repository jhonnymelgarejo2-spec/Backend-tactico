from typing import Dict, Any, List

from app.utils.helpers import safe_float, safe_int, safe_text


def _avg(values: List[float]) -> float:
    clean = [safe_float(v, 0.0) for v in values if safe_float(v, 0.0) != 0.0]
    if not clean:
        return 0.0
    return round(sum(clean) / len(clean), 2)


def build_dashboard_payload(scan_result: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(scan_result, dict):
        return {
            "ok": False,
            "error": "SCAN_RESULT_INVALID",
            "signals": [],
            "observed_signals": [],
            "hot_matches": [],
            "stats": {
                "total_matches": 0,
                "total_signals": 0,
                "total_hot_matches": 0,
                "observed_signals": 0,
                "strict_signals": 0,
                "flex_signals": 0,
                "avg_confidence": 0.0,
                "avg_value": 0.0,
                "avg_risk": 0.0,
                "elite_signals": 0,
                "top_signals": 0,
                "validated_odds_signals": 0,
                "publish_ready_signals": 0,
                "errors": 1,
            },
        }

    signals = scan_result.get("signals", [])
    observed_signals = scan_result.get("observed_signals", [])
    hot_matches = scan_result.get("hot_matches", [])
    base_stats = scan_result.get("stats", {}) or {}
    errors = scan_result.get("errors", []) or []

    if not isinstance(signals, list):
        signals = []
    if not isinstance(observed_signals, list):
        observed_signals = []
    if not isinstance(hot_matches, list):
        hot_matches = []

    confidences = [safe_float(s.get("confidence"), 0.0) for s in signals]
    values = [safe_float(s.get("value", s.get("valor", 0.0)), 0.0) for s in signals]
    risks = [safe_float(s.get("risk_score"), 0.0) for s in signals]

    elite_signals = 0
    top_signals = 0
    validated_odds_signals = 0
    publish_ready_signals = 0

    strict_signals_count = 0
    flex_signals_count = 0

    for signal in observed_signals:
        publication_mode = safe_text(signal.get("publication_mode")).upper()

        if publication_mode == "STRICT":
            strict_signals_count += 1
        elif publication_mode == "INTERNAL_FLEX":
            flex_signals_count += 1

    for signal in signals:
        rank = safe_text(signal.get("signal_rank")).upper()

        if rank == "ELITE":
            elite_signals += 1

        if rank in {"ELITE", "TOP"}:
            top_signals += 1

        if bool(signal.get("odds_validation_ok", False)):
            validated_odds_signals += 1

        if bool(signal.get("publish_ready", False)):
            publish_ready_signals += 1

    stats = {
        "total_matches": safe_int(base_stats.get("total_matches"), 0),
        "total_signals": safe_int(base_stats.get("total_signals"), len(signals)),
        "total_hot_matches": safe_int(base_stats.get("total_hot_matches"), len(hot_matches)),
        "observed_signals": safe_int(base_stats.get("observed_signals"), len(observed_signals)),
        "strict_signals": safe_int(base_stats.get("strict_signals"), strict_signals_count),
        "flex_signals": safe_int(base_stats.get("flex_signals"), flex_signals_count),
        "avg_confidence": _avg(confidences),
        "avg_value": _avg(values),
        "avg_risk": _avg(risks),
        "elite_signals": elite_signals,
        "top_signals": top_signals,
        "validated_odds_signals": validated_odds_signals,
        "publish_ready_signals": publish_ready_signals,
        "errors": safe_int(base_stats.get("errors"), len(errors)),
    }

    return {
        "ok": bool(scan_result.get("ok", True)),
        "error": safe_text(scan_result.get("error", "")),
        "system": safe_text(scan_result.get("system")),
        "version": safe_text(scan_result.get("version")),
        "scan_started_at": safe_int(scan_result.get("scan_started_at"), 0),
        "scan_finished_at": safe_int(scan_result.get("scan_finished_at"), 0),
        "signals": signals,
        "observed_signals": observed_signals,
        "hot_matches": hot_matches,
        "stats": stats,
        "errors": errors,
        }

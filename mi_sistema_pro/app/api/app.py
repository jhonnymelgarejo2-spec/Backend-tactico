from flask import Flask, jsonify

from app.config.config import settings
from app.services.dashboard_service import build_dashboard_payload
from app.services.scan_cache_service import (
    clear_scan_cache,
    get_cache_meta,
    get_scan_result,
)

app = Flask(__name__)


def _empty_stats(errors: int = 1) -> dict:
    return {
        "total_matches": 0,
        "total_signals": 0,
        "total_hot_matches": 0,
        "observed_signals": 0,
        "strict_signals": 0,
        "flex_signals": 0,
        "errors": errors,
    }


def _safe_scan_result(force_refresh: bool = False) -> dict:
    try:
        result = get_scan_result(force_refresh=force_refresh)
        if not isinstance(result, dict):
            return {
                "ok": False,
                "error": "SCAN_RESULT_INVALID",
                "signals": [],
                "observed_signals": [],
                "hot_matches": [],
                "stats": _empty_stats(),
            }
        return result
    except Exception as e:
        return {
            "ok": False,
            "error": f"SCAN_CRASH: {e}",
            "signals": [],
            "observed_signals": [],
            "hot_matches": [],
            "stats": _empty_stats(),
        }


def _safe_list(value) -> list:
    return value if isinstance(value, list) else []


@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "ok": True,
        "system": settings.SYSTEM_NAME,
        "version": settings.SYSTEM_VERSION,
        "message": "API activa",
        "endpoints": [
            "/health",
            "/scan",
            "/scan/refresh",
            "/scan/cache-meta",
            "/scan/cache-clear",
            "/signals",
            "/observed-signals",
            "/strict-signals",
            "/flex-signals",
            "/hot-matches",
            "/dashboard-data",
        ],
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok": True,
        "system": settings.SYSTEM_NAME,
        "version": settings.SYSTEM_VERSION,
        "status": "healthy",
    }), 200


@app.route("/scan", methods=["GET"])
def scan():
    result = _safe_scan_result()
    return jsonify(result), 200


@app.route("/scan/refresh", methods=["GET"])
def scan_refresh():
    result = _safe_scan_result(force_refresh=True)
    return jsonify(result), 200


@app.route("/scan/cache-meta", methods=["GET"])
def scan_cache_meta():
    return jsonify({
        "ok": True,
        "cache": get_cache_meta(),
    }), 200


@app.route("/scan/cache-clear", methods=["GET"])
def scan_cache_clear():
    payload = clear_scan_cache()
    return jsonify(payload), 200


@app.route("/signals", methods=["GET"])
def signals():
    result = _safe_scan_result()
    signals_list = _safe_list(result.get("signals", []))

    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "signals": signals_list,
        "total": len(signals_list),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/observed-signals", methods=["GET"])
def observed_signals():
    result = _safe_scan_result()
    observed = _safe_list(result.get("observed_signals", []))

    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "observed_signals": observed,
        "total": len(observed),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/strict-signals", methods=["GET"])
def strict_signals():
    result = _safe_scan_result()
    observed = _safe_list(result.get("observed_signals", []))

    strict = [
        signal for signal in observed
        if str(signal.get("publication_mode", "")).upper() == "STRICT"
    ]

    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "strict_signals": strict,
        "total": len(strict),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/flex-signals", methods=["GET"])
def flex_signals():
    result = _safe_scan_result()
    observed = _safe_list(result.get("observed_signals", []))

    flex = [
        signal for signal in observed
        if str(signal.get("publication_mode", "")).upper() == "INTERNAL_FLEX"
    ]

    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "flex_signals": flex,
        "total": len(flex),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/hot-matches", methods=["GET"])
def hot_matches():
    result = _safe_scan_result()
    hot_matches_list = _safe_list(result.get("hot_matches", []))

    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "hot_matches": hot_matches_list,
        "total": len(hot_matches_list),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():
    result = _safe_scan_result()
    payload = build_dashboard_payload(result)
    return jsonify(payload), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT, debug=settings.DEBUG)

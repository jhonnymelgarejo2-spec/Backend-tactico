from flask import Flask, jsonify

from app.config.config import settings
from app.services.dashboard_service import build_dashboard_payload
from app.services.scan_service import run_scan_cycle

app = Flask(__name__)


def _empty_stats(errors: int = 1) -> dict:
    return {
        "total_matches": 0,
        "total_signals": 0,
        "total_hot_matches": 0,
        "observed_signals": 0,
        "errors": errors,
    }


def _safe_scan_result() -> dict:
    try:
        result = run_scan_cycle()
        if not isinstance(result, dict):
            return {
                "ok": False,
                "error": "SCAN_RESULT_INVALID",
                "signals": [],
                "hot_matches": [],
                "observed_signals": [],
                "stats": _empty_stats(),
            }
        return result
    except Exception as e:
        return {
            "ok": False,
            "error": f"SCAN_CRASH: {e}",
            "signals": [],
            "hot_matches": [],
            "observed_signals": [],
            "stats": _empty_stats(),
        }


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
            "/signals",
            "/observed-signals",
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


@app.route("/signals", methods=["GET"])
def signals():
    result = _safe_scan_result()
    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "signals": result.get("signals", []),
        "total": len(result.get("signals", [])),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/observed-signals", methods=["GET"])
def observed_signals():
    result = _safe_scan_result()
    observed = result.get("observed_signals", [])
    if not isinstance(observed, list):
        observed = []

    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "observed_signals": observed,
        "total": len(observed),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/hot-matches", methods=["GET"])
def hot_matches():
    result = _safe_scan_result()
    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "hot_matches": result.get("hot_matches", []),
        "total": len(result.get("hot_matches", [])),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.route("/dashboard-data", methods=["GET"])
def dashboard_data():
    result = _safe_scan_result()
    payload = build_dashboard_payload(result)
    return jsonify(payload), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT, debug=settings.DEBUG)

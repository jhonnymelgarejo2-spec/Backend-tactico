from flask import Flask, jsonify

from app.config.config import settings
from app.services.scan_service import run_scan_cycle

app = Flask(__name__)


def _empty_stats(errors: int = 1) -> dict:
    return {
        "total_matches": 0,
        "total_signals": 0,
        "total_hot_matches": 0,
        "errors": errors,
    }


def _safe_scan_result():
    try:
        result = run_scan_cycle()
        if not isinstance(result, dict):
            return {
                "ok": False,
                "error": "SCAN_RESULT_INVALID",
                "signals": [],
                "hot_matches": [],
                "stats": _empty_stats(),
            }
        return result
    except Exception as e:
        return {
            "ok": False,
            "error": f"SCAN_CRASH: {e}",
            "signals": [],
            "hot_matches": [],
            "stats": _empty_stats(),
        }


@app.get("/")
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
            "/hot-matches",
            "/dashboard-data",
        ],
    })


@app.get("/health")
def health():
    return jsonify({
        "ok": True,
        "system": settings.SYSTEM_NAME,
        "version": settings.SYSTEM_VERSION,
        "status": "healthy",
    })


@app.get("/scan")
def scan():
    result = _safe_scan_result()
    return jsonify(result), 200


@app.get("/signals")
def signals():
    result = _safe_scan_result()
    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "signals": result.get("signals", []),
        "total": len(result.get("signals", [])),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.get("/hot-matches")
def hot_matches():
    result = _safe_scan_result()
    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "hot_matches": result.get("hot_matches", []),
        "total": len(result.get("hot_matches", [])),
        "stats": result.get("stats", _empty_stats(0)),
    }), 200


@app.get("/dashboard-data")
def dashboard_data():
    result = _safe_scan_result()
    return jsonify({
        "ok": result.get("ok", False),
        "error": result.get("error", ""),
        "signals": result.get("signals", []),
        "hot_matches": result.get("hot_matches", []),
        "stats": result.get("stats", _empty_stats(0)),
        "system": settings.SYSTEM_NAME,
        "version": settings.SYSTEM_VERSION,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT, debug=settings.DEBUG)

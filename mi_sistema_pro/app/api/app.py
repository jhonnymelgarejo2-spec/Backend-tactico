from flask import Flask, jsonify

from app.config.config import settings
from app.services.scan_service import run_scan_cycle

app = Flask(__name__)


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
    try:
        result = run_scan_cycle()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"SCAN_CRASH: {e}",
            "signals": [],
            "hot_matches": [],
            "stats": {
                "total_matches": 0,
                "total_signals": 0,
                "total_hot_matches": 0,
                "errors": 1,
            },
        }), 200


@app.get("/signals")
def signals():
    try:
        result = run_scan_cycle()
        return jsonify({
            "ok": True,
            "signals": result.get("signals", []),
            "total": len(result.get("signals", [])),
        }), 200
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"SIGNALS_CRASH: {e}",
            "signals": [],
            "total": 0,
        }), 200


@app.get("/hot-matches")
def hot_matches():
    try:
        result = run_scan_cycle()
        return jsonify({
            "ok": True,
            "hot_matches": result.get("hot_matches", []),
            "total": len(result.get("hot_matches", [])),
        }), 200
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"HOT_MATCHES_CRASH: {e}",
            "hot_matches": [],
            "total": 0,
        }), 200


@app.get("/dashboard-data")
def dashboard_data():
    try:
        result = run_scan_cycle()
        return jsonify({
            "ok": True,
            "signals": result.get("signals", []),
            "hot_matches": result.get("hot_matches", []),
            "stats": result.get("stats", {}),
        }), 200
    except Exception as e:
        return jsonify({
            "ok": False,
            "error": f"DASHBOARD_CRASH: {e}",
            "signals": [],
            "hot_matches": [],
            "stats": {
                "total_matches": 0,
                "total_signals": 0,
                "total_hot_matches": 0,
                "errors": 1,
            },
        }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.PORT, debug=settings.DEBUG)

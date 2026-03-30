# app/api/app.py

from flask import Flask, jsonify

from app.config.config import config
from app.services.scan_service import (
    run_scan_cycle,
    get_dashboard_data,
    get_signals,
    get_hot_matches,
)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "system": config.SYSTEM_NAME,
            "version": config.SYSTEM_VERSION,
            "mode": config.SYSTEM_MODE,
        })

    @app.get("/scan")
    def scan():
        try:
            result = run_scan_cycle()
            return jsonify(result), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Scan falló: {e}",
                "signals": [],
                "hot_matches": [],
                "total_matches": 0,
                "total_signals": 0,
                "total_hot_matches": 0,
            }), 200

    @app.get("/dashboard-data")
    def dashboard_data():
        try:
            return jsonify(get_dashboard_data()), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"dashboard-data falló: {e}",
                "signals": [],
                "stats": {"win_rate": 0.0},
                "total_matches": 0,
                "total_hot_matches": 0,
                "total_signals": 0,
            }), 200

    @app.get("/signals")
    def signals():
        try:
            return jsonify(get_signals()), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"signals falló: {e}",
                "signals": [],
                "total_signals": 0,
            }), 200

    @app.get("/hot-matches")
    def hot_matches():
        try:
            return jsonify(get_hot_matches()), 200
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"hot-matches falló: {e}",
                "hot_matches": [],
                "total_hot_matches": 0,
            }), 200

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
      )

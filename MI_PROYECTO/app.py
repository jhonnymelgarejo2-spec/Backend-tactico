import os
import sys

from flask import Flask, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, "MI_PROYECTO")

if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from core.decision_pipeline import procesar_partido

app = Flask(__name__)


@app.route("/")
def home():
    return "JHONNY ELITE BACKEND ACTIVO"


@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "service": "jhonny_elite_backend"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "ok"
    })


@app.route("/test-pipeline")
def test_pipeline():
    partido_fake = {
        "id": 1,
        "local": "Equipo A",
        "visitante": "Equipo B",
        "liga": "Demo League",
        "pais": "World",
        "minuto": 25,
        "marcador_local": 1,
        "marcador_visitante": 0,
        "xG": 1.4,
        "momentum": "ALTO",
        "goal_pressure": {"pressure_score": 7},
        "goal_predictor": {
            "predictor_score": 8,
            "goal_next_5_prob": 0.34,
            "goal_next_10_prob": 0.41
        },
        "chaos": {"chaos_score": 3}
    }

    try:
        resultado = procesar_partido(partido_fake)
        return jsonify(resultado or {"msg": "No signal"})
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

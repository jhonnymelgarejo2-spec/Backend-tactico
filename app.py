from flask import Flask, jsonify
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

# EJEMPLO DE ENDPOINT (puedes ampliarlo luego)
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
        "momentum": "HIGH"
    }

    resultado = procesar_partido(partido_fake)

    return jsonify(resultado or {"msg": "No signal"})

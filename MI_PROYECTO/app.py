from flask import Flask, jsonify
from core.decision_pipeline import procesar_partido

app = Flask(__name__)

# 🔹 Ruta base
@app.route("/")
def home():
    return "JHONNY ELITE BACKEND ACTIVO"

# 🔹 Health check (importante para Render)
@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "service": "jhonny_elite_backend"
    })

# 🔹 Test del pipeline
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

    try:
        resultado = procesar_partido(partido_fake)
        return jsonify(resultado or {"msg": "No signal"})
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": "pipeline_error"
        }), 500

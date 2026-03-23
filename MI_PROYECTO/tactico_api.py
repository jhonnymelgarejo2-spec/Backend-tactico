from flask import Flask, jsonify, request
from typing import Dict, Any, List
import time

# =========================================================
# IMPORT PIPELINE
# =========================================================
try:
    from core.decision_pipeline import procesar_partido
    print("[IMPORT] decision_pipeline OK")
except Exception as e:
    print(f"[IMPORT ERROR] decision_pipeline -> {e}")
    procesar_partido = None


# =========================================================
# APP FLASK (BACKEND PRINCIPAL)
# =========================================================
app = Flask(__name__)

# =========================================================
# ESTADO GLOBAL (CACHE SIMPLE)
# =========================================================
STATE = {
    "last_scan": 0,
    "signals": [],
    "hot_matches": [],
    "history": [],
    "stats": {
        "ganadas": 0,
        "perdidas": 0,
        "win_rate": 0,
        "roi_percent": 0,
        "signals_elite": 0,
        "signals_top": 0,
        "value_promedio": 0,
        "riesgo_medio": 0,
    },
    "leagues": []
}


# =========================================================
# FUNCIONES CORE
# =========================================================
def procesar_partidos(partidos: List[Dict[str, Any]]) -> List[Dict]:
    señales = []

    if not procesar_partido:
        return señales

    for p in partidos:
        try:
            s = procesar_partido(p)
            if s:
                señales.append(s)
        except Exception as e:
            print(f"[ERROR PARTIDO] {e}")

    return señales


def detectar_hot_matches(partidos: List[Dict]) -> List[Dict]:
    hot = []

    for p in partidos:
        xg = float(p.get("xG", 0))
        shots = int(p.get("shots", 0))

        if xg >= 1.2 or shots >= 8:
            hot.append(p)

    return hot


# =========================================================
# ENDPOINTS BASE
# =========================================================
@app.route("/")
def home():
    return "JHONNY ELITE V16 BACKEND ACTIVO"


@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "service": "jhonny_elite_v16"
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


# =========================================================
# SCAN (SIMULADO POR AHORA)
# =========================================================
@app.route("/scan")
def scan():
    # 🔥 Aquí luego irá el scraper real
    partidos_fake = [
        {
            "id": 1,
            "local": "Equipo A",
            "visitante": "Equipo B",
            "liga": "Demo League",
            "pais": "World",
            "minuto": 25,
            "marcador_local": 1,
            "marcador_visitante": 0,
            "xG": 1.4,
            "shots": 9,
            "shots_on_target": 4,
            "dangerous_attacks": 22,
            "momentum": "ALTO",
            "goal_pressure": {"pressure_score": 7},
            "goal_predictor": {
                "predictor_score": 8,
                "goal_next_5_prob": 0.34,
                "goal_next_10_prob": 0.41
            },
            "chaos": {"chaos_score": 3}
        }
    ]

    señales = procesar_partidos(partidos_fake)
    hot = detectar_hot_matches(partidos_fake)

    STATE["signals"] = señales
    STATE["hot_matches"] = hot
    STATE["last_scan"] = int(time.time())

    return jsonify({
        "ultimo_scan": STATE["last_scan"],
        "total_partidos": len(partidos_fake)
    })


# =========================================================
# SEÑALES
# =========================================================
@app.route("/signals")
def signals():
    return jsonify({
        "signals": STATE["signals"]
    })


# =========================================================
# HOT MATCHES
# =========================================================
@app.route("/hot-matches")
def hot_matches():
    return jsonify({
        "hot_matches": STATE["hot_matches"]
    })


# =========================================================
# LEARNING STATS
# =========================================================
@app.route("/learning-stats")
def learning_stats():
    return jsonify(STATE["stats"])


# =========================================================
# HISTORIAL
# =========================================================
@app.route("/history")
def history():
    return jsonify(STATE["history"])


# =========================================================
# LIGAS
# =========================================================
@app.route("/api/leagues")
def leagues():
    return jsonify(STATE["leagues"])


# =========================================================
# TEST PIPELINE
# =========================================================
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
        "shots": 9,
        "shots_on_target": 4,
        "dangerous_attacks": 22,
        "momentum": "ALTO",
        "goal_pressure": {"pressure_score": 7},
        "goal_predictor": {
            "predictor_score": 8,
            "goal_next_5_prob": 0.34,
            "goal_next_10_prob": 0.41
        },
        "chaos": {"chaos_score": 3}
    }

    if not procesar_partido:
        return jsonify({"error": "pipeline no disponible"})

    try:
        resultado = procesar_partido(partido_fake)
        return jsonify(resultado or {"msg": "No signal"})
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500

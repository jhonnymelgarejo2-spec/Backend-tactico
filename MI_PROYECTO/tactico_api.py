import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# =========================================================
# IMPORTS
# =========================================================
try:
    from live_fetcher import obtener_partidos_en_vivo
except:
    obtener_partidos_en_vivo = None

# 🔥 PIPELINE CENTRAL
def get_procesar_partido():
    try:
        from core.decision_pipeline import procesar_partido
        return procesar_partido
    except:
        return None

# 🔥 HISTORIAL REAL
try:
    from core.history_manager import (
        cargar_historial,
        obtener_estadisticas_historial
    )
except:
    cargar_historial = None
    obtener_estadisticas_historial = None


# =========================================================
# APP
# =========================================================
app = Flask(__name__)
CORS(app)

AUTO_SCAN_INTERVAL = 60
MAX_SIGNALS = 10

cache_partidos: List[Dict] = []
cache_senales: List[Dict] = []
ultimo_scan: Optional[float] = None


# =========================================================
# HELPERS
# =========================================================
def now():
    return time.time()


def iso_now():
    return datetime.now(timezone.utc).isoformat()


def to_int(v, d=0):
    try:
        return int(float(v))
    except:
        return d


def to_float(v, d=0.0):
    try:
        return float(v)
    except:
        return d


# =========================================================
# NORMALIZADOR
# =========================================================
def normalizar_partido(p: Dict) -> Dict:
    return {
        "id": p.get("id"),
        "local": p.get("local"),
        "visitante": p.get("visitante"),
        "liga": p.get("liga"),
        "pais": p.get("pais"),
        "minuto": to_int(p.get("minuto"), 0),
        "marcador_local": to_int(p.get("marcador_local"), 0),
        "marcador_visitante": to_int(p.get("marcador_visitante"), 0),
        "xG": to_float(p.get("xG"), 0),
        "shots": to_int(p.get("shots"), 0),
        "shots_on_target": to_int(p.get("shots_on_target"), 0),
        "dangerous_attacks": to_int(p.get("dangerous_attacks"), 0),
        "momentum": p.get("momentum", "MEDIO"),
        "goal_pressure": p.get("goal_pressure", {}),
        "goal_predictor": p.get("goal_predictor", {}),
        "chaos": p.get("chaos", {}),
        "estado_partido": p.get("estado_partido", "LIVE"),
        "live": True
    }


def partido_valido(p: Dict) -> bool:
    minuto = to_int(p.get("minuto"), 0)
    return 1 <= minuto <= 88


# =========================================================
# GENERADOR DE SEÑALES
# =========================================================
def generar_senales(partidos: List[Dict]) -> List[Dict]:
    procesar_partido = get_procesar_partido()
    senales = []

    for p in partidos:
        if not partido_valido(p):
            continue

        if procesar_partido:
            try:
                s = procesar_partido(p)
            except Exception as e:
                print(f"[PIPELINE ERROR] {e}")
                s = None

            if s:
                senales.append(s)

    # ordenar por calidad real
    senales.sort(
        key=lambda x: (
            to_float(x.get("signal_score", 0)),
            to_float(x.get("confidence", 0)),
            to_float(x.get("value", 0)),
        ),
        reverse=True
    )

    return senales[:MAX_SIGNALS]


# =========================================================
# FETCH
# =========================================================
def obtener_partidos():
    if obtener_partidos_en_vivo:
        try:
            raw = obtener_partidos_en_vivo()
            return [normalizar_partido(p) for p in raw]
        except:
            pass

    # fallback
    return [
        {
            "id": "1",
            "local": "Arsenal",
            "visitante": "Chelsea",
            "liga": "Premier League",
            "pais": "England",
            "minuto": 25,
            "marcador_local": 1,
            "marcador_visitante": 1,
            "xG": 1.8,
            "shots": 10,
            "shots_on_target": 5,
            "dangerous_attacks": 30,
            "momentum": "ALTO",
            "goal_pressure": {"pressure_score": 7},
            "goal_predictor": {"predictor_score": 8},
            "chaos": {"chaos_score": 3},
            "estado_partido": "LIVE"
        }
    ]


def refrescar():
    global cache_partidos, cache_senales, ultimo_scan

    cache_partidos = obtener_partidos()
    cache_senales = generar_senales(cache_partidos)
    ultimo_scan = now()

    print(f"[SCAN] partidos={len(cache_partidos)} señales={len(cache_senales)}")


# =========================================================
# STATS REALES
# =========================================================
def get_stats():
    if not obtener_estadisticas_historial:
        return {"msg": "sin stats"}

    try:
        return obtener_estadisticas_historial()
    except:
        return {"msg": "error stats"}


# =========================================================
# ROUTES API
# =========================================================
@app.route("/status")
def status():
    return jsonify({
        "status": "ok",
        "time": iso_now()
    })


@app.route("/scan")
def scan():
    refrescar()
    return jsonify({
        "ok": True,
        "partidos": len(cache_partidos),
        "senales": len(cache_senales)
    })


@app.route("/signals")
def signals():
    return jsonify({
        "signals": cache_senales
    })


@app.route("/hot-matches")
def hot_matches():
    partidos = sorted(
        cache_partidos,
        key=lambda x: to_float(x.get("xG"), 0),
        reverse=True
    )

    return jsonify({
        "hot_matches": partidos[:20]
    })


@app.route("/history")
def history():
    if not cargar_historial:
        return jsonify([])

    try:
        data = cargar_historial()
        return jsonify(data[-50:])
    except:
        return jsonify([])


@app.route("/learning-stats")
def learning_stats():
    return jsonify(get_stats())


@app.route("/api/leagues")
def leagues():
    ligas = {}

    for p in cache_partidos:
        key = (p["liga"], p["pais"])
        ligas.setdefault(key, 0)
        ligas[key] += 1

    result = [
        {
            "league": k[0],
            "country": k[1],
            "matches": v
        }
        for k, v in ligas.items()
    ]

    return jsonify(result)


# =========================================================
# FRONT
# =========================================================
@app.route("/")
def dashboard():
    return render_template("dashboard.html")


# =========================================================
# START
# =========================================================
if __name__ == "__main__":
    refrescar()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

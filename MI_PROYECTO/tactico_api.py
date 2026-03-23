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

from core.signal_storage import obtener_senales

# =========================================================
# IMPORT STORAGE
# =========================================================
try:
    from core.signal_storage import guardar_senal, obtener_senales
    print("[IMPORT] signal_storage OK")
except Exception as e:
    print(f"[IMPORT ERROR] signal_storage -> {e}")
    guardar_senal = None
    obtener_senales = None


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
# HELPERS
# =========================================================
def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def detectar_hot_matches(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    hot = []

    for p in partidos:
        xg = _safe_float(p.get("xG"), 0)
        shots = _safe_int(p.get("shots"), 0)
        shots_on_target = _safe_int(p.get("shots_on_target"), 0)
        dangerous_attacks = _safe_int(p.get("dangerous_attacks"), 0)

        if (
            xg >= 1.2 or
            shots >= 8 or
            shots_on_target >= 3 or
            dangerous_attacks >= 18
        ):
            hot.append(p)

    hot.sort(
        key=lambda x: (
            _safe_float(x.get("xG"), 0),
            _safe_int(x.get("shots_on_target"), 0),
            _safe_int(x.get("dangerous_attacks"), 0),
        ),
        reverse=True
    )

    return hot


def construir_leagues(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ligas = {}

    for p in partidos:
        league = p.get("liga", "Unknown")
        country = p.get("pais", "Unknown")
        key = f"{country}::{league}"

        if key not in ligas:
            ligas[key] = {
                "league": league,
                "country": country,
                "matches_live": 0
            }

        ligas[key]["matches_live"] += 1

    return list(ligas.values())


def calcular_stats_desde_storage() -> Dict[str, Any]:
    if not obtener_senales:
        return STATE["stats"]

    try:
        data = obtener_senales()
    except Exception:
        return STATE["stats"]

    if not data:
        return {
            "ganadas": 0,
            "perdidas": 0,
            "win_rate": 0,
            "roi_percent": 0,
            "signals_elite": 0,
            "signals_top": 0,
            "value_promedio": 0,
            "riesgo_medio": 0,
        }

    ganadas = sum(1 for x in data if str(x.get("estado_resultado", "")).lower() == "ganada")
    perdidas = sum(1 for x in data if str(x.get("estado_resultado", "")).lower() == "perdida")
    total_resueltas = ganadas + perdidas

    win_rate = round((ganadas / total_resueltas) * 100, 2) if total_resueltas > 0 else 0

    profits = sum(_safe_float(x.get("profit"), 0.0) for x in data)
    stakes = sum(_safe_float(x.get("stake_amount"), 0.0) for x in data)
    roi_percent = round((profits / stakes) * 100, 2) if stakes > 0 else 0

    signals_elite = sum(1 for x in data if str(x.get("signal_rank", "")).upper() == "ELITE")
    signals_top = sum(1 for x in data if str(x.get("signal_rank", "")).upper() in ["TOP", "ALTA"])

    value_promedio = round(
        sum(_safe_float(x.get("value"), 0.0) for x in data) / len(data),
        2
    ) if data else 0

    riesgo_medio = round(
        sum(_safe_float(x.get("risk_score"), 0.0) for x in data) / len(data),
        2
    ) if data else 0

    return {
        "ganadas": ganadas,
        "perdidas": perdidas,
        "win_rate": win_rate,
        "roi_percent": roi_percent,
        "signals_elite": signals_elite,
        "signals_top": signals_top,
        "value_promedio": value_promedio,
        "riesgo_medio": riesgo_medio,
    }


def procesar_partidos(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    senales = []

    if not procesar_partido:
        return senales

    for p in partidos:
        try:
            s = procesar_partido(p)
            if s:
                senales.append(s)

                if guardar_senal:
                    try:
                        guardar_senal(s)
                    except Exception as e:
                        print(f"[STORAGE] ERROR guardar_senal -> {e}")

        except Exception as e:
            print(f"[ERROR PARTIDO] {e}")

    senales.sort(
        key=lambda x: (
            _safe_float(x.get("ai_decision_score"), 0),
            _safe_float(x.get("signal_score"), 0),
            _safe_float(x.get("confidence"), 0),
            _safe_float(x.get("value"), 0),
        ),
        reverse=True
    )

    return senales


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

    senales = procesar_partidos(partidos_fake)
    hot = detectar_hot_matches(partidos_fake)
    leagues = construir_leagues(partidos_fake)

    STATE["signals"] = senales
    STATE["hot_matches"] = hot
    STATE["leagues"] = leagues
    STATE["last_scan"] = int(time.time())
    STATE["stats"] = calcular_stats_desde_storage()

    if obtener_senales:
        try:
            all_signals = obtener_senales()
            STATE["history"] = all_signals[-50:]
        except Exception as e:
            print(f"[STORAGE] ERROR obtener_senales history -> {e}")

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
        "signals": obtener_senales()
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
    STATE["stats"] = calcular_stats_desde_storage()
    return jsonify(STATE["stats"])


# =========================================================
# HISTORIAL
# =========================================================
@app.route("/history")
def history():
    if obtener_senales:
        try:
            data = obtener_senales()
            return jsonify(data[-50:])
        except Exception as e:
            print(f"[STORAGE] ERROR history -> {e}")

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

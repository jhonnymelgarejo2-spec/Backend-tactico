import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# =========================================================
# IMPORTS DEL SISTEMA
# =========================================================
try:
    from signal_engine import generar_senal
except Exception:
    generar_senal = None

try:
    from live_fetcher import obtener_partidos_en_vivo
except Exception:
    obtener_partidos_en_vivo = None

try:
    from ai_brain import decision_final_ia
except Exception:
    decision_final_ia = None


# =========================================================
# APP FLASK
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__)
CORS(app)


# =========================================================
# CONFIG
# =========================================================
AUTO_SCAN_INTERVAL = 60
MAX_MINUTE_FOR_SIGNAL = 88
MIN_CONFIDENCE = 72
MIN_VALUE = 3

# 🔥 NUEVO
MAX_SIGNALS_TO_PUBLISH = 10

cache_partidos: List[Dict[str, Any]] = []
cache_senales: List[Dict[str, Any]] = []
cache_historial: List[Dict[str, Any]] = []

ultimo_scan_ts: Optional[float] = None
auto_scan_activo = True


# =========================================================
# HELPERS
# =========================================================
def now_ts() -> float:
    return time.time()


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalizar_texto(valor: Any) -> str:
    return str(valor or "").strip().lower()


def safe_upper(valor: Any) -> str:
    return str(valor or "").strip().upper()


def to_int(valor: Any, default: int = 0) -> int:
    try:
        if valor is None or valor == "":
            return default
        if isinstance(valor, str):
            valor = valor.replace("%", "").strip()
        return int(float(valor))
    except Exception:
        return default


def to_float(valor: Any, default: float = 0.0) -> float:
    try:
        if valor is None or valor == "":
            return default
        if isinstance(valor, str):
            valor = valor.replace("%", "").strip()
        return float(valor)
    except Exception:
        return default


# =========================================================
# FILTRO IA
# =========================================================
def filtrar_por_decision_ia(senal: Dict[str, Any]) -> bool:

    ai_recommendation = str(senal.get("ai_recommendation", "")).upper()
    chaos_level = str(senal.get("chaos_level", "")).upper()

    ai_conf = to_float(senal.get("ai_confidence_final"), 0)
    decision_score = to_float(senal.get("ai_decision_score"), 0)

    if ai_recommendation == "NO_APOSTAR":
        return False

    if chaos_level == "ALTO":
        return False

    if ai_conf < 58:
        return False

    if decision_score < 58:
        return False

    return True


# =========================================================
# GENERACION DE SEÑALES
# =========================================================
def generar_senales(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    senales = []

    for p in partidos:

        datos = {
            "id": p.get("id", ""),
            "momentum": p.get("momentum", "MEDIO"),
            "xG": p.get("xG", 0),
            "prob_real": p.get("prob_real", 0.75),
            "prob_implicita": p.get("prob_implicita", 0.54),
            "cuota": p.get("cuota", 1.85),
            "minuto": p.get("minuto", 0),
            "marcador_local": p.get("marcador_local", 0),
            "marcador_visitante": p.get("marcador_visitante", 0),
            "goal_pressure": p.get("goal_pressure", {}),
            "goal_predictor": p.get("goal_predictor", {}),
            "chaos": p.get("chaos", {}),
            "estado_partido": p.get("estado_partido", "activo"),
        }

        if generar_senal:
            try:
                senal = generar_senal(datos)
            except Exception:
                continue
        else:
            continue

        if not senal:
            continue

        senal_final = {
            "match_id": p.get("id"),
            "home": p.get("local"),
            "away": p.get("visitante"),
            "league": p.get("liga"),
            "country": p.get("pais"),
            "minute": p.get("minuto"),
            "score": f'{p.get("marcador_local")}-{p.get("marcador_visitante")}',
            "market": senal.get("mercado"),
            "selection": senal.get("apuesta"),
            "odd": senal.get("cuota"),
            "prob": senal.get("prob_real"),
            "value": senal.get("valor"),
            "confidence": senal.get("confianza"),
            "reason": senal.get("razon"),
        }

        # ======================
        # IA BRAIN
        # ======================

        if decision_final_ia:
            try:
                ai_eval = decision_final_ia(p, senal_final)
                senal_final.update(ai_eval)
            except Exception as e:
                print("AI ERROR:", e)

        # ======================
        # FILTRO IA
        # ======================

        if not filtrar_por_decision_ia(senal_final):
            continue

        senales.append(senal_final)

    # =========================================================
    # ORDEN FINAL
    # =========================================================

    senales.sort(
        key=lambda s: (
            to_float(s.get("ai_decision_score"), 0),
            to_float(s.get("confidence"), 0),
            to_float(s.get("value"), 0)
        ),
        reverse=True
    )

    # 🔥 SOLO TOP 10
    return senales[:MAX_SIGNALS_TO_PUBLISH]


# =========================================================
# REFRESH
# =========================================================
def refrescar_datos():
    global cache_partidos, cache_senales, ultimo_scan_ts

    raw = []

    if obtener_partidos_en_vivo:
        try:
            raw = obtener_partidos_en_vivo()
        except Exception as e:
            print("FETCH ERROR:", e)

    cache_partidos = raw
    cache_senales = generar_senales(cache_partidos)

    ultimo_scan_ts = now_ts()

    print("PARTIDOS:", len(cache_partidos))
    print("SEÑALES:", len(cache_senales))


# =========================================================
# API
# =========================================================
@app.route("/signals")
def signals():
    return jsonify({
        "total": len(cache_senales),
        "signals": cache_senales
    })


@app.route("/scan")
def scan():
    refrescar_datos()
    return jsonify({
        "ok": True,
        "signals": len(cache_senales)
    })


# =========================================================
# HTML
# =========================================================
@app.route("/")
def index():
    return render_template("dashboard.html")


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    refrescar_datos()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

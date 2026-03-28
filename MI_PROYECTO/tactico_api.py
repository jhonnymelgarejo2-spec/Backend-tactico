# tactico_api.py

from flask import Flask, jsonify, render_template
from typing import Dict, Any, List
import time

# =========================================================
# IMPORT PIPELINE OFICIAL
# =========================================================
try:
    from core.decision_pipeline import procesar_partido
    print("[IMPORTAR] pipeline de decisiones OK")
except Exception:
    try:
        from pipeline_de_decisión import procesar_partido
        print("[IMPORTAR] pipeline_de_decisión OK")
    except Exception as e:
        print(f"[ERROR IMPORTAR] decision_pipeline -> {e}")
        procesar_partido = None

# =========================================================
# IMPORT WRAPPER DE SENALES
# =========================================================
try:
    from signals import generar_senales
    print("[IMPORTAR] signals wrapper OK")
except Exception as e:
    print(f"[ERROR IMPORTAR] signals -> {e}")
    generar_senales = None

# =========================================================
# IMPORT STORAGE
# =========================================================
try:
    from core.signal_storage import obtener_senales, guardar_senal
    print("[IMPORTAR] almacenamiento de señales OK")
except Exception:
    try:
        from signal_storage import obtener_senales, guardar_senal
        print("[IMPORTAR] signal_storage OK")
    except Exception as e:
        print(f"[ERROR IMPORTAR] signal_storage -> {e}")
        obtener_senales = None
        guardar_senal = None

# =========================================================
# IMPORT HISTORY STATS
# =========================================================
try:
    from history_store import obtener_estadisticas_historial
    print("[IMPORTAR] history_store OK")
except Exception as e:
    print(f"[ERROR IMPORTAR] history_store -> {e}")
    obtener_estadisticas_historial = None

# =========================================================
# IMPORT FETCHER PRINCIPAL
# =========================================================
try:
    from api_football_fetcher import obtener_partidos_en_vivo
    print("[IMPORTAR] api_football_fetcher OK")
except Exception as e:
    print(f"[ERROR IMPORTAR] api_football_fetcher -> {e}")
    obtener_partidos_en_vivo = None

# =========================================================
# APP FLASK
# =========================================================
app = Flask(__name__)

# =========================================================
# ESTADO GLOBAL
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
    "leagues": [],
    "last_total_matches": 0,
}

MERCADOS_PERMITIDOS = {
    "OVER_NEXT_15_DYNAMIC",
    "OVER_MATCH_DYNAMIC",
    "UNDER_MATCH_DYNAMIC",
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


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _safe_upper(value: Any) -> str:
    return _safe_text(value).upper()


def _safe_lower(value: Any) -> str:
    return _safe_text(value).lower()


def _estado_partido_normalizado(partido: Dict[str, Any]) -> str:
    estado = partido.get("estado_partido", "")
    if isinstance(estado, dict):
        return _safe_lower(estado.get("estado", ""))
    return _safe_lower(estado)


def _esta_finalizado(partido: Dict[str, Any]) -> bool:
    estado = _estado_partido_normalizado(partido)
    return estado in {
        "finalizado", "finished", "ft", "ended"
    }


def _signal_sort_key(signal: Dict[str, Any]):
    return (
        _safe_float(signal.get("ranking_score")),
        _safe_float(signal.get("ai_decision_score")),
        _safe_float(signal.get("signal_score")),
        _safe_float(signal.get("confidence")),
        _safe_float(signal.get("value")),
    )


def _dedupe_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {}
    for s in signals:
        key = f"{s.get('match_id')}|{s.get('market')}|{s.get('selection')}|{s.get('minute')}"
        if key not in seen or _signal_sort_key(s) > _signal_sort_key(seen[key]):
            seen[key] = s
    return list(seen.values())


def _filtrar_publicables(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    publicables = [
        s for s in signals
        if (
            _safe_upper(s.get("market")) in MERCADOS_PERMITIDOS
            and _safe_float(s.get("confidence")) >= 64
            and _safe_float(s.get("value")) >= 0.5
            and _safe_float(s.get("risk_score")) <= 7.8
        )
    ]
    publicables.sort(key=_signal_sort_key, reverse=True)
    return publicables[:6]


# =========================================================
# HTML ROUTES
# =========================================================
@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# 🔥 NUEVA RUTA CLAVE
@app.route("/match_detail.html")
def match_detail_page():
    return render_template("match_detail.html")


# =========================================================
# SCAN
# =========================================================
@app.route("/scan")
def scan():
    partidos = obtener_partidos_en_vivo() if obtener_partidos_en_vivo else []
    senales = generar_senales(partidos) if generar_senales else []

    senales = _dedupe_signals(senales)
    top_signals = _filtrar_publicables(senales)

    STATE["signals"] = top_signals
    STATE["last_scan"] = int(time.time())

    return jsonify({
        "total_partidos": len(partidos),
        "total_senales": len(top_signals),
    })


# =========================================================
# SIGNALS
# =========================================================
@app.route("/signals")
def signals():
    return jsonify({
        "signals": STATE.get("signals", [])
    })


# =========================================================
# MATCH DETAIL API
# =========================================================
@app.route("/api/match/<match_id>")
def match_detail(match_id):
    for s in STATE.get("signals", []):
        if str(s.get("match_id")) == str(match_id):
            return jsonify(s)
    return jsonify({"error": "match no encontrado"}), 404


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

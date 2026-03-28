# tactico_api.py

from flask import Flask, jsonify, render_template
from typing import Dict, Any, List
import time
import os

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
# CONFIG
# =========================================================
MAX_SCAN_MATCHES = int(os.getenv("MAX_SCAN_MATCHES", "12"))
MAX_SIGNALS_VISIBLE = int(os.getenv("MAX_SIGNALS_VISIBLE", "6"))

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
    "last_scan_error": "",
}

MERCADOS_PERMITIDOS = {
    "OVER_NEXT_15_DYNAMIC",
    "OVER_MATCH_DYNAMIC",
    "UNDER_MATCH_DYNAMIC",
}

# =========================================================
# HELPERS BASE
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


# =========================================================
# HELPERS APP
# =========================================================
def _estado_partido_normalizado(partido: Dict[str, Any]) -> str:
    estado = partido.get("estado_partido", "")
    if isinstance(estado, dict):
        return _safe_lower(estado.get("estado", ""))
    return _safe_lower(estado)


def _esta_finalizado(partido: Dict[str, Any]) -> bool:
    estado = _estado_partido_normalizado(partido)
    return estado in {
        "finalizado",
        "finished",
        "ft",
        "ended",
        "after extra time",
        "penalties",
    }


def _signal_sort_key(signal: Dict[str, Any]):
    return (
        _safe_float(signal.get("ranking_score", 0.0), 0.0),
        _safe_float(signal.get("ai_decision_score", 0.0), 0.0),
        _safe_float(signal.get("signal_score", 0.0), 0.0),
        _safe_float(signal.get("confidence", 0.0), 0.0),
        _safe_float(signal.get("value", 0.0), 0.0),
    )


def _score_partido_para_scan(partido: Dict[str, Any]) -> float:
    minuto = _safe_int(partido.get("minuto"), 0)
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    pressure_score = _safe_float((partido.get("goal_pressure") or {}).get("pressure_score"), 0.0)
    predictor_score = _safe_float((partido.get("goal_predictor") or {}).get("predictor_score"), 0.0)

    score = 0.0

    if 15 <= minuto <= 85:
        score += 20
    elif 10 <= minuto <= 88:
        score += 10
    else:
        score -= 20

    score += xg * 10.0
    score += shots * 0.5
    score += shots_on_target * 2.5
    score += dangerous_attacks * 0.18
    score += pressure_score * 1.8
    score += predictor_score * 1.5

    return round(score, 2)


def _seleccionar_partidos_para_scan(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidatos = []

    for p in partidos:
        try:
            if _esta_finalizado(p):
                continue
            candidatos.append(p)
        except Exception:
            continue

    candidatos.sort(key=_score_partido_para_scan, reverse=True)

    seleccionados = candidatos[:MAX_SCAN_MATCHES]
    print(f"[SCAN] partidos seleccionados para procesamiento -> {len(seleccionados)} de {len(partidos)}")
    return seleccionados


def _dedupe_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {}

    for s in signals:
        match_id = _safe_text(s.get("match_id"))
        market = _safe_text(s.get("market"))
        selection = _safe_text(s.get("selection"))
        minute = str(_safe_int(s.get("minute", 0), 0))

        key = f"{match_id}|{market}|{selection}|{minute}"

        prev = seen.get(key)
        if prev is None:
            seen[key] = s
            continue

        if _signal_sort_key(s) > _signal_sort_key(prev):
            seen[key] = s

    return list(seen.values())


def _filtrar_publicables(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    publicables = [
        s for s in signals
        if (
            _safe_upper(s.get("market")) in MERCADOS_PERMITIDOS
            and bool(s.get("publish_ready", False))
            and _safe_float(s.get("confidence", 0.0), 0.0) >= 64
            and _safe_float(s.get("value", 0.0), 0.0) >= 0.5
            and _safe_float(s.get("risk_score", 10.0), 10.0) <= 7.8
            and _safe_float(s.get("ranking_score", 0.0), 0.0) >= 110
            and bool(s.get("qualifies_for_top", True))
        )
    ]

    publicables.sort(key=_signal_sort_key, reverse=True)
    return publicables[:MAX_SIGNALS_VISIBLE]


def _build_stats_from_signals(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
    if obtener_estadisticas_historial:
        try:
            stats = obtener_estadisticas_historial()
            if isinstance(stats, dict):
                return stats
        except Exception as e:
            print(f"[STATS] ERROR history_store -> {e}")

    if not signals:
        return {
            "ganadas": STATE["stats"].get("ganadas", 0),
            "perdidas": STATE["stats"].get("perdidas", 0),
            "win_rate": STATE["stats"].get("win_rate", 0),
            "roi_percent": STATE["stats"].get("roi_percent", 0),
            "signals_elite": 0,
            "signals_top": 0,
            "value_promedio": 0,
            "riesgo_medio": 0,
        }

    total = len(signals)
    elite = sum(1 for s in signals if _safe_upper(s.get("signal_rank")) == "ELITE")
    top = sum(1 for s in signals if _safe_upper(s.get("signal_rank")) == "TOP")
    avg_value = round(sum(_safe_float(s.get("value"), 0.0) for s in signals) / total, 2)
    avg_risk = round(sum(_safe_float(s.get("risk_score"), 0.0) for s in signals) / total, 2)

    return {
        "ganadas": STATE["stats"].get("ganadas", 0),
        "perdidas": STATE["stats"].get("perdidas", 0),
        "win_rate": STATE["stats"].get("win_rate", 0),
        "roi_percent": STATE["stats"].get("roi_percent", 0),
        "signals_elite": elite,
        "signals_top": top,
        "value_promedio": avg_value,
        "riesgo_medio": avg_risk,
    }


def _demo_partidos() -> List[Dict[str, Any]]:
    return [
        {
            "id": 99999,
            "local": "Argentina",
            "visitante": "Brasil",
            "liga": "Demo League",
            "pais": "World",
            "minuto": 45,
            "marcador_local": 2,
            "marcador_visitante": 1,
            "xG": 1.8,
            "shots": 12,
            "shots_on_target": 6,
            "dangerous_attacks": 24,
            "momentum": "ALTO",
            "goal_pressure": {"pressure_score": 7},
            "goal_predictor": {
                "predictor_score": 8,
                "goal_next_5_prob": 0.27,
                "goal_next_10_prob": 0.39
            },
            "chaos": {"chaos_score": 2},
            "estado_partido": "en_juego",
            "cuota": 1.85,
            "prob_real": 0.65,
            "prob_implicita": 0.54,
            "live": True,
        }
    ]


def obtener_partidos_para_scan() -> List[Dict[str, Any]]:
    if obtener_partidos_en_vivo:
        try:
            partidos = obtener_partidos_en_vivo()
            if isinstance(partidos, list) and partidos:
                print(f"[SCAN] fetcher principal devolvio -> {len(partidos)} partidos")
                return partidos
            print("[SCAN] fetcher principal devolvio vacio, usando demo")
        except Exception as e:
            print(f"[SCAN] ERROR fetcher principal -> {e}")

    print("[SCAN] usando partidos demo")
    return _demo_partidos()


def detectar_hot_matches(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    hot = []

    for p in partidos:
        if _esta_finalizado(p):
            continue

        xg = _safe_float(p.get("xG"), 0.0)
        shots = _safe_int(p.get("shots"), 0)
        shots_on_target = _safe_int(p.get("shots_on_target"), 0)
        dangerous_attacks = _safe_int(p.get("dangerous_attacks"), 0)
        minute = _safe_int(p.get("minuto"), 0)

        if (
            xg >= 1.0 or
            shots >= 7 or
            shots_on_target >= 2 or
            dangerous_attacks >= 16 or
            (15 <= minute <= 80 and (shots >= 5 or dangerous_attacks >= 14))
        ):
            hot.append(p)

    hot.sort(key=_score_partido_para_scan, reverse=True)
    return hot[:10]


def _signals_from_storage() -> List[Dict[str, Any]]:
    if not obtener_senales:
        return []

    try:
        data = obtener_senales()
        if not isinstance(data, list):
            return []

        filtradas = [
            s for s in data
            if _safe_upper(s.get("market")) in MERCADOS_PERMITIDOS
        ]

        filtradas = _dedupe_signals(filtradas)
        filtradas.sort(key=_signal_sort_key, reverse=True)

        return _filtrar_publicables(filtradas)
    except Exception as e:
        print(f"[SIGNALS] ERROR storage -> {e}")
        return []


# =========================================================
# PROCESAMIENTO
# =========================================================
def procesar_partidos(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(partidos, list):
        return []

    partidos = _seleccionar_partidos_para_scan(partidos)

    if generar_senales:
        try:
            senales = generar_senales(partidos)
            if not isinstance(senales, list):
                senales = []

            senales = _dedupe_signals(senales)
            senales.sort(key=_signal_sort_key, reverse=True)
            top_signals = _filtrar_publicables(senales)

            for s in top_signals:
                if guardar_senal:
                    try:
                        guardar_senal(s)
                    except Exception as e:
                        print(f"[ALMACENAMIENTO] ERROR guardar_senal -> {e}")

            print(f"[SCAN] total senales generadas -> {len(top_signals)}")
            return top_signals
        except Exception as e:
            print(f"[SCAN] ERROR wrapper generar_senales -> {e}")

    # Fallback directo al pipeline si falla el wrapper
    senales = []

    if not procesar_partido:
        print("[SCAN] procesar_partido no disponible")
        return senales

    for p in partidos:
        try:
            if _esta_finalizado(p):
                print(f"[SCAN] partido omitido por finalizado -> {p.get('id')}")
                continue

            s = procesar_partido(p)
            if not s:
                continue

            senales.append(s)

            if guardar_senal:
                try:
                    guardar_senal(s)
                except Exception as e:
                    print(f"[ALMACENAMIENTO] ERROR guardar_senal -> {e}")

        except Exception as e:
            print(f"[ERROR PARTIDO] {e}")

    senales = _dedupe_signals(senales)
    senales.sort(key=_signal_sort_key, reverse=True)

    top_signals = _filtrar_publicables(senales)
    print(f"[SCAN] total senales generadas -> {len(top_signals)}")
    return top_signals


# =========================================================
# ENDPOINTS HTML
# =========================================================
@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/match_detail.html")
def match_detail_html():
    return render_template("match_detail.html")


# =========================================================
# ENDPOINTS BASE
# =========================================================
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
# SCAN
# =========================================================
@app.route("/scan")
def scan():
    try:
        partidos = obtener_partidos_para_scan()
        senales = procesar_partidos(partidos)
        hot = detectar_hot_matches(partidos)

        STATE["signals"] = senales
        STATE["hot_matches"] = hot
        STATE["last_scan"] = int(time.time())
        STATE["last_total_matches"] = len(partidos)
        STATE["last_scan_error"] = ""

        ligas = sorted(list({
            f"{_safe_text(p.get('pais'))} - {_safe_text(p.get('liga'))}"
            for p in partidos
        }))
        STATE["leagues"] = ligas
        STATE["stats"] = _build_stats_from_signals(senales)

        return jsonify({
            "ok": True,
            "ultimo_scan": STATE["last_scan"],
            "total_partidos": len(partidos),
            "total_senales": len(senales),
            "procesados": min(len(partidos), MAX_SCAN_MATCHES),
        })
    except Exception as e:
        STATE["last_scan_error"] = str(e)
        print(f"[SCAN] ERROR GLOBAL -> {e}")

        return jsonify({
            "ok": False,
            "error": str(e),
            "ultimo_scan": STATE.get("last_scan", 0),
            "total_partidos": STATE.get("last_total_matches", 0),
            "total_senales": len(STATE.get("signals", [])),
        }), 200


# =========================================================
# SENALES
# =========================================================
@app.route("/signals")
def signals():
    current_signals = STATE.get("signals", [])
    if current_signals:
        current_sorted = sorted(current_signals, key=_signal_sort_key, reverse=True)
        current_sorted = _filtrar_publicables(current_sorted) or current_sorted[:MAX_SIGNALS_VISIBLE]
        print(f"[SIGNALS] desde memoria -> {len(current_sorted)}")
        return jsonify({"signals": current_sorted[:MAX_SIGNALS_VISIBLE]})

    fallback = _signals_from_storage()
    if fallback:
        print(f"[SIGNALS] obtenidas desde archivo -> {len(fallback)}")
        STATE["signals"] = fallback[:MAX_SIGNALS_VISIBLE]
        return jsonify({"signals": fallback[:MAX_SIGNALS_VISIBLE]})

    print("[SIGNALS] sin memoria ni storage -> devolviendo vacio")
    return jsonify({"signals": []})


# =========================================================
# HOT MATCHES
# =========================================================
@app.route("/hot-matches")
def hot_matches():
    hot = STATE.get("hot_matches", [])
    return jsonify({
        "hot_matches": hot[:10]
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
    if obtener_senales:
        try:
            data = obtener_senales()
            if isinstance(data, list):
                return jsonify(data[-50:])
        except Exception as e:
            print(f"[HISTORY] ERROR -> {e}")

    return jsonify(STATE["history"])


# =========================================================
# LIGAS
# =========================================================
@app.route("/api/leagues")
def leagues():
    return jsonify(STATE["leagues"])


# =========================================================
# DASHBOARD DATA
# =========================================================
@app.route("/dashboard-data")
def dashboard_data():
    signals_data = STATE.get("signals", [])
    if not signals_data:
        signals_data = _signals_from_storage()

    return jsonify({
        "status": "ok",
        "service": "jhonny_elite_v16",
        "last_scan": STATE.get("last_scan", 0),
        "last_scan_error": STATE.get("last_scan_error", ""),
        "total_signals": len(signals_data),
        "total_hot_matches": len(STATE.get("hot_matches", [])),
        "total_matches": STATE.get("last_total_matches", 0),
        "signals": signals_data[:MAX_SIGNALS_VISIBLE],
        "stats": STATE.get("stats", {}),
    })


# =========================================================
# TEST PIPELINE
# =========================================================
@app.route("/test-pipeline")
def test_pipeline():
    partidos = obtener_partidos_para_scan()
    partido_test = partidos[0] if partidos else _demo_partidos()[0]

    if not procesar_partido:
        return jsonify({"error": "pipeline no disponible"})

    try:
        resultado = procesar_partido(partido_test)
        return jsonify(resultado or {"msg": "No signal"})
    except Exception as e:
        return jsonify({
            "error": str(e),
            "type": type(e).__name__
        }), 500


# =========================================================
# API MATCH DETAIL
# =========================================================
@app.route("/api/match/<match_id>")
def match_detail(match_id):
    match_id_str = str(match_id)

    for s in STATE.get("signals", []):
        if str(s.get("match_id")) == match_id_str:
            return jsonify(s)

    fallback = _signals_from_storage()
    for s in fallback:
        if str(s.get("match_id")) == match_id_str:
            return jsonify(s)

    return jsonify({"error": "match no encontrado"}), 404


# =========================================================
# MAIN LOCAL
# =========================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)

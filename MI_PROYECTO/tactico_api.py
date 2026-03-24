from flask import Flask, jsonify, render_template
from typing import Dict, Any, List
import time

# =========================================================
# IMPORT PIPELINE
# =========================================================
try:
    from core.decision_pipeline import procesar_partido
    print("[IMPORTAR] pipeline de decisiones OK")
except Exception as e:
    print(f"[ERROR IMPORTAR] decision_pipeline -> {e}")
    procesar_partido = None

# =========================================================
# IMPORT STORAGE
# =========================================================
try:
    from core.signal_storage import obtener_senales, guardar_senal
    print("[IMPORTAR] almacenamiento de señales OK")
except Exception as e:
    print(f"[ERROR IMPORTAR] signal_storage -> {e}")
    obtener_senales = None
    guardar_senal = None

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
        "finalizado",
        "finished",
        "ft",
        "ended",
        "after extra time",
        "penalties",
    }


def _ranking_penalty(signal: Dict[str, Any]) -> float:
    penalty = 0.0

    minute = _safe_int(signal.get("minute"), 0)
    market = _safe_upper(signal.get("market"))
    confidence = _safe_float(signal.get("confidence"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 0.0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    signal_score = _safe_float(signal.get("signal_score"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)

    if minute >= 86:
        penalty += 30
    elif minute >= 80:
        penalty += 12

    if confidence < 70:
        penalty += 10
    elif confidence < 75:
        penalty += 4

    if value < 2:
        penalty += 14

    if risk_score >= 7:
        penalty += 18
    elif risk_score >= 6:
        penalty += 10

    if tactical_score < 12:
        penalty += 12

    if signal_score < 100:
        penalty += 10

    if market == "RESULT_HOLDS_NEXT_15" and tactical_score < 22:
        penalty += 18

    if market == "RESULT_HOLDS_NEXT_15" and confidence < 76:
        penalty += 14

    return round(penalty, 2)


def _ranking_score(signal: Dict[str, Any]) -> float:
    base = 0.0
    base += _safe_float(signal.get("ai_decision_score"), 0.0) * 1.8
    base += _safe_float(signal.get("signal_score"), 0.0) * 1.4
    base += _safe_float(signal.get("confidence"), 0.0) * 1.25
    base += _safe_float(signal.get("value"), 0.0) * 3.0
    base += _safe_float(signal.get("tactical_score"), 0.0) * 0.7
    base -= _safe_float(signal.get("risk_score"), 0.0) * 12.0
    return round(base, 2)


def _qualifies_for_top(signal: Dict[str, Any]) -> bool:
    minute = _safe_int(signal.get("minute"), 0)
    confidence = _safe_float(signal.get("confidence"), 0.0)
    value = _safe_float(signal.get("value"), 0.0)
    risk_score = _safe_float(signal.get("risk_score"), 10.0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0.0)
    signal_score = _safe_float(signal.get("signal_score"), 0.0)

    if minute >= 89:
        return False
    if confidence < 68:
        return False
    if value < 2:
        return False
    if risk_score > 6.5:
        return False
    if tactical_score < 12:
        return False
    if signal_score < 90:
        return False

    return True


def _decorate_signal(signal: Dict[str, Any]) -> Dict[str, Any]:
    s = dict(signal)

    ranking_penalty = _ranking_penalty(s)
    ranking_score_base = _ranking_score(s)
    ranking_score = round(ranking_score_base - ranking_penalty, 2)

    s["ranking_score_base"] = ranking_score_base
    s["ranking_penalty"] = ranking_penalty
    s["ranking_score"] = ranking_score
    s["qualifies_for_top"] = _qualifies_for_top(s)
    s["publish_ready"] = bool(s.get("publish_ready", True))
    s["publish_rank"] = int(s.get("publish_rank", 1) or 1)

    return s


def _dedupe_signals(signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = {}
    for s in signals:
        match_id = _safe_text(s.get("match_id"))
        market = _safe_text(s.get("market"))
        selection = _safe_text(s.get("selection"))
        key = f"{match_id}|{market}|{selection}"

        prev = seen.get(key)
        if prev is None:
            seen[key] = s
            continue

        prev_rank = _safe_float(prev.get("ranking_score"), 0.0)
        new_rank = _safe_float(s.get("ranking_score"), 0.0)
        if new_rank > prev_rank:
            seen[key] = s

    return list(seen.values())


def _build_stats_from_signals(signals: List[Dict[str, Any]]) -> Dict[str, Any]:
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
            "chaos": {"chaos_score": 3},
            "estado_partido": "en_juego",
            "cuota": 1.85,
            "prob_real": 0.75,
            "prob_implicita": 0.54,
        }
    ]


def obtener_partidos_para_scan() -> List[Dict[str, Any]]:
    if obtener_partidos_en_vivo:
        try:
            partidos = obtener_partidos_en_vivo()
            if isinstance(partidos, list) and partidos:
                print(f"[SCAN] fetcher principal devolvió -> {len(partidos)} partidos")
                return partidos
            print("[SCAN] fetcher principal devolvió vacío, usando demo")
        except Exception as e:
            print(f"[SCAN] ERROR fetcher principal -> {e}")

    print("[SCAN] usando partidos demo")
    return _demo_partidos()

# =========================================================
# PROCESAMIENTO
# =========================================================
def procesar_partidos(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    senales = []

    if not procesar_partido:
        print("[SCAN] procesar_partido no disponible")
        return senales

    for p in partidos:
        try:
            if _esta_finalizado(p):
                print(f"[SCAN] partido omitido por finalizado -> {p.get('id')}")
                continue

            print(f"[SCAN] procesando partido -> {p.get('id')}")
            s = procesar_partido(p)
            print(f"[SCAN] resultado pipeline -> {s}")

            if not s:
                print(f"[SCAN] señal vacía -> {p.get('id')}")
                continue

            s = _decorate_signal(s)

            if not s.get("qualifies_for_top", False):
                print(f"[SCAN] señal descartada por ranking mínimo -> {p.get('id')}")
                continue

            senales.append(s)
            print(f"[SCAN] señal agregada -> {p.get('id')}")

            if guardar_senal:
                try:
                    guardar_senal(s)
                    print(f"[ALMACENAMIENTO] señal guardada -> {p.get('id')}")
                except Exception as e:
                    print(f"[ALMACENAMIENTO] ERROR guardar_senal -> {e}")

        except Exception as e:
            print(f"[ERROR PARTIDO] {e}")

    senales = _dedupe_signals(senales)
    senales.sort(
        key=lambda x: (
            _safe_float(x.get("ranking_score"), 0.0),
            _safe_float(x.get("ai_decision_score"), 0.0),
            _safe_float(x.get("signal_score"), 0.0),
            _safe_float(x.get("confidence"), 0.0),
            _safe_float(x.get("value"), 0.0),
        ),
        reverse=True
    )

    top_signals = senales[:10]

    print(f"[SCAN] total señales generadas -> {len(top_signals)}")
    print(f"[SCAN] ESTADO señales -> {top_signals}")

    return top_signals


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
            xg >= 1.2 or
            shots >= 8 or
            shots_on_target >= 3 or
            dangerous_attacks >= 20 or
            (15 <= minute <= 80 and (shots >= 6 or dangerous_attacks >= 16))
        ):
            hot.append(p)

    return hot[:10]


def _signals_from_storage() -> List[Dict[str, Any]]:
    if not obtener_senales:
        return []

    try:
        data = obtener_senales()
        if not isinstance(data, list):
            return []

        decoradas = [_decorate_signal(s) for s in data]
        decoradas = [s for s in decoradas if s.get("qualifies_for_top", False)]
        decoradas = _dedupe_signals(decoradas)
        decoradas.sort(
            key=lambda x: _safe_float(x.get("ranking_score"), 0.0),
            reverse=True
        )
        return decoradas[:10]
    except Exception as e:
        print(f"[SIGNALS] ERROR storage -> {e}")
        return []

# =========================================================
# ENDPOINTS HTML
# =========================================================
@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

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
    partidos = obtener_partidos_para_scan()
    senales = procesar_partidos(partidos)
    hot = detectar_hot_matches(partidos)

    STATE["signals"] = senales
    STATE["hot_matches"] = hot
    STATE["last_scan"] = int(time.time())
    STATE["last_total_matches"] = len(partidos)

    ligas = sorted(list({
        f"{_safe_text(p.get('pais'))} - {_safe_text(p.get('liga'))}"
        for p in partidos
    }))
    STATE["leagues"] = ligas
    STATE["stats"] = _build_stats_from_signals(senales)

    return jsonify({
        "ultimo_scan": STATE["last_scan"],
        "total_partidos": len(partidos),
        "total_senales": len(senales),
    })

# =========================================================
# SEÑALES
# =========================================================
@app.route("/signals")
def signals():
    current_signals = STATE.get("signals", [])
    if current_signals:
        current_sorted = sorted(
            [_decorate_signal(s) for s in current_signals],
            key=lambda x: _safe_float(x.get("ranking_score"), 0.0),
            reverse=True
        )[:10]
        print(f"[SIGNALS] desde memoria -> {len(current_sorted)}")
        return jsonify({"signals": current_sorted})

    fallback = _signals_from_storage()
    if fallback:
        print(f"[SIGNALS] obtenidas desde archivo -> {len(fallback)}")
        STATE["signals"] = fallback[:10]
        return jsonify({"signals": fallback[:10]})

    print("[SIGNALS] memoria vacía y archivo vacío -> ejecutando rescan")
    partidos = obtener_partidos_para_scan()
    senales = procesar_partidos(partidos)

    STATE["signals"] = senales
    STATE["hot_matches"] = detectar_hot_matches(partidos)
    STATE["last_scan"] = int(time.time())
    STATE["last_total_matches"] = len(partidos)
    STATE["stats"] = _build_stats_from_signals(senales)

    return jsonify({"signals": senales[:10]})

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
    signals = STATE.get("signals", [])
    if not signals:
        signals = _signals_from_storage()

    return jsonify({
        "status": "ok",
        "service": "jhonny_elite_v16",
        "last_scan": STATE.get("last_scan", 0),
        "total_signals": len(signals),
        "total_hot_matches": len(STATE.get("hot_matches", [])),
        "total_matches": STATE.get("last_total_matches", 0),
        "signals": signals[:10],
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
        if resultado:
            resultado = _decorate_signal(resultado)
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

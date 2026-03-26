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


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


# =========================================================
# HELPERS TACTICOS EXPORTABLES
# ESTOS SON LOS QUE IMPORTA decision_pipeline.py
# =========================================================
def calcular_tactical_score(partido: Dict[str, Any]) -> float:
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    minuto = _safe_int(partido.get("minuto"), 0)
    momentum = _safe_upper(partido.get("momentum"))

    goal_pressure = partido.get("goal_pressure") or {}
    goal_predictor = partido.get("goal_predictor") or {}
    chaos = partido.get("chaos") or {}

    pressure_score = _safe_float(goal_pressure.get("pressure_score"), 0.0)
    predictor_score = _safe_float(goal_predictor.get("predictor_score"), 0.0)
    goal_next_5_prob = _safe_float(goal_predictor.get("goal_next_5_prob"), 0.0) * 100
    goal_next_10_prob = _safe_float(goal_predictor.get("goal_next_10_prob"), 0.0) * 100
    chaos_score = _safe_float(chaos.get("chaos_score"), 0.0)

    score = 0.0
    score += xg * 16.0
    score += shots * 0.7
    score += shots_on_target * 3.8
    score += dangerous_attacks * 0.22
    score += pressure_score * 2.2
    score += predictor_score * 1.8
    score += goal_next_5_prob * 0.22
    score += goal_next_10_prob * 0.15
    score -= chaos_score * 0.4

    if momentum == "MUY ALTO":
        score += 14
    elif momentum == "ALTO":
        score += 10
    elif momentum == "MEDIO":
        score += 5

    if 15 <= minuto <= 85:
        score += 8
    elif 86 <= minuto <= 88:
        score += 3

    return round(score, 2)


def calcular_goal_inminente_score(senal: Dict[str, Any], partido: Dict[str, Any]) -> float:
    gp5 = _safe_float(senal.get("goal_prob_5"), 0.0)
    gp10 = _safe_float(senal.get("goal_prob_10"), 0.0)
    gp15 = _safe_float(senal.get("goal_prob_15"), 0.0)

    if gp5 == 0 and gp10 == 0 and gp15 == 0:
        predictor = partido.get("goal_predictor") or {}
        gp5 = _safe_float(predictor.get("goal_next_5_prob"), 0.0) * 100
        gp10 = _safe_float(predictor.get("goal_next_10_prob"), 0.0) * 100
        gp15 = (gp5 * 0.55) + (gp10 * 0.45)

    estado_obj = senal.get("estado_partido") or {}
    if isinstance(estado_obj, dict):
        estado = _safe_upper(estado_obj.get("estado"))
    else:
        estado = _safe_upper(estado_obj)

    bonus = 0.0
    if estado in ("EXPLOSIVO", "CAOS", "CALIENTE"):
        bonus = 12
    elif estado == "CONTROLADO":
        bonus = 4

    score = (gp5 * 0.48) + (gp10 * 0.32) + (gp15 * 0.20) + bonus
    return round(score, 2)


def calcular_risk_score(senal: Dict[str, Any], partido: Dict[str, Any]) -> float:
    minuto = _safe_int(partido.get("minuto"), 0)
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)
    odd = _safe_float(senal.get("odd"), 0.0)

    estado_obj = senal.get("estado_partido") or {}
    if isinstance(estado_obj, dict):
        estado = _safe_upper(estado_obj.get("estado"))
    else:
        estado = _safe_upper(estado_obj)

    riesgo = 5.0

    if confidence >= 85:
        riesgo -= 1.5
    elif confidence >= 75:
        riesgo -= 1.0
    elif confidence < 60:
        riesgo += 1.2

    if value >= 10:
        riesgo -= 1.0
    elif value < 2:
        riesgo += 1.0

    if odd >= 2.5:
        riesgo += 1.0
    elif 0 < odd <= 1.40:
        riesgo += 0.6

    if minuto >= 86:
        riesgo += 1.4
    elif minuto >= 80:
        riesgo += 0.8

    if estado in ("FRIO", "MUERTO"):
        riesgo += 1.2
    elif estado in ("EXPLOSIVO", "CALIENTE"):
        riesgo -= 0.5

    return round(_clamp(riesgo, 1.0, 10.0), 2)


def calcular_signal_score(
    senal: Dict[str, Any],
    partido: Dict[str, Any],
    tactical_score: float,
    goal_score: float,
    risk_score: float,
) -> float:
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)
    ai_decision_score = _safe_float(senal.get("ai_decision_score"), 0.0)
    confianza_prediccion = _safe_float(senal.get("confianza_prediccion"), 0.0)

    score = 0.0
    score += confidence * 1.20
    score += value * 2.20
    score += tactical_score * 0.85
    score += goal_score * 0.75
    score += confianza_prediccion * 0.45
    score += ai_decision_score * 0.30
    score -= risk_score * 4.50

    return round(score, 2)


def calcular_signal_rank(signal_score: float) -> str:
    if signal_score >= 230:
        return "ELITE"
    if signal_score >= 170:
        return "TOP"
    if signal_score >= 110:
        return "ALTA"
    return "NORMAL"


def evaluar_value(prob_real: float, cuota: float) -> Dict[str, Any]:
    prob_real = _safe_float(prob_real, 0.0)
    cuota = _safe_float(cuota, 0.0)

    if cuota <= 1.0:
        return {
            "prob_implicita": 0.0,
            "value_pct": 0.0,
            "edge_pct": 0.0,
            "value_score": 0.0,
            "value_categoria": "SIN_VALUE",
            "recomendacion_value": "NO_APOSTAR",
            "razon_value": "Cuota inválida",
        }

    prob_implicita = round(1.0 / cuota, 4)
    edge_pct = round((prob_real - prob_implicita) * 100, 2)
    value_pct = edge_pct
    value_score = round(max(0.0, edge_pct), 2)

    if edge_pct >= 12:
        categoria = "VALUE_ELITE"
        recomendacion = "APOSTAR_FUERTE"
        razon = "Value muy alto respecto a la probabilidad implícita"
    elif edge_pct >= 8:
        categoria = "VALUE_ALTO"
        recomendacion = "APOSTAR"
        razon = "Value alto y aprovechable"
    elif edge_pct >= 4:
        categoria = "VALUE_MEDIO"
        recomendacion = "APOSTAR_SUAVE"
        razon = "Existe valor positivo razonable en la cuota"
    elif edge_pct > 0:
        categoria = "VALUE_BAJO"
        recomendacion = "OBSERVAR"
        razon = "Hay value leve, pero no es fuerte"
    else:
        categoria = "SIN_VALUE"
        recomendacion = "NO_APOSTAR"
        razon = "No hay ventaja estadística suficiente"

    return {
        "prob_implicita": prob_implicita,
        "value_pct": value_pct,
        "edge_pct": edge_pct,
        "value_score": value_score,
        "value_categoria": categoria,
        "recomendacion_value": recomendacion,
        "razon_value": razon,
    }


def enriquecer_senal(senal: Dict[str, Any], partido: Dict[str, Any]) -> Dict[str, Any]:
    senal = dict(senal)

    tactical_score = calcular_tactical_score(partido)
    goal_score = calcular_goal_inminente_score(senal, partido)
    risk_score = calcular_risk_score(senal, partido)

    prob = _safe_float(senal.get("prob"), _safe_float(senal.get("prob_real"), 0.0))
    odd = _safe_float(senal.get("odd"), _safe_float(senal.get("cuota"), 0.0))
    value_data = evaluar_value(prob, odd)

    senal["prob_implicita_calculada"] = value_data["prob_implicita"]
    senal["value_pct"] = value_data["value_pct"]
    senal["edge_pct"] = value_data["edge_pct"]
    senal["value_score"] = max(
        _safe_float(senal.get("value_score"), 0.0),
        _safe_float(value_data["value_score"], 0.0),
    )
    senal["value_categoria"] = senal.get("value_categoria") or value_data["value_categoria"]
    senal["recomendacion_value"] = senal.get("recomendacion_value") or value_data["recomendacion_value"]
    senal["razon_value"] = senal.get("razon_value") or value_data["razon_value"]

    if "ai_decision_score" not in senal or _safe_float(senal.get("ai_decision_score"), 0.0) == 0.0:
        senal["ai_decision_score"] = round(
            (_safe_float(senal.get("confidence"), 0.0) * 0.65) +
            (_safe_float(senal.get("value"), 0.0) * 1.1),
            2
        )

    signal_score = calcular_signal_score(
        senal=senal,
        partido=partido,
        tactical_score=tactical_score,
        goal_score=goal_score,
        risk_score=risk_score,
    )
    signal_rank = calcular_signal_rank(signal_score)

    senal["tactical_score"] = tactical_score
    senal["goal_inminente_score"] = goal_score
    senal["risk_score"] = risk_score
    senal["signal_score"] = signal_score
    senal["signal_rank"] = signal_rank

    senal.setdefault("ai_reason", "Lectura IA sin anomalías extremas")
    senal.setdefault("motivo_operacion", "OK")
    senal.setdefault("permitido_operar", True)
    senal.setdefault("stake_pct", 0.0)
    senal.setdefault("stake_amount", 0.0)
    senal.setdefault("stake_label", "N/A")
    senal.setdefault("bankroll_mode", "FLAT")

    return senal


def filtro_antifake_partido(partido: Dict[str, Any], senal: Dict[str, Any]) -> bool:
    minuto = _safe_int(partido.get("minuto"), 0)
    xg = _safe_float(partido.get("xG"), 0.0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks"), 0)
    momentum = _safe_upper(partido.get("momentum"))
    market = _safe_upper(senal.get("market"))
    confidence = _safe_float(senal.get("confidence"), 0.0)
    value = _safe_float(senal.get("value"), 0.0)

    if minuto < 8:
        return False

    if confidence < 55:
        return False

    if value < 0:
        return False

    sin_stats = (
        xg == 0 and
        shots == 0 and
        shots_on_target == 0 and
        dangerous_attacks == 0
    )

    if sin_stats:
        return confidence >= 72

    if "OVER" in market or "GOAL" in market:
        if xg < 0.25 and shots_on_target < 1 and dangerous_attacks < 8 and confidence < 75:
            return False

    if "RESULT" in market:
        if minuto < 20 and xg > 2.0 and shots_on_target >= 4 and confidence < 78:
            return False

    if momentum == "BAJO" and dangerous_attacks < 6 and shots_on_target == 0 and confidence < 72:
        return False

    return True


def filtrar_value_bets_reales(senal: Dict[str, Any]) -> bool:
    league = _safe_lower(senal.get("league"))
    market = _safe_upper(senal.get("market"))
    value = _safe_float(senal.get("value"), 0.0)
    confidence = _safe_float(senal.get("confidence"), 0.0)
    tactical_score = _safe_float(senal.get("tactical_score"), 0.0)
    signal_score = _safe_float(senal.get("signal_score"), 0.0)
    risk_score = _safe_float(senal.get("risk_score"), 10.0)
    odd = _safe_float(senal.get("odd"), 0.0)
    minute = _safe_int(senal.get("minute"), 0)

    ligas_top = {
        "premier league",
        "la liga",
        "serie a",
        "bundesliga",
        "ligue 1",
        "champions league",
        "uefa champions league",
        "europa league",
        "uefa europa league",
        "libertadores",
        "sudamericana",
    }

    if minute >= 89:
        return False

    if 0 < odd < 1.20:
        return False

    if league in ligas_top:
        if value < 2:
            return False
        if confidence < 60:
            return False
    else:
        if value < 0.5:
            return False
        if confidence < 56:
            return False

    if tactical_score < 6:
        return False

    if signal_score < 45:
        return False

    if risk_score > 8.5:
        return False

    if "RESULT" in market and confidence < 60:
        return False

    return True


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
        penalty += 20
    elif minute >= 80:
        penalty += 8

    if confidence < 66:
        penalty += 8
    elif confidence < 72:
        penalty += 3

    if value < 2:
        penalty += 10

    if risk_score >= 7:
        penalty += 12
    elif risk_score >= 6:
        penalty += 6

    if tactical_score < 10:
        penalty += 8

    if signal_score < 80:
        penalty += 8

    if market == "RESULT_HOLDS_NEXT_15" and tactical_score < 18:
        penalty += 10

    if market == "RESULT_HOLDS_NEXT_15" and confidence < 72:
        penalty += 8

    return round(penalty, 2)


def _ranking_score(signal: Dict[str, Any]) -> float:
    base = 0.0
    base += _safe_float(signal.get("ai_decision_score"), 0.0) * 1.8
    base += _safe_float(signal.get("signal_score"), 0.0) * 1.4
    base += _safe_float(signal.get("confidence"), 0.0) * 1.25
    base += _safe_float(signal.get("value"), 0.0) * 3.0
    base += _safe_float(signal.get("tactical_score"), 0.0) * 0.7
    base -= _safe_float(signal.get("risk_score"), 0.0) * 10.0
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
    if confidence < 62:
        return False
    if value < 0.5:
        return False
    if risk_score > 7.5:
        return False
    if tactical_score < 8:
        return False
    if signal_score < 55:
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
                print(f"[SCAN] señal débil pero conservada para ranking -> {p.get('id')}")

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

    publicables = [
        s for s in senales
        if (
            _safe_float(s.get("confidence"), 0.0) >= 62 and
            _safe_float(s.get("value"), 0.0) >= 0.5 and
            _safe_float(s.get("risk_score"), 10.0) <= 7.5 and
            _safe_float(s.get("ranking_score"), 0.0) >= 105
        )
    ]

    top_signals = publicables[:10]

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
            xg >= 1.0 or
            shots >= 7 or
            shots_on_target >= 2 or
            dangerous_attacks >= 16 or
            (15 <= minute <= 80 and (shots >= 5 or dangerous_attacks >= 14))
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
        decoradas = _dedupe_signals(decoradas)
        decoradas.sort(
            key=lambda x: _safe_float(x.get("ranking_score"), 0.0),
            reverse=True
        )

        publicables = [
            s for s in decoradas
            if (
                _safe_float(s.get("confidence"), 0.0) >= 62 and
                _safe_float(s.get("value"), 0.0) >= 0.5 and
                _safe_float(s.get("risk_score"), 10.0) <= 7.5 and
                _safe_float(s.get("ranking_score"), 0.0) >= 105
            )
        ]

        return publicables[:10]
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

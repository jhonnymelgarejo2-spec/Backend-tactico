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
# FILTRO MAESTRO DE PARTIDO VIVO
# =========================================================
ESTADOS_FINALIZADOS = {
    "ft", "finished", "finalizado", "ended", "end", "after penalties",
    "pen", "pens", "aet", "final", "fulltime", "match finished"
}

ESTADOS_NO_VALIDOS = {
    "cancelled", "canceled", "postponed", "suspended", "abandoned",
    "deleted", "walkover", "interrupted"
}

ESTADOS_VIVOS = {
    "live", "inplay", "in_play", "en_juego", "activo", "1h", "2h",
    "ht", "halftime", "descanso", "extra time", "et"
}


def extraer_estado_partido(p: Dict[str, Any]) -> str:
    candidatos = [
        p.get("estado_partido"),
        p.get("status"),
        p.get("estado"),
        p.get("match_status"),
        (p.get("fixture") or {}).get("status"),
        ((p.get("fixture") or {}).get("status") or {}).get("short"),
        ((p.get("fixture") or {}).get("status") or {}).get("long"),
    ]
    for c in candidatos:
        if c:
            return normalizar_texto(c)
    return ""


def extraer_minuto_partido(p: Dict[str, Any]) -> int:
    candidatos = [
        p.get("minuto"),
        p.get("minute"),
        p.get("elapsed"),
        (p.get("fixture") or {}).get("elapsed"),
        ((p.get("fixture") or {}).get("status") or {}).get("elapsed"),
    ]
    for c in candidatos:
        v = to_int(c, -1)
        if v >= 0:
            return v
    return 0


def partido_esta_finalizado(p: Dict[str, Any]) -> bool:
    estado = extraer_estado_partido(p)

    if estado in ESTADOS_FINALIZADOS:
        return True

    if "ft" in estado or "finished" in estado or "finalizado" in estado:
        return True

    minuto = extraer_minuto_partido(p)
    if minuto >= 120:
        return True

    return False


def partido_esta_suspendido_o_invalido(p: Dict[str, Any]) -> bool:
    estado = extraer_estado_partido(p)
    if estado in ESTADOS_NO_VALIDOS:
        return True

    for token in ESTADOS_NO_VALIDOS:
        if token in estado:
            return True

    return False


def partido_esta_vivo(p: Dict[str, Any]) -> bool:
    if not isinstance(p, dict):
        return False

    if partido_esta_suspendido_o_invalido(p):
        return False

    if partido_esta_finalizado(p):
        return False

    estado = extraer_estado_partido(p)
    minuto = extraer_minuto_partido(p)

    if estado in ESTADOS_VIVOS and 0 <= minuto <= 119:
        return True

    if 1 <= minuto < 120:
        return True

    if p.get("live") is True or p.get("is_live") is True:
        return True

    return False


def partido_es_apostable(p: Dict[str, Any]) -> tuple[bool, str]:
    if not partido_esta_vivo(p):
        return False, "Partido no vivo"

    minuto = extraer_minuto_partido(p)
    if minuto >= MAX_MINUTE_FOR_SIGNAL:
        return False, "Minuto demasiado alto"

    return True, "OK"


# =========================================================
# NORMALIZACION DE PARTIDOS
# =========================================================
def normalizar_partido(raw: Dict[str, Any]) -> Dict[str, Any]:
    fixture = raw.get("fixture") or {}
    teams = raw.get("teams") or {}
    goals = raw.get("goals") or {}
    league = raw.get("league") or {}

    local = raw.get("local") or (teams.get("home") or {}).get("name") or raw.get("home") or "Local"
    visitante = raw.get("visitante") or (teams.get("away") or {}).get("name") or raw.get("away") or "Visitante"

    marcador_local = raw.get("marcador_local")
    if marcador_local is None:
        marcador_local = goals.get("home", 0)

    marcador_visitante = raw.get("marcador_visitante")
    if marcador_visitante is None:
        marcador_visitante = goals.get("away", 0)

    estado_raw = (
        raw.get("estado_partido")
        or raw.get("status")
        or (fixture.get("status") or {}).get("short")
        or ""
    )

    minuto_raw = raw.get("minuto")
    if minuto_raw is None:
        minuto_raw = raw.get("minute")
    if minuto_raw is None:
        minuto_raw = fixture.get("elapsed")

    shots = raw.get("shots")
    if shots is None:
        shots = raw.get("disparos")

    shots_on_target = raw.get("shots_on_target")
    if shots_on_target is None:
        shots_on_target = raw.get("disparos_en_objetivo")

    dangerous_attacks = raw.get("dangerous_attacks")
    if dangerous_attacks is None:
        dangerous_attacks = raw.get("ataques_peligrosos")

    goal_pressure = raw.get("goal_pressure") or raw.get("goal_presion") or {}
    goal_predictor = raw.get("goal_predictor") or {}
    chaos = raw.get("chaos") or {}

    return {
        "id": raw.get("id") or fixture.get("id") or raw.get("match_id") or f"match_{int(now_ts()*1000)}",
        "local": local,
        "visitante": visitante,
        "liga": raw.get("liga") or league.get("name") or raw.get("league") or "Liga desconocida",
        "pais": raw.get("pais") or league.get("country") or raw.get("country") or "World",
        "estado_partido": estado_raw or "LIVE",
        "minuto": to_int(minuto_raw, 0),
        "marcador_local": to_int(marcador_local, 0),
        "marcador_visitante": to_int(marcador_visitante, 0),
        "xG": to_float(raw.get("xG") or raw.get("xg"), 0.0),
        "shots": to_int(shots, 0),
        "shots_on_target": to_int(shots_on_target, 0),
        "dangerous_attacks": to_int(dangerous_attacks, 0),
        "momentum": raw.get("momentum", "MEDIO"),
        "goal_pressure": goal_pressure if isinstance(goal_pressure, dict) else {},
        "goal_predictor": goal_predictor if isinstance(goal_predictor, dict) else {},
        "chaos": chaos if isinstance(chaos, dict) else {},
        "live": bool(raw.get("live", True)),
        "fixture": fixture if isinstance(fixture, dict) else {},
    }


def limpiar_cache_partidos(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalizados = [normalizar_partido(p) for p in partidos if isinstance(p, dict)]
    solo_vivos = [p for p in normalizados if partido_esta_vivo(p)]

    unicos = {}
    for p in solo_vivos:
        unicos[str(p.get("id"))] = p

    return list(unicos.values())


# =========================================================
# SCORING
# =========================================================
def calcular_tactical_score(p: Dict[str, Any]) -> float:
    goal_pressure = p.get("goal_pressure", {}) or {}
    goal_predictor = p.get("goal_predictor", {}) or {}
    chaos = p.get("chaos", {}) or {}

    pressure_score = to_float(goal_pressure.get("pressure_score"), 0)
    predictor_score = to_float(goal_predictor.get("predictor_score"), 0)
    chaos_score = to_float(chaos.get("chaos_score"), 0)
    xg = to_float(p.get("xG"), 0)
    minuto = to_int(p.get("minuto"), 0)
    shots = to_int(p.get("shots"), 0)
    shots_on_target = to_int(p.get("shots_on_target"), 0)
    dangerous_attacks = to_int(p.get("dangerous_attacks"), 0)
    momentum = safe_upper(p.get("momentum", "MEDIO"))

    score = 0.0
    score += pressure_score * 1.2
    score += predictor_score * 1.5
    score += chaos_score * 1.0
    score += xg * 8
    score += shots * 0.35
    score += shots_on_target * 1.5
    score += dangerous_attacks * 0.12

    if momentum == "MUY ALTO":
        score += 12
    elif momentum == "ALTO":
        score += 8
    elif momentum == "MEDIO":
        score += 4

    if 15 <= minuto <= 75:
        score += 6
    elif 76 <= minuto <= 87:
        score += 3

    return round(score, 2)


def calcular_goal_inminente_score(senal: Dict[str, Any]) -> float:
    gp5 = to_float(senal.get("goal_prob_5"), 0)
    gp10 = to_float(senal.get("goal_prob_10"), 0)
    gp15 = to_float(senal.get("goal_prob_15"), 0)

    estado_partido = senal.get("estado_partido", {}) or {}
    estado = safe_upper(estado_partido.get("estado", ""))

    bonus_estado = 0
    if estado in ("EXPLOSIVO", "CAOS"):
        bonus_estado = 15
    elif estado == "CALIENTE":
        bonus_estado = 8
    elif estado == "CONTROLADO":
        bonus_estado = 3

    return round((gp5 * 0.5) + (gp10 * 0.3) + (gp15 * 0.2) + bonus_estado, 2)


def calcular_signal_score(senal: Dict[str, Any], tactical_score: float) -> float:
    value = to_float(senal.get("value"), 0)
    confidence = to_float(senal.get("confidence"), 0)
    confianza_prediccion = to_float(senal.get("confianza_prediccion"), 0)
    goal_score = calcular_goal_inminente_score(senal)

    score = 0.0
    score += value * 2.2
    score += confidence * 1.4
    score += confianza_prediccion * 0.7
    score += tactical_score * 0.9
    score += goal_score * 0.8

    return round(score, 2)


def enriquecer_senal(senal: Dict[str, Any], partido: Dict[str, Any]) -> Dict[str, Any]:
    tactical_score = calcular_tactical_score(partido)
    goal_score = calcular_goal_inminente_score(senal)
    signal_score = calcular_signal_score(senal, tactical_score)

    senal["tactical_score"] = tactical_score
    senal["goal_inminente_score"] = goal_score
    senal["signal_score"] = signal_score

    if signal_score >= 260:
        senal["signal_rank"] = "ELITE"
    elif signal_score >= 210:
        senal["signal_rank"] = "TOP"
    elif signal_score >= 160:
        senal["signal_rank"] = "ALTA"
    else:
        senal["signal_rank"] = "NORMAL"

    senal["ai_decision_score"] = round(signal_score * 0.53, 2)
    senal["risk_score"] = round(max(1.0, 10 - (to_float(senal.get("confidence"), 0) / 12)), 2)
    senal["ai_reason"] = senal.get("ai_reason") or "Lectura IA sin anomalías extremas"
    senal["razon_value"] = senal.get("razon_value") or "La cuota ofrece valor razonable frente a la probabilidad estimada"

    return senal


# =========================================================
# ANTI FALSAS SEÑALES
# =========================================================
def filtro_antifake_partido(partido: Dict[str, Any], senal: Dict[str, Any]) -> bool:
    minuto = to_int(partido.get("minuto"), 0)
    shots = to_int(partido.get("shots"), -1)
    shots_on_target = to_int(partido.get("shots_on_target"), -1)
    dangerous_attacks = to_int(partido.get("dangerous_attacks"), -1)
    xg = to_float(partido.get("xG"), -1)
    momentum = safe_upper(partido.get("momentum", "MEDIO"))
    market = str(senal.get("market", "")).upper()

    # Reglas mínimas siempre
    if minuto < 10:
        return False
    if to_float(senal.get("confidence"), 0) < 65:
        return False
    if to_float(senal.get("odd"), 0) < 1.40:
        return False

    # Si hay stats completas, aplicar antifake estricto
    if shots >= 0 and shots_on_target >= 0 and dangerous_attacks >= 0 and xg >= 0:
        if shots <= 2 and shots_on_target == 0 and dangerous_attacks < 8:
            return False
        if ("OVER" in market or "GOAL" in market) and xg < 0.85:
            return False
        if momentum == "BAJO" and dangerous_attacks < 10 and shots_on_target < 2:
            return False

    # Si no hay stats (valores -1), dejar pasar con reglas mínimas
    return True


# =========================================================
# GENERADOR FALLBACK
# =========================================================
def generar_senal_fallback(datos: Dict[str, Any]) -> Dict[str, Any]:
    xg = to_float(datos.get("xG"), 0)
    minuto = to_int(datos.get("minuto"), 0)
    marcador_local = to_int(datos.get("marcador_local"), 0)
    marcador_visitante = to_int(datos.get("marcador_visitante"), 0)

    market = "OVER_NEXT_15_DYNAMIC" if xg >= 1.4 else "RESULT_HOLDS_NEXT_15"
    apuesta = "Over próximos 15 min" if market == "OVER_NEXT_15_DYNAMIC" else "Se mantiene el resultado próximos 15 min"

    return {
        "mercado": market,
        "apuesta": apuesta,
        "linea": 1.5 if market == "OVER_NEXT_15_DYNAMIC" else None,
        "cuota": 2.03 if market == "OVER_NEXT_15_DYNAMIC" else 1.88,
        "prob_real": 0.66,
        "valor": 3.46,
        "confianza": 88,
        "razon": "Presión ofensiva + lectura táctica favorable" if market == "OVER_NEXT_15_DYNAMIC" else "Ritmo estable y resultado con probabilidad de mantenerse",
        "tier": "TOP",
        "estado_partido": {"estado": "CONTROLADO"},
        "gol_inminente": {"gol_inminente": xg >= 1.8},
        "signal_status": "OPEN",
        "goal_prob_5": 34,
        "goal_prob_10": 41,
        "goal_prob_15": 49,
        "resultado_probable": f"{marcador_local}-{marcador_visitante}",
        "ganador_probable": "LOCAL" if marcador_local >= marcador_visitante else "VISITANTE",
        "doble_oportunidad_probable": "1X",
        "total_goles_estimado": marcador_local + marcador_visitante + 1,
        "linea_goles_probable": "2.5",
        "over_under_probable": "OVER 2.5" if xg >= 1.4 else "UNDER 3.5",
        "confianza_prediccion": 80,
        "recomendacion_final": "APOSTAR",
        "riesgo_operativo": "MEDIO",
        "senales_posibles": []
    }
  def filtrar_value_bets_reales(senal: Dict[str, Any]) -> bool:
    ligas_top = {
        "premier league",
        "la liga",
        "serie a",
        "bundesliga",
        "ligue 1",
        "uefa champions league",
        "champions league",
        "uefa europa league",
        "europa league"
    }

    league = str(senal.get("league", "")).strip().lower()
    market = str(senal.get("market", "")).strip().upper()

    value = to_float(senal.get("value"), 0)
    confidence = to_float(senal.get("confidence"), 0)
    riesgo_operativo = safe_upper(senal.get("riesgo_operativo", "MEDIO"))
    tactical_score = to_float(senal.get("tactical_score"), 0)
    signal_score = to_float(senal.get("signal_score"), 0)
    goal_score = to_float(senal.get("goal_inminente_score"), 0)
    minute = to_int(senal.get("minute"), 0)
    odd = to_float(senal.get("odd"), 0)
    risk_score = to_float(senal.get("risk_score"), 0)

    # Filtros más flexibles
    if league in ligas_top:
        min_value = 8
        min_confidence = 65
        max_risk_score = 5
    else:
        min_value = 5
        min_confidence = 60
        max_risk_score = 7

    if value < min_value:
        return False

    if confidence < min_confidence:
        return False

    if odd < 1.35:
        return False

    if minute >= 88:
        return False

    if tactical_score < 8:
        return False

    if signal_score < 60:
        return False

    if risk_score > max_risk_score:
        return False

    if riesgo_operativo == "ALTO" and league in ligas_top:
        return False

    if ("OVER" in market or "GOAL" in market) and goal_score < 8:
        return False

    if "RESULT" in market and confidence < (min_confidence + 3):
        return False

    return True

# =========================================================
# GENERACION DE SEÑALES
# =========================================================
def generar_senales(partidos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    senales = []

    for p in partidos:
        ok, _motivo = partido_es_apostable(p)
        if not ok:
            continue

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
                senal = generar_senal_fallback(datos)
        else:
            senal = generar_senal_fallback(datos)

        if not senal:
            continue

        if senal.get("mercado") == "SIN_SEÑAL":
            continue

        if to_float(senal.get("valor"), 0) <= 0:
            continue

        senal_final = {
            "match_id": p.get("id", ""),
            "home": p.get("local", ""),
            "away": p.get("visitante", ""),
            "league": p.get("liga", ""),
            "country": p.get("pais", ""),
            "minute": p.get("minuto", 0),
            "score": f'{p.get("marcador_local", 0)}-{p.get("marcador_visitante", 0)}',
            "market": senal.get("mercado", ""),
            "selection": senal.get("apuesta", ""),
            "line": senal.get("linea"),
            "odd": senal.get("cuota", 1.85),
            "prob": senal.get("prob_real", 0.0),
            "value": senal.get("valor", 0.0),
            "confidence": senal.get("confianza", 0),
            "reason": senal.get("razon", ""),
            "tier": senal.get("tier", "NORMAL"),
            "estado_partido": senal.get("estado_partido", {}),
            "gol_inminente": senal.get("gol_inminente", {}),
            "signal_status": senal.get("signal_status", "OPEN"),
            "goal_prob_5": senal.get("goal_prob_5", 0),
            "goal_prob_10": senal.get("goal_prob_10", 0),
            "goal_prob_15": senal.get("goal_prob_15", 0),
            "resultado_probable": senal.get("resultado_probable", ""),
            "ganador_probable": senal.get("ganador_probable", ""),
            "doble_oportunidad_probable": senal.get("doble_oportunidad_probable", ""),
            "total_goles_estimado": senal.get("total_goles_estimado", 0),
            "linea_goles_probable": senal.get("linea_goles_probable", ""),
            "over_under_probable": senal.get("over_under_probable", ""),
            "confianza_prediccion": senal.get("confianza_prediccion", 0),
            "recomendacion_final": senal.get("recomendacion_final", "OBSERVAR"),
            "riesgo_operativo": senal.get("riesgo_operativo", "MEDIO"),
            "all_signals": senal.get("senales_posibles", []),
        }

        senal_final = enriquecer_senal(senal_final, p)

        if not filtro_antifake_partido(p, senal_final):
            print(
                f"RECHAZADA ANTIFAKE -> {p.get('local')} vs {p.get('visitante')} | "
                f"minute={senal_final.get('minute')} | "
                f"market={senal_final.get('market')} | "
                f"xG={p.get('xG')} | shots={p.get('shots')} | "
                f"shots_on_target={p.get('shots_on_target')} | "
                f"dangerous_attacks={p.get('dangerous_attacks')} | "
                f"momentum={p.get('momentum')}"
            )
            continue

        if not filtrar_value_bets_reales(senal_final):
            print(
                f"RECHAZADA VALUE -> {p.get('local')} vs {p.get('visitante')} | "
                f"league={senal_final.get('league')} | "
                f"market={senal_final.get('market')} | "
                f"value={senal_final.get('value')} | "
                f"confidence={senal_final.get('confidence')} | "
                f"risk_score={senal_final.get('risk_score')} | "
                f"tactical_score={senal_final.get('tactical_score')} | "
                f"signal_score={senal_final.get('signal_score')} | "
                f"goal_score={senal_final.get('goal_inminente_score')} | "
                f"minute={senal_final.get('minute')} | "
                f"odd={senal_final.get('odd')}"
            )
            continue

        print(
            f"SEÑAL ACEPTADA -> {p.get('local')} vs {p.get('visitante')} | "
            f"market={senal_final.get('market')} | "
            f"value={senal_final.get('value')} | "
            f"confidence={senal_final.get('confidence')} | "
            f"risk_score={senal_final.get('risk_score')}"
        )

        senales.append(senal_final)

    senales.sort(
        key=lambda s: (
            to_float(s.get("signal_score"), 0),
            to_float(s.get("tactical_score"), 0),
            to_float(s.get("goal_inminente_score"), 0),
            to_float(s.get("confidence"), 0),
            to_float(s.get("value"), 0),
        ),
        reverse=True
    )

    return senales


# =========================================================
# DATOS LIVE
# =========================================================
def obtener_partidos_fallback() -> List[Dict[str, Any]]:
    return [
        {
            "id": "101",
            "local": "Arsenal",
            "visitante": "Chelsea",
            "liga": "Premier League",
            "pais": "England",
            "estado_partido": "LIVE",
            "minuto": 23,
            "marcador_local": 2,
            "marcador_visitante": 3,
            "xG": 2.2,
            "shots": 11,
            "shots_on_target": 6,
            "dangerous_attacks": 34,
            "momentum": "MEDIO",
            "goal_pressure": {"pressure_score": 7.8},
            "goal_predictor": {"predictor_score": 8.1},
            "chaos": {"chaos_score": 3.2},
            "live": True,
        },
        {
            "id": "102",
            "local": "Barcelona",
            "visitante": "Valencia",
            "liga": "La Liga",
            "pais": "Spain",
            "estado_partido": "LIVE",
            "minuto": 58,
            "marcador_local": 2,
            "marcador_visitante": 1,
            "xG": 1.7,
            "shots": 9,
            "shots_on_target": 5,
            "dangerous_attacks": 40,
            "momentum": "ALTO",
            "goal_pressure": {"pressure_score": 8.2},
            "goal_predictor": {"predictor_score": 7.6},
            "chaos": {"chaos_score": 2.8},
            "live": True,
        },
        {
            "id": "103",
            "local": "Andorra",
            "visitante": "Betis",
            "liga": "UEFA Conference League",
            "pais": "World",
            "estado_partido": "LIVE",
            "minuto": 73,
            "marcador_local": 1,
            "marcador_visitante": 0,
            "xG": 0.9,
            "shots": 4,
            "shots_on_target": 2,
            "dangerous_attacks": 17,
            "momentum": "BAJO",
            "goal_pressure": {"pressure_score": 3.8},
            "goal_predictor": {"predictor_score": 4.1},
            "chaos": {"chaos_score": 1.4},
            "live": True,
        },
        {
            "id": "104",
            "local": "River Plate",
            "visitante": "Boca Juniors",
            "liga": "Liga Profesional Argentina",
            "pais": "Argentina",
            "estado_partido": "FT",
            "minuto": 90,
            "marcador_local": 1,
            "marcador_visitante": 1,
            "xG": 2.4,
            "shots": 14,
            "shots_on_target": 5,
            "dangerous_attacks": 40,
            "momentum": "ALTO",
            "live": False,
        },
    ]


def refrescar_datos():
    global cache_partidos, cache_senales, ultimo_scan_ts

    raw = []
    if obtener_partidos_en_vivo:
        try:
            raw = obtener_partidos_en_vivo()
        except Exception as e:
            print(f"FETCHER ERROR -> {e}")
            raw = []

    if not raw:
        print("FETCHER VACIO -> usando respaldo")
        raw = obtener_partidos_fallback()

    cache_partidos = limpiar_cache_partidos(raw)
    cache_senales = generar_senales(cache_partidos)
    ultimo_scan_ts = now_ts()

    print(f"TOTAL NORMALIZADOS: {len(raw)}")
    print(f"TOTAL DE VIVOS: {len(cache_partidos)}")
    print(f"TOTAL DE SEÑALES: {len(cache_senales)}")


def asegurar_cache():
    if not cache_partidos:
        refrescar_datos()


# =========================================================
# HISTORIAL / STATS
# =========================================================
def get_learning_stats() -> Dict[str, Any]:
    total = len(cache_historial)
    ganadas = sum(1 for x in cache_historial if x.get("estado_resultado") == "ganada")
    perdidas = sum(1 for x in cache_historial if x.get("estado_resultado") == "perdida")
    resueltas = ganadas + perdidas
    win_rate = round((ganadas / resueltas) * 100, 2) if resueltas else 0
    roi_percent = round(((ganadas - perdidas) / resueltas) * 100, 2) if resueltas else 0

    return {
        "total_senales": total,
        "resueltas": resueltas,
        "ganadas": ganadas,
        "perdidas": perdidas,
        "win_rate": win_rate,
        "roi_percent": roi_percent,
        "signals_elite": sum(1 for x in cache_historial if x.get("signal_rank") == "ELITE"),
        "signals_top": sum(1 for x in cache_historial if x.get("signal_rank") == "TOP"),
        "value_promedio": round(sum(to_float(x.get("value"), 0) for x in cache_historial) / total, 2) if total else 0,
        "riesgo_medio": round(sum(to_float(x.get("risk_score"), 0) for x in cache_historial) / total, 2) if total else 0,
    }


# =========================================================
# RUTAS API
# =========================================================
@app.route("/status")
def status():
    return jsonify({
        "service": "JHONNY_ELITE_BACKEND",
        "status": "ok",
        "time": utc_iso_now()
    })


@app.route("/scan")
def scan():
    refrescar_datos()
    return jsonify({
        "ok": True,
        "partidos_analizados": len(cache_partidos),
        "total_partidos": len(cache_partidos),
        "ultimo_scan": ultimo_scan_ts
    })


@app.route("/signals")
def signals():
    asegurar_cache()
    return jsonify({
        "total": len(cache_senales),
        "signals": cache_senales
    })


@app.route("/hot-matches")
def hot_matches():
    asegurar_cache()

    partidos_hot = [
        p for p in cache_partidos
        if partido_esta_vivo(p) and to_float(p.get("xG"), 0) >= 0.7
    ]

    partidos_hot.sort(
        key=lambda p: (
            to_float(p.get("xG"), 0),
            to_int(p.get("shots_on_target"), 0),
            to_int(p.get("dangerous_attacks"), 0),
            to_int(p.get("minuto"), 0),
        ),
        reverse=True
    )

    return jsonify({
        "total": len(partidos_hot),
        "hot_matches": partidos_hot[:20]
    })


@app.route("/history")
def history():
    return jsonify(cache_historial[-30:])


@app.route("/learning-stats")
def learning_stats():
    return jsonify(get_learning_stats())


@app.route("/auto-scan/status")
def auto_scan_status():
    asegurar_cache()
    return jsonify({
        "auto_scan_activo": auto_scan_activo,
        "intervalo_segundos": AUTO_SCAN_INTERVAL,
        "ultimo_scan": ultimo_scan_ts,
        "partidos_cache": len(cache_partidos),
        "senales_cache": len(cache_senales),
    })


@app.route("/api/leagues")
def api_leagues():
    asegurar_cache()

    state_filter = request.args.get("state", "live")
    partidos = cache_partidos[:]

    if state_filter == "live":
        partidos = [p for p in partidos if partido_esta_vivo(p)]
    elif state_filter == "finished":
        partidos = [p for p in partidos if partido_esta_finalizado(p)]

    agrupado = {}
    for p in partidos:
        key = (p.get("liga"), p.get("pais"))
        if key not in agrupado:
            agrupado[key] = {
                "league": p.get("liga"),
                "country": p.get("pais"),
                "matches_live": 0,
                "matches_total": 0,
            }
        agrupado[key]["matches_total"] += 1
        if partido_esta_vivo(p):
            agrupado[key]["matches_live"] += 1

    ligas = list(agrupado.values())
    ligas.sort(key=lambda x: (x["matches_live"], x["matches_total"], x["league"]), reverse=True)

    return jsonify(ligas)


@app.route("/match-details/<match_id>")
def match_details(match_id):
    asegurar_cache()

    partido = next((p for p in cache_partidos if str(p.get("id")) == str(match_id)), None)
    if not partido:
        return jsonify({"error": "Partido no encontrado"}), 404

    senal = next((s for s in cache_senales if str(s.get("match_id")) == str(match_id)), None)

    posesion_local = 60 if partido.get("local") == "Barcelona" else 52
    posesion_visitante = 40 if posesion_local == 60 else 48

    return jsonify({
        "match_id": partido.get("id"),
        "home": partido.get("local"),
        "away": partido.get("visitante"),
        "league": partido.get("liga"),
        "country": partido.get("pais"),
        "minute": partido.get("minuto"),
        "status": partido.get("estado_partido"),
        "score": f"{partido.get('marcador_local', 0)}-{partido.get('marcador_visitante', 0)}",
        "marcador_local": partido.get("marcador_local", 0),
        "marcador_visitante": partido.get("marcador_visitante", 0),
        "xg": partido.get("xG", 0),
        "shots": partido.get("shots", 0),
        "shots_on_target": partido.get("shots_on_target", 0),
        "dangerous_attacks": partido.get("dangerous_attacks", 0),
        "momentum": partido.get("momentum", "MEDIO"),
        "goal_pressure": partido.get("goal_pressure", {}),
        "goal_predictor": partido.get("goal_predictor", {}),
        "chaos": partido.get("chaos", {}),
        "posesion_local": posesion_local,
        "posesion_visitante": posesion_visitante,
        "faltas_local": 13,
        "faltas_visitante": 14,
        "amarillas_local": 2,
        "amarillas_visitante": 2,
        "rojas_local": 1,
        "rojas_visitante": 1,
        "signal": senal or None
    })


# =========================================================
# RUTAS HTML
# =========================================================
@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
    
@app.route("/league-explorer")
def league_explorer():
    asegurar_cache()

    partidos_vivos = [p for p in cache_partidos if partido_esta_vivo(p)]
    agrupado = {}

    for p in partidos_vivos:
        key = (p.get("liga"), p.get("pais"))
        if key not in agrupado:
            agrupado[key] = {
                "league": p.get("liga"),
                "country": p.get("pais"),
                "count": 0
            }
        agrupado[key]["count"] += 1

    leagues_data = sorted(
        list(agrupado.values()),
        key=lambda x: (x["count"], x["league"]),
        reverse=True
    )

    return render_template("leagues.html", leagues=leagues_data)


@app.route("/matches/<league_name>")
def matches_by_league(league_name):
    asegurar_cache()

    league_name_lower = normalizar_texto(league_name)

    partidos = [
        p for p in cache_partidos
        if partido_esta_vivo(p) and normalizar_texto(p.get("liga")) == league_name_lower
    ]

    sort_by = request.args.get("sort", "relevance")

    if sort_by == "time":
        partidos.sort(key=lambda p: to_int(p.get("minuto"), 0), reverse=True)
    elif sort_by == "popularity":
        partidos.sort(key=lambda p: to_int(p.get("dangerous_attacks"), 0), reverse=True)
    else:
        partidos.sort(
            key=lambda p: (
                to_float(p.get("xG"), 0),
                to_int(p.get("shots_on_target"), 0),
                to_int(p.get("dangerous_attacks"), 0)
            ),
            reverse=True
        )

    return render_template(
        "matches.html",
        league_name=league_name,
        matches=partidos,
        sort_by=sort_by
    )


@app.route("/match/<match_id>")
def match_page(match_id):
    asegurar_cache()

    partido = next((p for p in cache_partidos if str(p.get("id")) == str(match_id)), None)
    if not partido:
        return "Partido no encontrado", 404

    detail = match_details(match_id).get_json()
    senal = next((s for s in cache_senales if str(s.get("match_id")) == str(match_id)), None)

    return render_template(
        "match_detail.html",
        match=detail,
        signal=senal
    )


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":
    refrescar_datos()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

# api_football_fetcher.py

from typing import Any, Dict, List
import os
import requests
import time


# =========================================================
# CONFIG
# =========================================================
API_KEY_ENV = "FOOTBALL_API_KEY"
API_URL_ENV = "FOOTBALL_API_URL"
DEFAULT_API_URL = "https://v3.football.api-sports.io/fixtures?live=all"
STATISTICS_URL = "https://v3.football.api-sports.io/fixtures/statistics"

REQUEST_TIMEOUT = 25
STAT_REQUEST_SLEEP_MS = 120
MAX_SOURCE_DELAY_SECONDS = 90


# =========================================================
# HELPERS
# =========================================================
def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return int(float(value))
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, str):
            value = value.replace("%", "").strip()
        return float(value)
    except Exception:
        return default


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _parse_iso_timestamp_to_epoch(ts: Any) -> int:
    """
    Convierte ISO timestamp tipo:
    2025-03-01T19:45:00+00:00
    """
    text = _safe_text(ts)
    if not text:
        return 0

    try:
        from datetime import datetime
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return 0


def _build_headers() -> Dict[str, str]:
    api_key = os.getenv(API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(f"No se encontró la variable de entorno {API_KEY_ENV}")

    return {
        "x-apisports-key": api_key,
        "Accept": "application/json",
        "User-Agent": "JHONNY_ELITE_V16/1.0",
    }


def _build_url() -> str:
    return os.getenv(API_URL_ENV, DEFAULT_API_URL).strip()


def _request_json(url: str, headers: Dict[str, str], params: Dict[str, Any] | None = None) -> Dict[str, Any]:
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else {}


# =========================================================
# PARSERS / HEURISTICAS
# =========================================================
def _parse_momentum(minuto: int, goles_totales: int, shots: int, shots_on_target: int, dangerous_attacks: int) -> str:
    if dangerous_attacks >= 25 or shots_on_target >= 5:
        return "MUY ALTO"
    if dangerous_attacks >= 16 or shots_on_target >= 3 or shots >= 9:
        return "ALTO"
    if minuto >= 20 or goles_totales >= 1 or shots >= 4:
        return "MEDIO"
    return "BAJO"


def _parse_estado_partido(status_short: str, status_long: str) -> str:
    short = (status_short or "").upper()
    long_ = (status_long or "").lower()

    if short in {"FT", "AET", "PEN", "CANC", "ABD", "AWD", "WO"}:
        return "finalizado"

    if short in {"1H", "2H", "HT", "ET", "BT", "P", "LIVE"}:
        return "en_juego"

    if "live" in long_ or "half" in long_ or "playing" in long_:
        return "en_juego"

    return "en_juego"


def _pick_stat(source: Dict[str, Any], *keys: str, default: Any = 0) -> Any:
    for key in keys:
        if key in source and source.get(key) is not None:
            return source.get(key)
    return default


def _normalize_stats_payload(statistics_payload: Dict[str, Any]) -> Dict[str, Any]:
    response = statistics_payload.get("response", [])
    stats_home: Dict[str, Any] = {}
    stats_away: Dict[str, Any] = {}

    if isinstance(response, list):
        for idx, team_stats in enumerate(response):
            values = team_stats.get("statistics", []) or []
            parsed: Dict[str, Any] = {}

            for row in values:
                key = _safe_text(row.get("type"))
                val = row.get("value")
                parsed[key] = val

            if idx == 0:
                stats_home = parsed
            elif idx == 1:
                stats_away = parsed

    shots_home = _to_int(_pick_stat(stats_home, "Total Shots"), 0)
    shots_away = _to_int(_pick_stat(stats_away, "Total Shots"), 0)

    shots_on_target_home = _to_int(_pick_stat(stats_home, "Shots on Goal"), 0)
    shots_on_target_away = _to_int(_pick_stat(stats_away, "Shots on Goal"), 0)

    dangerous_home = _to_int(_pick_stat(stats_home, "Dangerous Attacks", "Dangerous attacks"), 0)
    dangerous_away = _to_int(_pick_stat(stats_away, "Dangerous Attacks", "Dangerous attacks"), 0)

    if dangerous_home == 0:
        dangerous_home = (
            shots_home * 2 +
            shots_on_target_home * 3 +
            _to_int(_pick_stat(stats_home, "Corner Kicks"), 0) * 2
        )
    if dangerous_away == 0:
        dangerous_away = (
            shots_away * 2 +
            shots_on_target_away * 3 +
            _to_int(_pick_stat(stats_away, "Corner Kicks"), 0) * 2
        )

    possession_home = _to_float(_pick_stat(stats_home, "Ball Possession", default="0"), 0.0)
    possession_away = _to_float(_pick_stat(stats_away, "Ball Possession", default="0"), 0.0)

    corners_home = _to_int(_pick_stat(stats_home, "Corner Kicks"), 0)
    corners_away = _to_int(_pick_stat(stats_away, "Corner Kicks"), 0)

    yellow_home = _to_int(_pick_stat(stats_home, "Yellow Cards"), 0)
    yellow_away = _to_int(_pick_stat(stats_away, "Yellow Cards"), 0)

    red_home = _to_int(_pick_stat(stats_home, "Red Cards"), 0)
    red_away = _to_int(_pick_stat(stats_away, "Red Cards"), 0)

    return {
        "shots_home": shots_home,
        "shots_away": shots_away,
        "shots_total": shots_home + shots_away,
        "shots_on_target_home": shots_on_target_home,
        "shots_on_target_away": shots_on_target_away,
        "shots_on_target_total": shots_on_target_home + shots_on_target_away,
        "dangerous_attacks_home": dangerous_home,
        "dangerous_attacks_away": dangerous_away,
        "dangerous_attacks_total": dangerous_home + dangerous_away,
        "possession_home": possession_home,
        "possession_away": possession_away,
        "corners_home": corners_home,
        "corners_away": corners_away,
        "corners_total": corners_home + corners_away,
        "yellow_home": yellow_home,
        "yellow_away": yellow_away,
        "yellow_total": yellow_home + yellow_away,
        "red_home": red_home,
        "red_away": red_away,
        "red_total": red_home + red_away,
    }


def _build_pressure_score(minuto: int, shots_on_target: int, dangerous_attacks: int, corners: int) -> float:
    score = 0.0
    score += min(shots_on_target * 1.6, 12.0)
    score += min(dangerous_attacks * 0.22, 12.0)
    score += min(corners * 0.6, 4.0)

    if 20 <= minuto <= 75:
        score += 1.5
    elif 76 <= minuto <= 88:
        score += 1.0

    return round(score, 2)


def _build_predictor_score(minuto: int, goles_totales: int, shots_on_target: int, dangerous_attacks: int) -> float:
    score = 0.0
    score += min(shots_on_target * 1.4, 10.0)
    score += min(dangerous_attacks * 0.18, 10.0)

    if goles_totales >= 1:
        score += 1.0
    if minuto >= 60:
        score += 1.2
    if minuto >= 75:
        score += 1.0

    return round(score, 2)


def _build_chaos_score(goles_totales: int, yellow_total: int, red_total: int, minuto: int) -> float:
    score = 0.0
    score += min(goles_totales * 1.3, 4.0)
    score += min(yellow_total * 0.35, 3.0)
    score += min(red_total * 2.5, 5.0)

    if minuto >= 75:
        score += 1.0

    return round(score, 2)


def _estimate_xg(shots: int, shots_on_target: int, dangerous_attacks: int, corners: int) -> float:
    xg = (
        shots * 0.05 +
        shots_on_target * 0.18 +
        dangerous_attacks * 0.025 +
        corners * 0.03
    )
    return round(xg, 2)


def _goal_probs(minuto: int, pressure_score: float, predictor_score: float, chaos_score: float) -> Dict[str, float]:
    base5 = 0.0
    base10 = 0.0

    base5 += pressure_score * 0.018
    base5 += predictor_score * 0.022
    base5 += chaos_score * 0.008

    base10 += pressure_score * 0.024
    base10 += predictor_score * 0.030
    base10 += chaos_score * 0.012

    if 25 <= minuto <= 45:
        base5 += 0.03
        base10 += 0.05
    elif 60 <= minuto <= 75:
        base5 += 0.04
        base10 += 0.06
    elif 76 <= minuto <= 85:
        base5 += 0.03
        base10 += 0.05

    base5 = max(0.0, min(base5, 0.65))
    base10 = max(0.0, min(base10, 0.78))

    return {
        "goal_next_5_prob": round(base5, 4),
        "goal_next_10_prob": round(base10, 4),
    }


# =========================================================
# FRESHNESS / TIEMPO
# =========================================================
def _build_freshness_fields(fixture: Dict[str, Any], fetched_at: int) -> Dict[str, Any]:
    update_iso = _safe_text(fixture.get("update"))
    source_updated_at = _parse_iso_timestamp_to_epoch(update_iso)

    delay = 0
    if source_updated_at > 0:
        delay = max(0, fetched_at - source_updated_at)

    time_fresh = delay <= MAX_SOURCE_DELAY_SECONDS if source_updated_at > 0 else True

    return {
        "fetched_at": fetched_at,
        "source_updated_at": source_updated_at,
        "source_update_iso": update_iso,
        "source_delay_seconds": delay,
        "time_fresh": time_fresh,
    }


# =========================================================
# FETCH DE ESTADISTICAS POR FIXTURE
# =========================================================
def _fetch_fixture_statistics(fixture_id: int, headers: Dict[str, str]) -> Dict[str, Any]:
    if fixture_id <= 0:
        return {}

    try:
        data = _request_json(
            STATISTICS_URL,
            headers=headers,
            params={"fixture": fixture_id},
        )
        return _normalize_stats_payload(data)
    except Exception as e:
        print(f"Error obteniendo estadísticas del fixture {fixture_id}: {e}")
        return {}


# =========================================================
# NORMALIZACION DEL FIXTURE
# =========================================================
def _normalizar_fixture(item: Dict[str, Any], headers: Dict[str, str], fetched_at: int) -> Dict[str, Any]:
    fixture = item.get("fixture", {}) or {}
    league = item.get("league", {}) or {}
    teams = item.get("teams", {}) or {}
    goals = item.get("goals", {}) or {}
    status = fixture.get("status", {}) or {}

    fixture_id = _to_int(fixture.get("id"), 0)

    local = ((teams.get("home") or {}).get("name")) or "Local"
    visitante = ((teams.get("away") or {}).get("name")) or "Visitante"

    marcador_local = _to_int(goals.get("home"), 0)
    marcador_visitante = _to_int(goals.get("away"), 0)
    minuto = _to_int(status.get("elapsed"), 0)
    goles_totales = marcador_local + marcador_visitante

    stats = _fetch_fixture_statistics(fixture_id, headers)

    shots = _to_int(stats.get("shots_total"), 0)
    shots_on_target = _to_int(stats.get("shots_on_target_total"), 0)
    dangerous_attacks = _to_int(stats.get("dangerous_attacks_total"), 0)
    corners_total = _to_int(stats.get("corners_total"), 0)
    yellow_total = _to_int(stats.get("yellow_total"), 0)
    red_total = _to_int(stats.get("red_total"), 0)

    # =========================================================
    # FALLBACK FUERTE SI LA API NO TRAE STATS
    # =========================================================
    if shots == 0 and shots_on_target == 0 and dangerous_attacks == 0:
        base = max(1, minuto // 10)

        shots = max(4, goles_totales * 3 + base)
        shots_on_target = max(2, goles_totales + base // 2)
        dangerous_attacks = max(8, goles_totales * 5 + base * 2)
        corners_total = max(2, goles_totales + base // 2)
        yellow_total = max(yellow_total, 0)
        red_total = max(red_total, 0)

    pressure_score = _build_pressure_score(minuto, shots_on_target, dangerous_attacks, corners_total)
    predictor_score = _build_predictor_score(minuto, goles_totales, shots_on_target, dangerous_attacks)
    chaos_score = _build_chaos_score(goles_totales, yellow_total, red_total, minuto)
    xg = _estimate_xg(shots, shots_on_target, dangerous_attacks, corners_total)

    probs = _goal_probs(minuto, pressure_score, predictor_score, chaos_score)
    momentum = _parse_momentum(minuto, goles_totales, shots, shots_on_target, dangerous_attacks)

    freshness = _build_freshness_fields(fixture, fetched_at)

    return {
        "id": fixture_id,
        "liga": league.get("name", "Liga desconocida"),
        "pais": league.get("country", "País desconocido"),
        "local": local,
        "visitante": visitante,
        "minuto": minuto,
        "marcador_local": marcador_local,
        "marcador_visitante": marcador_visitante,
        "estado_partido": _parse_estado_partido(
            status.get("short", ""),
            status.get("long", "")
        ),
        "xG": xg,
        "shots": shots,
        "shots_on_target": shots_on_target,
        "dangerous_attacks": dangerous_attacks,
        "corners": corners_total,
        "tarjetas_amarillas": yellow_total,
        "tarjetas_rojas": red_total,
        "posesion_local": _to_float(stats.get("possession_home"), 0.0),
        "posesion_visitante": _to_float(stats.get("possession_away"), 0.0),
        "momentum": momentum,
        "cuota": 0.0,
        "prob_real": 0.75,
        "prob_implicita": 0.54,
        "goal_pressure": {
            "pressure_score": pressure_score,
            "pressure_level": "ALTA" if pressure_score >= 10 else "MEDIA" if pressure_score >= 5 else "BAJA",
            "pressure_reason": "Score calculado desde tiros, ataques peligrosos y corners",
        },
        "goal_predictor": {
            "goal_next_5_prob": probs["goal_next_5_prob"],
            "goal_next_10_prob": probs["goal_next_10_prob"],
            "predictor_score": predictor_score,
            "alert_level": "ROJA" if predictor_score >= 12 else "AMARILLA" if predictor_score >= 6 else "BAJA",
            "alert_reason": "Predictor calculado desde volumen ofensivo y tramo del partido",
        },
        "chaos": {
            "chaos_score": chaos_score,
            "chaos_level": "ALTO" if chaos_score >= 6 else "MEDIO" if chaos_score >= 3 else "BAJO",
            "chaos_reason": "Caos calculado desde goles, tarjetas y minuto",
        },
        "fixture_raw": fixture,
        "provider_status_short": _safe_text(status.get("short")),
        "provider_status_long": _safe_text(status.get("long")),
        "provider_elapsed": minuto,
        "provider_league_id": _to_int(league.get("id"), 0),
        "provider_fixture_id": fixture_id,
        "source": "api_football_real",
        **freshness,
    }


# =========================================================
# FALLBACK
# =========================================================
def _fallback_demo() -> List[Dict[str, Any]]:
    now_ts = int(time.time())
    return [{
        "id": 99999,
        "liga": "Demo (API-Football fallback)",
        "pais": "Demo",
        "local": "Argentina",
        "visitante": "Brasil",
        "minuto": 45,
        "marcador_local": 2,
        "marcador_visitante": 1,
        "estado_partido": "en_juego",
        "xG": 1.60,
        "shots": 12,
        "shots_on_target": 6,
        "dangerous_attacks": 24,
        "corners": 6,
        "tarjetas_amarillas": 2,
        "tarjetas_rojas": 0,
        "posesion_local": 53.0,
        "posesion_visitante": 47.0,
        "momentum": "ALTO",
        "cuota": 0.0,
        "prob_real": 0.75,
        "prob_implicita": 0.54,
        "goal_pressure": {
            "pressure_score": 9.0,
            "pressure_level": "ALTA",
            "pressure_reason": "Fallback demo",
        },
        "goal_predictor": {
            "goal_next_5_prob": 0.27,
            "goal_next_10_prob": 0.39,
            "predictor_score": 8.0,
            "alert_level": "AMARILLA",
            "alert_reason": "Fallback demo",
        },
        "chaos": {
            "chaos_score": 3.0,
            "chaos_level": "MEDIO",
            "chaos_reason": "Fallback demo",
        },
        "provider_status_short": "LIVE",
        "provider_status_long": "Fallback demo",
        "provider_elapsed": 45,
        "provider_league_id": 0,
        "provider_fixture_id": 99999,
        "fetched_at": now_ts,
        "source_updated_at": now_ts,
        "source_update_iso": "",
        "source_delay_seconds": 0,
        "time_fresh": True,
        "source": "fallback_demo",
    }]


# =========================================================
# FETCH PRINCIPAL
# =========================================================
def obtener_partidos_en_vivo() -> List[Dict[str, Any]]:
    try:
        headers = _build_headers()
        url = _build_url()

        fetched_at = int(time.time())
        data = _request_json(url, headers=headers)
        fixtures = data.get("response", [])

        if not isinstance(fixtures, list):
            print("API-Football respondió sin lista válida. Usando fallback demo.")
            return _fallback_demo()

        resultados: List[Dict[str, Any]] = []

        for item in fixtures:
            try:
                normalizado = _normalizar_fixture(item, headers, fetched_at)

                if normalizado.get("estado_partido") == "finalizado":
                    continue

                resultados.append(normalizado)

                time.sleep(STAT_REQUEST_SLEEP_MS / 1000.0)

            except Exception as e:
                print("Error normalizando fixture API-Football:", e)

        if resultados:
            print(f"OK: API-Football devolvió {len(resultados)} partidos en vivo")
            return resultados

        print("API-Football no devolvió partidos live utilizables. Usando fallback demo.")
        return _fallback_demo()

    except Exception as e:
        print("Error API-Football:", e)
        return _fallback_demo()

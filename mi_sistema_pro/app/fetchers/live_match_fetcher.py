import time
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from app.config.config import settings
from app.utils.helpers import safe_float, safe_int, safe_text


# =========================================================
# HELPERS DE RED
# =========================================================
def _build_headers() -> Dict[str, str]:
    api_key = safe_text(settings.FOOTBALL_API_KEY)
    if not api_key:
        raise RuntimeError("FOOTBALL_API_KEY no configurada")

    return {
        "x-apisports-key": api_key,
        "Accept": "application/json",
        "User-Agent": f"{settings.SYSTEM_NAME}/{settings.SYSTEM_VERSION}",
    }


def _request_json(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=settings.HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else {}


# =========================================================
# HELPERS DE PARSEO
# =========================================================
def _parse_estado_partido(status_short: str, status_long: str) -> str:
    short = safe_text(status_short).upper()
    long_ = safe_text(status_long).lower()

    if short in {"FT", "AET", "PEN", "CANC", "ABD", "AWD", "WO"}:
        return "finalizado"

    if short in {"1H", "2H", "HT", "ET", "BT", "P", "LIVE"}:
        return "en_juego"

    if "live" in long_ or "half" in long_ or "playing" in long_:
        return "en_juego"

    return "en_juego"


def _parse_momentum(
    minuto: int,
    goles_totales: int,
    shots: int,
    shots_on_target: int,
    dangerous_attacks: int,
) -> str:
    if dangerous_attacks >= 25 or shots_on_target >= 5:
        return "MUY ALTO"
    if dangerous_attacks >= 16 or shots_on_target >= 3 or shots >= 9:
        return "ALTO"
    if minuto >= 20 or goles_totales >= 1 or shots >= 4:
        return "MEDIO"
    return "BAJO"


def _estimate_xg(shots: int, shots_on_target: int, dangerous_attacks: int, corners: int) -> float:
    xg = (
        shots * 0.05 +
        shots_on_target * 0.18 +
        dangerous_attacks * 0.025 +
        corners * 0.03
    )
    return round(xg, 2)


def _pick_stat(source: Dict[str, Any], *keys: str, default: Any = 0) -> Any:
    for key in keys:
        if key in source and source.get(key) is not None:
            return source.get(key)
    return default


def _parse_iso_timestamp_to_epoch(ts: Any) -> int:
    text = safe_text(ts)
    if not text:
        return 0

    try:
        from datetime import datetime
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return int(dt.timestamp())
    except Exception:
        return 0


# =========================================================
# NORMALIZAR ESTADÍSTICAS
# =========================================================
def _normalize_stats_payload(statistics_payload: Dict[str, Any]) -> Dict[str, Any]:
    response = statistics_payload.get("response", [])
    stats_home: Dict[str, Any] = {}
    stats_away: Dict[str, Any] = {}

    if isinstance(response, list):
        for idx, team_stats in enumerate(response):
            values = team_stats.get("statistics", []) or []
            parsed: Dict[str, Any] = {}

            for row in values:
                key = safe_text(row.get("type"))
                parsed[key] = row.get("value")

            if idx == 0:
                stats_home = parsed
            elif idx == 1:
                stats_away = parsed

    shots_home = safe_int(_pick_stat(stats_home, "Total Shots"), 0)
    shots_away = safe_int(_pick_stat(stats_away, "Total Shots"), 0)

    shots_on_target_home = safe_int(_pick_stat(stats_home, "Shots on Goal"), 0)
    shots_on_target_away = safe_int(_pick_stat(stats_away, "Shots on Goal"), 0)

    dangerous_home = safe_int(_pick_stat(stats_home, "Dangerous Attacks", "Dangerous attacks"), 0)
    dangerous_away = safe_int(_pick_stat(stats_away, "Dangerous Attacks", "Dangerous attacks"), 0)

    corners_home = safe_int(_pick_stat(stats_home, "Corner Kicks"), 0)
    corners_away = safe_int(_pick_stat(stats_away, "Corner Kicks"), 0)

    yellow_home = safe_int(_pick_stat(stats_home, "Yellow Cards"), 0)
    yellow_away = safe_int(_pick_stat(stats_away, "Yellow Cards"), 0)

    red_home = safe_int(_pick_stat(stats_home, "Red Cards"), 0)
    red_away = safe_int(_pick_stat(stats_away, "Red Cards"), 0)

    possession_home = safe_float(_pick_stat(stats_home, "Ball Possession", default="0"), 0.0)
    possession_away = safe_float(_pick_stat(stats_away, "Ball Possession", default="0"), 0.0)

    # fallback si la API no trae dangerous attacks
    if dangerous_home == 0:
        dangerous_home = shots_home * 2 + shots_on_target_home * 3 + corners_home * 2
    if dangerous_away == 0:
        dangerous_away = shots_away * 2 + shots_on_target_away * 3 + corners_away * 2

    return {
        "shots_total": shots_home + shots_away,
        "shots_on_target_total": shots_on_target_home + shots_on_target_away,
        "dangerous_attacks_total": dangerous_home + dangerous_away,
        "corners_total": corners_home + corners_away,
        "yellow_total": yellow_home + yellow_away,
        "red_total": red_home + red_away,
        "possession_home": possession_home,
        "possession_away": possession_away,
    }


# =========================================================
# ESTADÍSTICAS POR FIXTURE
# =========================================================
def _fetch_fixture_statistics(fixture_id: int, headers: Dict[str, str]) -> Dict[str, Any]:
    if fixture_id <= 0:
        return {}

    try:
        data = _request_json(
            settings.FOOTBALL_STATISTICS_URL,
            headers=headers,
            params={"fixture": fixture_id},
        )
        return _normalize_stats_payload(data)
    except (Timeout, ConnectionError, HTTPError, RequestException, Exception) as e:
        print(f"[FETCHER] stats error fixture={fixture_id}: {e}")
        return {}


# =========================================================
# FRESHNESS
# =========================================================
def _build_freshness_fields(fixture: Dict[str, Any], fetched_at: int) -> Dict[str, Any]:
    update_iso = safe_text(fixture.get("update"))
    source_updated_at = _parse_iso_timestamp_to_epoch(update_iso)

    delay = 0
    if source_updated_at > 0:
        delay = max(0, fetched_at - source_updated_at)

    time_fresh = delay <= settings.MAX_SOURCE_DELAY_SECONDS if source_updated_at > 0 else True

    return {
        "fetched_at": fetched_at,
        "source_updated_at": source_updated_at,
        "source_update_iso": update_iso,
        "source_delay_seconds": delay,
        "time_fresh": time_fresh,
    }


# =========================================================
# NORMALIZACIÓN DEL PARTIDO
# =========================================================
def _normalize_fixture(item: Dict[str, Any], headers: Dict[str, str], fetched_at: int) -> Dict[str, Any]:
    fixture = item.get("fixture", {}) or {}
    league = item.get("league", {}) or {}
    teams = item.get("teams", {}) or {}
    goals = item.get("goals", {}) or {}
    status = fixture.get("status", {}) or {}

    fixture_id = safe_int(fixture.get("id"), 0)

    local = ((teams.get("home") or {}).get("name")) or "Local"
    visitante = ((teams.get("away") or {}).get("name")) or "Visitante"

    marcador_local = safe_int(goals.get("home"), 0)
    marcador_visitante = safe_int(goals.get("away"), 0)
    minuto = safe_int(status.get("elapsed"), 0)
    goles_totales = marcador_local + marcador_visitante

    stats = _fetch_fixture_statistics(fixture_id, headers)

    shots = safe_int(stats.get("shots_total"), 0)
    shots_on_target = safe_int(stats.get("shots_on_target_total"), 0)
    dangerous_attacks = safe_int(stats.get("dangerous_attacks_total"), 0)
    corners_total = safe_int(stats.get("corners_total"), 0)
    yellow_total = safe_int(stats.get("yellow_total"), 0)
    red_total = safe_int(stats.get("red_total"), 0)

    # fallback suave si stats vienen vacías
    if shots == 0 and shots_on_target == 0 and dangerous_attacks == 0:
        shots = max(0, goles_totales * 3 + (1 if minuto >= 25 else 0))
        shots_on_target = max(0, goles_totales + (1 if minuto >= 35 else 0))
        dangerous_attacks = max(0, goles_totales * 6 + (3 if minuto >= 30 else 0))
        corners_total = max(corners_total, goles_totales)

    xg = _estimate_xg(shots, shots_on_target, dangerous_attacks, corners_total)
    momentum = _parse_momentum(minuto, goles_totales, shots, shots_on_target, dangerous_attacks)
    freshness = _build_freshness_fields(fixture, fetched_at)

    pressure_score = round((shots_on_target * 1.4) + (dangerous_attacks * 0.18) + (corners_total * 0.5), 2)
    predictor_score = round((shots_on_target * 1.2) + (dangerous_attacks * 0.10), 2)
    chaos_score = round((goles_totales * 1.3) + (yellow_total * 0.25) + (red_total * 2.0), 2)

    return {
        "id": safe_text(fixture_id),
        "liga": safe_text(league.get("name"), "Liga desconocida"),
        "pais": safe_text(league.get("country"), "País desconocido"),
        "local": safe_text(local, "Local"),
        "visitante": safe_text(visitante, "Visitante"),
        "minuto": minuto,
        "marcador_local": marcador_local,
        "marcador_visitante": marcador_visitante,
        "estado_partido": _parse_estado_partido(status.get("short", ""), status.get("long", "")),
        "xG": xg,
        "shots": shots,
        "shots_on_target": shots_on_target,
        "dangerous_attacks": dangerous_attacks,
        "corners": corners_total,
        "tarjetas_amarillas": yellow_total,
        "tarjetas_rojas": red_total,
        "posesion_local": safe_float(stats.get("possession_home"), 0.0),
        "posesion_visitante": safe_float(stats.get("possession_away"), 0.0),
        "momentum": momentum,
        "cuota": settings.DEFAULT_ODD,
        "prob_real": settings.DEFAULT_PROB_REAL,
        "prob_implicita": settings.DEFAULT_PROB_IMPLICITA,
        "goal_pressure": {
            "pressure_score": pressure_score,
            "pressure_level": "ALTA" if pressure_score >= 10 else "MEDIA" if pressure_score >= 5 else "BAJA",
        },
        "goal_predictor": {
            "goal_next_5_prob": 0.12,
            "goal_next_10_prob": 0.22,
            "predictor_score": predictor_score,
        },
        "chaos": {
            "chaos_score": chaos_score,
            "chaos_level": "ALTO" if chaos_score >= 6 else "MEDIO" if chaos_score >= 3 else "BAJO",
        },
        "provider_fixture_id": fixture_id,
        "provider_status_short": safe_text(status.get("short")),
        "provider_status_long": safe_text(status.get("long")),
        "source": "api_football_real",
        **freshness,
    }


# =========================================================
# FALLBACK OPCIONAL
# =========================================================
def _fallback_demo() -> List[Dict[str, Any]]:
    now_ts = int(time.time())
    return [{
        "id": "99999",
        "liga": "Demo fallback",
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
        "cuota": settings.DEFAULT_ODD,
        "prob_real": settings.DEFAULT_PROB_REAL,
        "prob_implicita": settings.DEFAULT_PROB_IMPLICITA,
        "goal_pressure": {"pressure_score": 9.0, "pressure_level": "ALTA"},
        "goal_predictor": {
            "goal_next_5_prob": 0.27,
            "goal_next_10_prob": 0.39,
            "predictor_score": 8.0,
        },
        "chaos": {"chaos_score": 3.0, "chaos_level": "MEDIO"},
        "fetched_at": now_ts,
        "source_updated_at": now_ts,
        "source_update_iso": "",
        "source_delay_seconds": 0,
        "time_fresh": True,
        "source": "fallback_demo",
    }]


# =========================================================
# API PRINCIPAL
# =========================================================
def obtener_partidos_en_vivo() -> List[Dict[str, Any]]:
    try:
        headers = _build_headers()
        fetched_at = int(time.time())

        data = _request_json(settings.FOOTBALL_API_URL, headers=headers)
        fixtures = data.get("response", [])

        if not isinstance(fixtures, list):
            print("[FETCHER] response inválida")
            return _fallback_demo() if settings.USE_FALLBACK_IF_EMPTY else []

        resultados: List[Dict[str, Any]] = []

        for item in fixtures:
            try:
                normalizado = _normalize_fixture(item, headers, fetched_at)

                if safe_text(normalizado.get("estado_partido")).lower() == "finalizado":
                    continue

                resultados.append(normalizado)

                if settings.STAT_REQUEST_SLEEP_MS > 0:
                    time.sleep(settings.STAT_REQUEST_SLEEP_MS / 1000.0)

            except Exception as e:
                print(f"[FETCHER] fixture normalize error: {e}")
                continue

        if resultados:
            print(f"[FETCHER] partidos live: {len(resultados)}")
            return resultados

        print("[FETCHER] sin resultados live")
        return _fallback_demo() if settings.USE_FALLBACK_IF_EMPTY else []

    except Exception as e:
        print(f"[FETCHER] fetch general error: {e}")
        return _fallback_demo() if settings.USE_FALLBACK_IF_EMPTY else []

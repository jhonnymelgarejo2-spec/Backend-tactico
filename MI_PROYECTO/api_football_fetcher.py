import os
import requests
from typing import Any, Dict, List


DEFAULT_API_FOOTBALL_URL = "https://v3.football.api-sports.io/fixtures?live=all"
API_KEY_ENV = "FOOTBALL_API_KEY"
API_URL_ENV = "FOOTBALL_API_URL"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
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


def _build_headers() -> Dict[str, str]:
    api_key = os.getenv(API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(f"No se encontró la variable de entorno {API_KEY_ENV}")

    return {
        "x-apisports-key": api_key,
        "Accept": "application/json",
        "User-Agent": "JHONNY_ELITE_V16/1.0",
    }


def _get_api_url() -> str:
    return os.getenv(API_URL_ENV, DEFAULT_API_FOOTBALL_URL).strip()


def _parse_estado_partido(status_short: str, status_long: str) -> str:
    short = _safe_text(status_short).upper()
    long_ = _safe_text(status_long).lower()

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
    shots_total: int,
    shots_on_target_total: int,
    dangerous_attacks_total: int
) -> str:
    score = 0

    if goles_totales >= 1:
        score += 2
    if goles_totales >= 3:
        score += 2

    if minuto >= 20:
        score += 1
    if 25 <= minuto <= 75:
        score += 2
    elif 76 <= minuto <= 85:
        score += 1

    if shots_total >= 8:
        score += 2
    elif shots_total >= 5:
        score += 1

    if shots_on_target_total >= 3:
        score += 3
    elif shots_on_target_total >= 1:
        score += 1

    if dangerous_attacks_total >= 20:
        score += 3
    elif dangerous_attacks_total >= 12:
        score += 2
    elif dangerous_attacks_total >= 6:
        score += 1

    if score >= 9:
        return "MUY ALTO"
    if score >= 6:
        return "ALTO"
    if score >= 3:
        return "MEDIO"
    return "BAJO"


def _build_pressure_score(
    minuto: int,
    shots_on_target_total: int,
    dangerous_attacks_total: int,
    corners_total: int
) -> float:
    score = 0.0

    if minuto >= 20:
        score += 1.0
    if 25 <= minuto <= 75:
        score += 1.0
    if minuto >= 60:
        score += 0.8

    score += shots_on_target_total * 0.9
    score += dangerous_attacks_total * 0.08
    score += corners_total * 0.25

    return round(score, 2)


def _build_predictor_score(
    minuto: int,
    goles_totales: int,
    shots_total: int,
    shots_on_target_total: int,
    dangerous_attacks_total: int
) -> float:
    score = 0.0

    if minuto >= 20:
        score += 0.8
    if minuto >= 60:
        score += 1.0

    if goles_totales >= 1:
        score += 0.8
    if goles_totales >= 3:
        score += 1.2

    score += shots_total * 0.10
    score += shots_on_target_total * 0.75
    score += dangerous_attacks_total * 0.06

    return round(score, 2)


def _build_goal_probs(
    predictor_score: float,
    pressure_score: float,
    minuto: int
) -> Dict[str, float]:
    base = predictor_score + (pressure_score * 0.7)

    gp5 = min(max((base * 3.2) + (0.08 * minuto), 0), 85)
    gp10 = min(max((base * 4.3) + (0.10 * minuto), 0), 92)

    return {
        "goal_next_5_prob": round(gp5 / 100, 4),
        "goal_next_10_prob": round(gp10 / 100, 4),
    }


def _build_chaos_score(
    minuto: int,
    goles_totales: int,
    yellow_total: int,
    red_total: int
) -> float:
    score = 0.0

    if goles_totales >= 1:
        score += 1.0
    if goles_totales >= 3:
        score += 2.0

    if minuto >= 75:
        score += 1.2

    score += yellow_total * 0.20
    score += red_total * 1.8

    return round(score, 2)


def _build_xg_proxy(
    shots_total: int,
    shots_on_target_total: int,
    dangerous_attacks_total: int,
    goals_total: int
) -> float:
    xg = 0.0
    xg += shots_total * 0.06
    xg += shots_on_target_total * 0.18
    xg += dangerous_attacks_total * 0.025
    xg += goals_total * 0.15
    return round(xg, 2)


def _parse_statistics(item: Dict[str, Any]) -> Dict[str, Any]:
    stats_block = item.get("statistics") or []

    parsed = {
        "shots_home": 0,
        "shots_away": 0,
        "shots_on_target_home": 0,
        "shots_on_target_away": 0,
        "possession_home": 0,
        "possession_away": 0,
        "corners_home": 0,
        "corners_away": 0,
        "yellow_home": 0,
        "yellow_away": 0,
        "red_home": 0,
        "red_away": 0,
        "dangerous_attacks_home": 0,
        "dangerous_attacks_away": 0,
    }

    if not isinstance(stats_block, list):
        return parsed

    for team_stats in stats_block:
        team_info = team_stats.get("team", {}) or {}
        team_name = _safe_text(team_info.get("name"))
        values = team_stats.get("statistics", []) or []

        bucket = {}
        for row in values:
            typ = _safe_text(row.get("type"))
            val = row.get("value")
            bucket[typ] = val

        shots = _to_int(
            bucket.get("Total Shots", bucket.get("Shots Total", bucket.get("Shots on Goal", 0))),
            0
        )
        shots_on_target = _to_int(
            bucket.get("Shots on Goal", bucket.get("Shots on Target", 0)),
            0
        )
        possession = _to_int(bucket.get("Ball Possession", 0), 0)
        corners = _to_int(bucket.get("Corner Kicks", 0), 0)
        yellow = _to_int(bucket.get("Yellow Cards", 0), 0)
        red = _to_int(bucket.get("Red Cards", 0), 0)

        dangerous_attacks = _to_int(
            bucket.get("Dangerous Attacks", bucket.get("Attacks Dangerous", bucket.get("Attacks", 0))),
            0
        )

        if "home" not in parsed.get("team_name_home", "") and "away" not in parsed.get("team_name_away", ""):
            pass

        if not parsed.get("team_name_home"):
            parsed["team_name_home"] = team_name
            parsed["shots_home"] = shots
            parsed["shots_on_target_home"] = shots_on_target
            parsed["possession_home"] = possession
            parsed["corners_home"] = corners
            parsed["yellow_home"] = yellow
            parsed["red_home"] = red
            parsed["dangerous_attacks_home"] = dangerous_attacks
        else:
            parsed["team_name_away"] = team_name
            parsed["shots_away"] = shots
            parsed["shots_on_target_away"] = shots_on_target
            parsed["possession_away"] = possession
            parsed["corners_away"] = corners
            parsed["yellow_away"] = yellow
            parsed["red_away"] = red
            parsed["dangerous_attacks_away"] = dangerous_attacks

    return parsed


def _normalizar_fixture(item: Dict[str, Any]) -> Dict[str, Any]:
    fixture = item.get("fixture", {}) or {}
    league = item.get("league", {}) or {}
    teams = item.get("teams", {}) or {}
    goals = item.get("goals", {}) or {}
    status = fixture.get("status", {}) or {}

    local = _safe_text((teams.get("home") or {}).get("name"), "Local")
    visitante = _safe_text((teams.get("away") or {}).get("name"), "Visitante")

    marcador_local = _to_int(goals.get("home"), 0)
    marcador_visitante = _to_int(goals.get("away"), 0)
    minuto = _to_int(status.get("elapsed"), 0)
    goles_totales = marcador_local + marcador_visitante

    stats = _parse_statistics(item)

    shots_home = _to_int(stats.get("shots_home"), 0)
    shots_away = _to_int(stats.get("shots_away"), 0)
    shots_total = shots_home + shots_away

    shots_on_target_home = _to_int(stats.get("shots_on_target_home"), 0)
    shots_on_target_away = _to_int(stats.get("shots_on_target_away"), 0)
    shots_on_target_total = shots_on_target_home + shots_on_target_away

    dangerous_attacks_home = _to_int(stats.get("dangerous_attacks_home"), 0)
    dangerous_attacks_away = _to_int(stats.get("dangerous_attacks_away"), 0)
    dangerous_attacks_total = dangerous_attacks_home + dangerous_attacks_away

    corners_home = _to_int(stats.get("corners_home"), 0)
    corners_away = _to_int(stats.get("corners_away"), 0)
    corners_total = corners_home + corners_away

    yellow_home = _to_int(stats.get("yellow_home"), 0)
    yellow_away = _to_int(stats.get("yellow_away"), 0)
    yellow_total = yellow_home + yellow_away

    red_home = _to_int(stats.get("red_home"), 0)
    red_away = _to_int(stats.get("red_away"), 0)
    red_total = red_home + red_away

    possession_home = _to_int(stats.get("possession_home"), 0)
    possession_away = _to_int(stats.get("possession_away"), 0)

    pressure_score = _build_pressure_score(
        minuto=minuto,
        shots_on_target_total=shots_on_target_total,
        dangerous_attacks_total=dangerous_attacks_total,
        corners_total=corners_total,
    )

    predictor_score = _build_predictor_score(
        minuto=minuto,
        goles_totales=goles_totales,
        shots_total=shots_total,
        shots_on_target_total=shots_on_target_total,
        dangerous_attacks_total=dangerous_attacks_total,
    )

    goal_probs = _build_goal_probs(
        predictor_score=predictor_score,
        pressure_score=pressure_score,
        minuto=minuto,
    )

    chaos_score = _build_chaos_score(
        minuto=minuto,
        goles_totales=goles_totales,
        yellow_total=yellow_total,
        red_total=red_total,
    )

    xg_proxy = _build_xg_proxy(
        shots_total=shots_total,
        shots_on_target_total=shots_on_target_total,
        dangerous_attacks_total=dangerous_attacks_total,
        goals_total=goles_totales,
    )

    momentum = _parse_momentum(
        minuto=minuto,
        goles_totales=goles_totales,
        shots_total=shots_total,
        shots_on_target_total=shots_on_target_total,
        dangerous_attacks_total=dangerous_attacks_total,
    )

    return {
        "id": fixture.get("id", 0),
        "liga": _safe_text(league.get("name"), "Liga desconocida"),
        "pais": _safe_text(league.get("country"), "País desconocido"),
        "local": local,
        "visitante": visitante,
        "minuto": minuto,
        "marcador_local": marcador_local,
        "marcador_visitante": marcador_visitante,
        "estado_partido": _parse_estado_partido(
            status.get("short", ""),
            status.get("long", "")
        ),

        "xG": xg_proxy,
        "shots": shots_total,
        "shots_on_target": shots_on_target_total,
        "dangerous_attacks": dangerous_attacks_total,

        "possession_home": possession_home,
        "possession_away": possession_away,
        "corners_home": corners_home,
        "corners_away": corners_away,
        "yellow_cards_home": yellow_home,
        "yellow_cards_away": yellow_away,
        "red_cards_home": red_home,
        "red_cards_away": red_away,

        "momentum": momentum,
        "cuota": 1.85,
        "prob_real": 0.75,
        "prob_implicita": 0.54,

        "goal_pressure": {
            "pressure_score": pressure_score,
            "pressure_level": "ALTA" if pressure_score >= 5 else "MEDIA" if pressure_score >= 2.5 else "BAJA",
            "pressure_reason": "Score base generado desde ritmo, remates a puerta, corners y ataques peligrosos",
        },

        "goal_predictor": {
            "goal_next_5_prob": goal_probs["goal_next_5_prob"],
            "goal_next_10_prob": goal_probs["goal_next_10_prob"],
            "predictor_score": predictor_score,
            "alert_level": "ROJA" if predictor_score >= 6 else "AMARILLA" if predictor_score >= 3 else "BAJA",
            "alert_reason": "Predictor base generado desde minuto, goles, remates y ataques peligrosos",
        },

        "chaos": {
            "chaos_score": chaos_score,
            "chaos_level": "ALTO" if chaos_score >= 4 else "MEDIO" if chaos_score >= 2 else "BAJO",
            "chaos_reason": "Caos base generado desde goles, tarjetas y tramo del partido",
        },

        "fixture": fixture,
        "league_raw": league,
        "teams_raw": teams,
        "goals_raw": goals,
        "status_raw": status,
    }


def _fallback_demo() -> List[Dict[str, Any]]:
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
        "xG": 1.12,
        "shots": 11,
        "shots_on_target": 5,
        "dangerous_attacks": 18,
        "possession_home": 54,
        "possession_away": 46,
        "corners_home": 4,
        "corners_away": 3,
        "yellow_cards_home": 1,
        "yellow_cards_away": 2,
        "red_cards_home": 0,
        "red_cards_away": 0,
        "momentum": "ALTO",
        "cuota": 1.85,
        "prob_real": 0.75,
        "prob_implicita": 0.54,
        "goal_pressure": {
            "pressure_score": 4.3,
            "pressure_level": "MEDIA",
            "pressure_reason": "Fallback demo",
        },
        "goal_predictor": {
            "goal_next_5_prob": 0.27,
            "goal_next_10_prob": 0.39,
            "predictor_score": 3.8,
            "alert_level": "AMARILLA",
            "alert_reason": "Fallback demo",
        },
        "chaos": {
            "chaos_score": 2.4,
            "chaos_level": "MEDIO",
            "chaos_reason": "Fallback demo",
        },
    }]


def obtener_partidos_en_vivo() -> List[Dict[str, Any]]:
    try:
        headers = _build_headers()
        api_url = _get_api_url()

        response = requests.get(
            api_url,
            headers=headers,
            timeout=25,
        )
        response.raise_for_status()

        data = response.json()
        fixtures = data.get("response", [])

        if not isinstance(fixtures, list):
            print("API-Football respondió en formato no esperado. Usando fallback demo.")
            return _fallback_demo()

        resultados = []
        for item in fixtures:
            try:
                partido = _normalizar_fixture(item)
                if partido.get("estado_partido") != "finalizado":
                    resultados.append(partido)
            except Exception as e:
                print("Error normalizando fixture API-Football:", e)

        if resultados:
            print(f"OK: API-Football devolvió {len(resultados)} partidos en vivo")
            return resultados

        print("API-Football no devolvió partidos live. Usando fallback demo.")
        return _fallback_demo()

    except Exception as e:
        print("Error API-Football:", e)
        return _fallback_demo()

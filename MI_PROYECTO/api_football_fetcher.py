from typing import Any, Dict, List
import os
import requests


# =========================================================
# CONFIG
# =========================================================
API_KEY_ENV = "FOOTBALL_API_KEY"
API_URL_ENV = "FOOTBALL_API_URL"
DEFAULT_API_URL = "https://v3.football.api-sports.io/fixtures?live=all"


# =========================================================
# HELPERS
# =========================================================
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


def _build_url() -> str:
    return os.getenv(API_URL_ENV, DEFAULT_API_URL).strip()


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


def _extract_statistics(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    API-Football en /fixtures?live=all normalmente no trae estadísticas completas.
    Si no existen, dejamos base en 0 para que tu pipeline no reviente.
    """
    stats_home = {}
    stats_away = {}

    statistics = item.get("statistics", [])
    if isinstance(statistics, list):
        for team_stats in statistics:
            team = team_stats.get("team", {}) or {}
            team_name = _safe_text(team.get("name"))
            values = team_stats.get("statistics", []) or []

            parsed = {}
            for row in values:
                key = _safe_text(row.get("type"))
                val = row.get("value")
                parsed[key] = val

            if team_name:
                if not stats_home:
                    stats_home = parsed
                else:
                    stats_away = parsed

    def pick_stat(*keys, source=None, default=0):
        source = source or {}
        for key in keys:
            if key in source and source.get(key) is not None:
                return source.get(key)
        return default

    shots_home = _to_int(pick_stat("Total Shots", source=stats_home), 0)
    shots_away = _to_int(pick_stat("Total Shots", source=stats_away), 0)

    shots_on_target_home = _to_int(pick_stat("Shots on Goal", source=stats_home), 0)
    shots_on_target_away = _to_int(pick_stat("Shots on Goal", source=stats_away), 0)

    dangerous_home = _to_int(pick_stat("Dangerous Attacks", source=stats_home), 0)
    dangerous_away = _to_int(pick_stat("Dangerous Attacks", source=stats_away), 0)

    possession_home = _to_float(str(pick_stat("Ball Possession", source=stats_home, default="0")).replace("%", ""), 0.0)
    possession_away = _to_float(str(pick_stat("Ball Possession", source=stats_away, default="0")).replace("%", ""), 0.0)

    corners_home = _to_int(pick_stat("Corner Kicks", source=stats_home), 0)
    corners_away = _to_int(pick_stat("Corner Kicks", source=stats_away), 0)

    yellow_home = _to_int(pick_stat("Yellow Cards", source=stats_home), 0)
    yellow_away = _to_int(pick_stat("Yellow Cards", source=stats_away), 0)

    red_home = _to_int(pick_stat("Red Cards", source=stats_home), 0)
    red_away = _to_int(pick_stat("Red Cards", source=stats_away), 0)

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
    base10 += predictor_score * 0.03
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


def _normalizar_fixture(item: Dict[str, Any]) -> Dict[str, Any]:
    fixture = item.get("fixture", {}) or {}
    league = item.get("league", {}) or {}
    teams = item.get("teams", {}) or {}
    goals = item.get("goals", {}) or {}
    status = fixture.get("status", {}) or {}

    local = ((teams.get("home") or {}).get("name")) or "Local"
    visitante = ((teams.get("away") or {}).get("name")) or "Visitante"

    marcador_local = _to_int(goals.get("home"), 0)
    marcador_visitante = _to_int(goals.get("away"), 0)
    minuto = _to_int(status.get("elapsed"), 0)
    goles_totales = marcador_local + marcador_visitante

    stats = _extract_statistics(item)

    shots = stats["shots_total"]
    shots_on_target = stats["shots_on_target_total"]
    dangerous_attacks = stats["dangerous_attacks_total"]
    corners_total = stats["corners_total"]
    yellow_total = stats["yellow_total"]
    red_total = stats["red_total"]

    pressure_score = _build_pressure_score(minuto, shots_on_target, dangerous_attacks, corners_total)
    predictor_score = _build_predictor_score(minuto, goles_totales, shots_on_target, dangerous_attacks)
    chaos_score = _build_chaos_score(goles_totales, yellow_total, red_total, minuto)
    xg = _estimate_xg(shots, shots_on_target, dangerous_attacks, corners_total)

    probs = _goal_probs(minuto, pressure_score, predictor_score, chaos_score)
    momentum = _parse_momentum(minuto, goles_totales, shots, shots_on_target, dangerous_attacks)

    return {
        "id": fixture.get("id", 0),
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
        "posesion_local": stats["possession_home"],
        "posesion_visitante": stats["possession_away"],
        "momentum": momentum,
        "cuota": 1.85,
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
        "source": "api_football_real",
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
        "xG": 1.6,
        "shots": 12,
        "shots_on_target": 6,
        "dangerous_attacks": 24,
        "corners": 6,
        "tarjetas_amarillas": 2,
        "tarjetas_rojas": 0,
        "posesion_local": 53.0,
        "posesion_visitante": 47.0,
        "momentum": "ALTO",
        "cuota": 1.85,
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
        "source": "fallback_demo",
    }]


# =========================================================
# FETCH PRINCIPAL
# =========================================================
def obtener_partidos_en_vivo() -> List[Dict[str, Any]]:
    try:
        headers = _build_headers()
        url = _build_url()

        response = requests.get(
            url,
            headers=headers,
            timeout=25,
        )
        response.raise_for_status()

        data = response.json()
        fixtures = data.get("response", [])

        if not isinstance(fixtures, list):
            print("API-Football respondió sin lista válida. Usando fallback demo.")
            return _fallback_demo()

        resultados = []
        for item in fixtures:
            try:
                normalizado = _normalizar_fixture(item)

                if normalizado.get("estado_partido") == "finalizado":
                    continue

                resultados.append(normalizado)
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

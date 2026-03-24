import os
import requests
from typing import Any, Dict, List


DEFAULT_API_FOOTBALL_URL = "https://v3.football.api-sports.io/fixtures"
API_KEY_ENV = "FOOTBALL_API_KEY"
API_URL_ENV = "FOOTBALL_API_URL"


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _build_headers() -> Dict[str, str]:
    api_key = os.getenv(API_KEY_ENV, "").strip()
    if not api_key:
        raise RuntimeError(
            f"No se encontró la variable de entorno {API_KEY_ENV}"
        )

    return {
        "x-apisports-key": api_key,
        "Accept": "application/json",
        "User-Agent": "JHONNY_ELITE_V16/1.0",
    }


def _get_api_url() -> str:
    return os.getenv(API_URL_ENV, DEFAULT_API_FOOTBALL_URL).strip()


def _parse_momentum(minuto: int, goles_totales: int) -> str:
    if minuto >= 75 and goles_totales >= 2:
        return "ALTO"
    if 30 <= minuto <= 75 and goles_totales >= 1:
        return "MEDIO"
    if minuto < 30 and goles_totales == 0:
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

    momentum = _parse_momentum(minuto, goles_totales)

    pressure_score = 0.0
    predictor_score = 0.0
    chaos_score = 0.0

    if minuto >= 20:
        pressure_score += 1.5
        predictor_score += 1.0

    if goles_totales >= 1:
        chaos_score += 1.0
        predictor_score += 0.8

    if minuto >= 60:
        pressure_score += 1.2

    if minuto >= 75:
        chaos_score += 1.5
        predictor_score += 1.2

    if goles_totales >= 3:
        chaos_score += 2.0

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
        "xG": 0.0,
        "shots": 0,
        "shots_on_target": 0,
        "dangerous_attacks": 0,
        "momentum": momentum,
        "cuota": 1.85,
        "prob_real": 0.75,
        "prob_implicita": 0.54,
        "goal_pressure": {
            "pressure_score": round(pressure_score, 2),
            "pressure_level": "MEDIA" if pressure_score >= 2 else "BAJA",
            "pressure_reason": "Score base generado desde minuto y contexto del partido",
        },
        "goal_predictor": {
            "goal_next_5_prob": 0.0,
            "goal_next_10_prob": 0.0,
            "predictor_score": round(predictor_score, 2),
            "alert_level": "AMARILLA" if predictor_score >= 2 else "BAJA",
            "alert_reason": "Predictor base generado desde estado live",
        },
        "chaos": {
            "chaos_score": round(chaos_score, 2),
            "chaos_level": "MEDIO" if chaos_score >= 2 else "BAJO",
            "chaos_reason": "Caos base generado desde goles y tramo del partido",
        },
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
        "xG": 0.0,
        "shots": 0,
        "shots_on_target": 0,
        "dangerous_attacks": 0,
        "momentum": "MEDIO",
        "cuota": 1.85,
        "prob_real": 0.75,
        "prob_implicita": 0.54,
        "goal_pressure": {
            "pressure_score": 2.0,
            "pressure_level": "BAJA",
            "pressure_reason": "Fallback demo",
        },
        "goal_predictor": {
            "goal_next_5_prob": 0.0,
            "goal_next_10_prob": 0.0,
            "predictor_score": 1.5,
            "alert_level": "BAJA",
            "alert_reason": "Fallback demo",
        },
        "chaos": {
            "chaos_score": 1.0,
            "chaos_level": "BAJO",
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
                resultados.append(_normalizar_fixture(item))
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

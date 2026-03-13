import requests
from typing import List, Dict, Any

URLS_POSIBLES = [
    "https://www.sofascore.com/api/v1/sport/football/events/live",
    "https://api.sofascore.com/api/v1/sport/football/events/live",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Connection": "keep-alive",
}


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _parse_minute(event: Dict) -> int:
    status = event.get("status", {}) or {}
    time_data = event.get("time", {}) or {}

    posibles = [
        time_data.get("currentPeriodStartMinute"),
        time_data.get("currentPeriodStartTimestamp"),
        status.get("description"),
    ]

    for item in posibles:
        if isinstance(item, int):
            if 0 <= item <= 130:
                return item
        if isinstance(item, str):
            numeros = "".join(ch for ch in item if ch.isdigit())
            if numeros:
                minuto = _to_int(numeros, 0)
                if 0 <= minuto <= 130:
                    return minuto

    return 0


def _parse_score(event: Dict) -> tuple[int, int]:
    home_score = event.get("homeScore", {}) or {}
    away_score = event.get("awayScore", {}) or {}

    local = _to_int(
        home_score.get("current", home_score.get("display", 0)),
        0
    )
    visitante = _to_int(
        away_score.get("current", away_score.get("display", 0)),
        0
    )

    return local, visitante


def _parse_estado(event: Dict) -> str:
    status = event.get("status", {}) or {}
    return (
        status.get("type")
        or status.get("description")
        or "en_juego"
    )


def _normalizar_evento(match: Dict) -> Dict:
    marcador_local, marcador_visitante = _parse_score(match)

    torneo = (
        ((match.get("tournament") or {}).get("name"))
        or ((match.get("uniqueTournament") or {}).get("name"))
        or "Liga desconocida"
    )

    pais = (
        (((match.get("tournament") or {}).get("category") or {}).get("name"))
        or (((match.get("uniqueTournament") or {}).get("category") or {}).get("name"))
        or "País desconocido"
    )

    local = ((match.get("homeTeam") or {}).get("name")) or "Local"
    visitante = ((match.get("awayTeam") or {}).get("name")) or "Visitante"

    minuto = _parse_minute(match)
    estado = _parse_estado(match)

    # Valores base para que el sistema táctico no se rompa
    goal_next_5 = 0.0
    goal_next_10 = 0.0
    predictor_score = 0.0
    alert_level = "BAJA"
    alert_reason = "Sin datos de predictor"

    pressure_score = 0.0
    pressure_level = "BAJA"
    pressure_reason = "Sin datos de presión"

    chaos_score = 0.0
    chaos_level = "BAJO"
    chaos_reason = "Sin datos de caos"

    return {
        "id": match.get("id", 0),
        "liga": torneo,
        "pais": pais,
        "local": local,
        "visitante": visitante,
        "minuto": minuto,
        "marcador_local": marcador_local,
        "marcador_visitante": marcador_visitante,
        "estado_partido": estado,
        "xG": 0.0,
        "momentum": "MEDIO",
        "cuota": 1.85,
        "prob_real": 0.75,
        "prob_implicita": 0.54,
        "goal_pressure": {
            "pressure_score": pressure_score,
            "pressure_level": pressure_level,
            "pressure_reason": pressure_reason,
        },
        "goal_predictor": {
            "goal_next_5_prob": goal_next_5,
            "goal_next_10_prob": goal_next_10,
            "predictor_score": predictor_score,
            "alert_level": alert_level,
            "alert_reason": alert_reason,
        },
        "chaos": {
            "chaos_score": chaos_score,
            "chaos_level": chaos_level,
            "chaos_reason": chaos_reason,
        },
    }


def _fetch_desde_url(url: str) -> List[Dict]:
    response = requests.get(url, headers=HEADERS, timeout=20)

    if response.status_code == 403:
        raise RuntimeError(f"403 bloqueado en {url}")

    response.raise_for_status()
    data = response.json()

    eventos = data.get("events", [])
    if not isinstance(eventos, list):
        return []

    resultados = []
    for event in eventos:
        try:
            resultados.append(_normalizar_evento(event))
        except Exception as e:
            print("Error normalizando evento:", e)

    return resultados


def obtener_partidos_en_vivo() -> List[Dict]:
    errores = []

    for url in URLS_POSIBLES:
        try:
            partidos = _fetch_desde_url(url)
            if partidos:
                print(f"OK: partidos reales obtenidos desde {url}")
                return partidos

            print(f"Sin partidos en {url}")
        except Exception as e:
            msg = f"{url} -> {str(e)}"
            errores.append(msg)
            print("Error endpoint:", msg)

    print("No se pudo obtener datos reales. Errores:")
    for err in errores:
        print(" -", err)

    # Fallback demo para no romper el sistema
    return [{
        "id": 99999,
        "liga": "Demo (Sofascore bloqueado)",
        "pais": "Demo",
        "local": "Argentina",
        "visitante": "Brasil",
        "minuto": 45,
        "marcador_local": 2,
        "marcador_visitante": 1,
        "estado_partido": "en_juego",
        "xG": 0.0,
        "momentum": "MEDIO",
        "cuota": 1.85,
        "prob_real": 0.75,
        "prob_implicita": 0.54,
        "goal_pressure": {
            "pressure_score": 0.0,
            "pressure_level": "BAJA",
            "pressure_reason": "Fallback demo",
        },
        "goal_predictor": {
            "goal_next_5_prob": 0.0,
            "goal_next_10_prob": 0.0,
            "predictor_score": 0.0,
            "alert_level": "BAJA",
            "alert_reason": "Fallback demo",
        },
        "chaos": {
            "chaos_score": 0.0,
            "chaos_level": "BAJO",
            "chaos_reason": "Fallback demo",
        },
    }]

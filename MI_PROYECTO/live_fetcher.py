import os
import requests


def obtener_partidos_en_vivo():
    api_key = os.environ.get("FOOTBALL_API_KEY", "").strip()
    api_url = os.environ.get(
        "FOOTBALL_API_URL",
        "https://v3.football.api-sports.io/fixtures?live=all"
    ).strip()

    if not api_key:
        print("LIVE_FETCHER -> No existe FOOTBALL_API_KEY")
        return []

    headers = {
        "x-apisports-key": api_key
    }

    try:
        r = requests.get(api_url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"LIVE_FETCHER ERROR -> {e}")
        return []

    response = data.get("response", [])
    partidos = []

    for item in response:
        fixture = item.get("fixture", {}) or {}
        league = item.get("league", {}) or {}
        teams = item.get("teams", {}) or {}
        goals = item.get("goals", {}) or {}

        partido = {
            "id": fixture.get("id"),
            "local": (teams.get("home") or {}).get("name", "Local"),
            "visitante": (teams.get("away") or {}).get("name", "Visitante"),
            "liga": league.get("name", "Liga desconocida"),
            "pais": league.get("country", "World"),
            "estado_partido": ((fixture.get("status") or {}).get("short") or "LIVE"),
            "minuto": (fixture.get("status") or {}).get("elapsed", 0),
            "marcador_local": goals.get("home", 0),
            "marcador_visitante": goals.get("away", 0),
            "shots": 0,
            "shots_on_target": 0,
            "dangerous_attacks": 0,
            "xG": 0.0,
            "momentum": "MEDIO",
            "goal_pressure": {"pressure_score": 0},
            "goal_predictor": {"predictor_score": 0},
            "chaos": {"chaos_score": 0},
            "live": True,
            "fixture": fixture
        }

        partidos.append(partido)

    print(f"LIVE_FETCHER -> partidos reales encontrados: {len(partidos)}")
    return partidos

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
        stats = item.get("statistics", []) or []

        home_stats = {}
        away_stats = {}

        if len(stats) >= 2:
            home_stats = _stats_to_dict(stats[0].get("statistics", []))
            away_stats = _stats_to_dict(stats[1].get("statistics", []))

        shots_on_target = _safe_int(home_stats.get("Shots on Goal")) + _safe_int(away_stats.get("Shots on Goal"))
        shots_total = _safe_int(home_stats.get("Total Shots")) + _safe_int(away_stats.get("Total Shots"))
        dangerous_attacks = _safe_int(home_stats.get("Dangerous Attacks")) + _safe_int(away_stats.get("Dangerous Attacks"))

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
            "shots": shots_total,
            "shots_on_target": shots_on_target,
            "dangerous_attacks": dangerous_attacks,
            "xG": _estimar_xg(shots_on_target, shots_total, dangerous_attacks),
            "momentum": _calcular_momentum(shots_on_target, dangerous_attacks),
            "goal_pressure": {
                "pressure_score": _calcular_pressure_score(shots_on_target, dangerous_attacks)
            },
            "goal_predictor": {
                "predictor_score": _calcular_predictor_score(shots_total, shots_on_target)
            },
            "chaos": {
                "chaos_score": _calcular_chaos_score(shots_total, dangerous_attacks)
            },
            "live": True,
            "fixture": fixture
        }

        partidos.append(partido)

    print(f"LIVE_FETCHER -> partidos reales encontrados: {len(partidos)}")
    return partidos


def _stats_to_dict(stats_list):
    resultado = {}
    for x in stats_list:
        tipo = x.get("type")
        valor = x.get("value")
        if tipo:
            resultado[tipo] = valor
    return resultado


def _safe_int(v):
    try:
        if v is None:
            return 0
        if isinstance(v, str):
            v = v.replace("%", "").strip()
        return int(float(v))
    except Exception:
        return 0


def _estimar_xg(shots_on_target, shots_total, dangerous_attacks):
    xg = (shots_on_target * 0.22) + (shots_total * 0.04) + (dangerous_attacks * 0.015)
    return round(xg, 2)


def _calcular_momentum(shots_on_target, dangerous_attacks):
    score = shots_on_target * 2 + dangerous_attacks * 0.4
    if score >= 22:
        return "MUY ALTO"
    if score >= 15:
        return "ALTO"
    if score >= 8:
        return "MEDIO"
    return "BAJO"


def _calcular_pressure_score(shots_on_target, dangerous_attacks):
    return round((shots_on_target * 1.8) + (dangerous_attacks * 0.15), 2)


def _calcular_predictor_score(shots_total, shots_on_target):
    return round((shots_total * 0.45) + (shots_on_target * 1.4), 2)


def _calcular_chaos_score(shots_total, dangerous_attacks):
    return round((shots_total * 0.12) + (dangerous_attacks * 0.06), 2)

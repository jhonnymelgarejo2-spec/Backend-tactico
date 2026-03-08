# providers.py
import os
import random
import requests

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")


def obtener_partidos_api():
    url = f"https://{API_HOST}/fixtures?live=all"
    headers = {
        "x-apisports-key": API_KEY
    }

    try:
        r = requests.get(url, headers=headers, timeout=12)
        r.raise_for_status()
        data = r.json()

        partidos = []

        for m in data.get("response", []):
            fixture = m.get("fixture", {})
            league = m.get("league", {})
            teams = m.get("teams", {})
            goals = m.get("goals", {})

            home = teams.get("home", {}) or {}
            away = teams.get("away", {}) or {}

            minuto = fixture.get("status", {}).get("elapsed")
            if minuto is None:
                minuto = 0

            marcador_local = goals.get("home")
            marcador_visitante = goals.get("away")

            partidos.append({
                "id": fixture.get("id"),
                "pais": league.get("country", "Desconocido"),
                "liga": league.get("name", "Desconocida"),

                "local": home.get("name", "Local"),
                "visitante": away.get("name", "Visitante"),

                "home_logo": home.get("logo"),
                "away_logo": away.get("logo"),

                "minuto": int(minuto or 0),
                "marcador_local": int(marcador_local or 0),
                "marcador_visitante": int(marcador_visitante or 0),

                "xG": round(random.uniform(0.5, 3.0), 2),
                "momentum": random.choice(["BAJO", "MEDIO", "ALTO", "MUY ALTO"]),
                "prob_real": round(random.uniform(0.45, 0.75), 2),
                "prob_implicita": round(random.uniform(0.40, 0.70), 2),
                "cuota": round(random.uniform(1.5, 3.2), 2)
            })

        if partidos:
            return partidos

        print("⚠️ API-Football no devolvió partidos live, usando DEMO")
        return obtener_partidos_demo()

    except Exception as e:
        print(f"⚠️ Error obteniendo partidos API-Football: {e}")
        return obtener_partidos_demo()


def obtener_partidos_demo():
    equipos = [
        "Real Madrid", "Barcelona", "Bayern", "PSG", "Liverpool",
        "Manchester City", "Inter", "Milan", "Ajax", "Porto",
        "Benfica", "Flamengo", "Palmeiras", "River Plate", "Boca Juniors"
    ]

    ligas = [
        "Premier League",
        "LaLiga",
        "Serie A",
        "Bundesliga",
        "Ligue 1"
    ]

    momentum_posible = ["BAJO", "MEDIO", "ALTO", "MUY ALTO"]
    partidos = []

    for i in range(60):
        local = random.choice(equipos)
        visitante = random.choice(equipos)

        while local == visitante:
            visitante = random.choice(equipos)

        minuto = random.randint(1, 90)
        prob_real = round(random.uniform(0.45, 0.75), 2)
        prob_implicita = round(random.uniform(0.40, 0.70), 2)

        partidos.append({
            "id": f"DEMO-{10000+i}",
            "pais": "Demo",
            "liga": random.choice(ligas),

            "local": local,
            "visitante": visitante,

            "minuto": minuto,
            "marcador_local": random.randint(0, 3),
            "marcador_visitante": random.randint(0, 3),

            "xG": round(random.uniform(0.1, 3.5), 2),
            "momentum": random.choice(momentum_posible),
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "cuota": round(random.uniform(1.5, 3.2), 2),

            "home_logo": None,
            "away_logo": None,
        })

    return partidos


def obtener_partidos():
    if API_KEY:
        return obtener_partidos_api()
    return obtener_partidos_demo()

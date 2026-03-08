# providers.py
import random
import os
import requests


API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = os.getenv("API_FOOTBALL_HOST")


def obtener_partidos_api():
    """
    Obtiene partidos reales desde API-Football
    """

    url = f"https://{API_HOST}/fixtures?live=all"

    headers = {
        "x-apisports-key": API_KEY
    }

    try:

        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()

        partidos = []

        for m in data["response"]:

            partidos.append({
                "id": m["fixture"]["id"],

                "pais": m["league"]["country"],
                "liga": m["league"]["name"],

                "local": m["teams"]["home"]["name"],
                "visitante": m["teams"]["away"]["name"],

                "home_logo": m["teams"]["home"]["logo"],
                "away_logo": m["teams"]["away"]["logo"],

                "minuto": m["fixture"]["status"]["elapsed"],

                "marcador_local": m["goals"]["home"],
                "marcador_visitante": m["goals"]["away"],

                # datos simulados mientras agregamos stats reales
                "xG": round(random.uniform(0.5,3.0),2),
                "momentum": random.choice(["BAJO","MEDIO","ALTO","MUY ALTO"]),
                "prob_real": round(random.uniform(0.45,0.75),2),
                "prob_implicita": round(random.uniform(0.40,0.70),2),
                "cuota": round(random.uniform(1.5,3.2),2)
            })

        return partidos

    except Exception as e:
        print("Error API Football:", e)
        return obtener_partidos_demo()


def obtener_partidos_demo():
    """
    Genera partidos DEMO si la API falla
    """

    equipos = [
        "Real Madrid","Barcelona","Bayern","PSG","Liverpool",
        "Manchester City","Inter","Milan","Ajax","Porto",
        "Benfica","Flamengo","Palmeiras","River Plate","Boca Juniors"
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

        if local == visitante:
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

            "marcador_local": random.randint(0,3),
            "marcador_visitante": random.randint(0,3),

            "xG": round(random.uniform(0.1,3.5),2),

            "momentum": random.choice(momentum_posible),
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "cuota": round(random.uniform(1.5, 3.2), 2)
        })

    return partidos


def obtener_partidos():
    """
    Decide si usar API o DEMO
    """

    if API_KEY and API_HOST:
        return obtener_partidos_api()

    return obtener_partidos_demo()

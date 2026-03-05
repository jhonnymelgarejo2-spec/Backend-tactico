# providers.py
import random

def obtener_partidos_demo():
    """
    Genera partidos falsos para pruebas
    mientras no tengamos API real.
    """

    equipos = [
        "Real Madrid","Barcelona","Bayern","PSG","Liverpool",
        "Manchester City","Inter","Milan","Ajax","Porto",
        "Benfica","Flamengo","Palmeiras","River","Boca"
    ]

    ligas = [
        "Premier League",
        "LaLiga",
        "Serie A",
        "Bundesliga",
        "Ligue 1"
    ]

    partidos = []

    for i in range(60):

        local = random.choice(equipos)
        visitante = random.choice(equipos)

        partidos.append({
            "id": 10000 + i,
            "pais": "Demo",
            "liga": random.choice(ligas),
            "local": local,
            "visitante": visitante,
            "minuto": random.randint(1,90),
            "marcador_local": random.randint(0,3),
            "marcador_visitante": random.randint(0,3),
            "xG": round(random.uniform(0.1,3.5),2)
        })

    return partidos

# providers.py
import random

def obtener_partidos_demo():
    """
    Genera partidos DEMO para probar el sistema
    mientras no usamos API real.
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
            "id": f"UEFA-{10000+i}",
            "pais": "Demo",
            "liga": random.choice(ligas),

            "local": local,
            "visitante": visitante,

            "minuto": minuto,

            "marcador_local": random.randint(0,3),
            "marcador_visitante": random.randint(0,3),

            "xG": round(random.uniform(0.1,3.5),2),

            # nuevos datos para el motor
            "momentum": random.choice(momentum_posible),
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "cuota": round(random.uniform(1.5, 3.2), 2)
        })

    return partidos

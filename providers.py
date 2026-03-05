# providers.py
from typing import List, Dict
import random

def obtener_partidos_demo() -> List[Dict]:
    """
    ✅ Partidos demo (mientras no pagas APIs)
    """
    ligas = [
        "Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1",
        "Brasileirão", "Primera División", "MLS"
    ]
    equipos = ["Real Madrid", "Barcelona", "Inter", "Milan", "Ajax", "PSG", "Bayern", "Liverpool", "City", "Boca"]

    partidos = []
    for i in range(1, 120):  # genera 119 y luego filtramos a 60
        local = random.choice(equipos)
        visitante = random.choice([e for e in equipos if e != local])
        minuto = random.randint(1, 90)

        partidos.append({
            "id": str(100000 + i),
            "liga": random.choice(ligas),
            "local": local,
            "visitante": visitante,
            "minuto": minuto,
            "marcador_local": random.randint(0, 3),
            "marcador_visitante": random.randint(0, 3),
        })

    return partidos

# providers.py
from __future__ import annotations
from typing import List, Dict, Any
import random

class MockProvider:
    """
    Provider de prueba (gratis).
    Devuelve partidos 'fake' para que el sistema funcione sin pagar APIs.
    """

    def get_live_matches(self, limit: int = 60) -> List[Dict[str, Any]]:
        ligas = [
            "Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1",
            "Primeira Liga", "Eredivisie", "Brasileirão", "Primera División", "MLS"
        ]
        equipos = ["Barcelona", "Real Madrid", "PSG", "City", "Inter", "Milan", "Bayern", "Liverpool", "Ajax", "Benfica"]

        matches = []
        for i in range(limit):
            home = random.choice(equipos)
            away = random.choice([e for e in equipos if e != home])
            minuto = random.randint(1, 90)
            marcador_local = random.randint(0, 3)
            marcador_visitante = random.randint(0, 3)

            matches.append({
                "id": 100000 + i,
                "liga": random.choice(ligas),
                "local": home,
                "visitante": away,
                "minuto": minuto,
                "marcador_local": marcador_local,
                "marcador_visitante": marcador_visitante,
                # opcional para tu motor:
                "xG": round(random.uniform(0.2, 2.2), 2),
                "momentum": random.choice(["bajo", "medio", "alto"]),
            })

        return matches

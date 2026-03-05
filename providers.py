# providers.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import random
import time

@dataclass
class LiveMatch:
    id: int
    country: str
    league: str
    is_first_division: bool
    home: str
    away: str
    minute: int
    score_home: int
    score_away: int

@dataclass
class LiveStats:
    match_id: int
    shots_on_target_home: int
    shots_on_target_away: int
    attacks_home: int
    attacks_away: int
    dangerous_attacks_home: int
    dangerous_attacks_away: int
    possession_home: int
    possession_away: int
    xg_home: float
    xg_away: float

@dataclass
class Odds:
    match_id: int
    market: str
    selection: str
    odd: float

class DataProvider:
    """Interfaz. Luego la reemplazamos por API-Football + Odds."""
    async def get_live_matches(self) -> List[LiveMatch]:
        raise NotImplementedError

    async def get_live_stats(self, match_id: int) -> LiveStats:
        raise NotImplementedError

    async def get_odds(self, match_id: int) -> List[Odds]:
        raise NotImplementedError

class MockProvider(DataProvider):
    """Genera partidos y stats falsos (pero realistas) para construir el sistema."""
    COUNTRIES = ["Argentina","Brasil","España","Inglaterra","Italia","Alemania","Francia","Portugal","Países Bajos","México","Colombia","Chile","Uruguay"]
    LEAGUES = ["Primera División", "Serie A", "Premier League", "LaLiga", "Bundesliga", "Ligue 1"]
    TEAMS = ["River","Boca","Flamengo","Palmeiras","Real Madrid","Barcelona","Liverpool","City","Inter","Milan","Bayern","PSG","Benfica","Porto","Ajax","PSV"]

    async def get_live_matches(self) -> List[LiveMatch]:
        random.seed(int(time.time()) // 60)  # cambia cada minuto
        matches = []
        n = 60  # tu objetivo
        for i in range(n):
            home, away = random.sample(self.TEAMS, 2)
            minute = random.randint(1, 90)
            score_home = random.randint(0, 3)
            score_away = random.randint(0, 3)
            matches.append(LiveMatch(
                id=100000 + i,
                country=random.choice(self.COUNTRIES),
                league=random.choice(self.LEAGUES),
                is_first_division=True,  # en mock lo dejamos True
                home=home,
                away=away,
                minute=minute,
                score_home=score_home,
                score_away=score_away,
            ))
        return matches

    async def get_live_stats(self, match_id: int) -> LiveStats:
        # stats coherentes
        shots_h = random.randint(0, 8)
        shots_a = random.randint(0, 8)
        poss_h = random.randint(35, 65)
        poss_a = 100 - poss_h
        return LiveStats(
            match_id=match_id,
            shots_on_target_home=shots_h,
            shots_on_target_away=shots_a,
            attacks_home=random.randint(20, 120),
            attacks_away=random.randint(20, 120),
            dangerous_attacks_home=random.randint(5, 60),
            dangerous_attacks_away=random.randint(5, 60),
            possession_home=poss_h,
            possession_away=poss_a,
            xg_home=round(random.uniform(0.1, 2.5), 2),
            xg_away=round(random.uniform(0.1, 2.5), 2),
        )

    async def get_odds(self, match_id: int) -> List[Odds]:
        # odds simuladas
        markets = [
            Odds(match_id, "OVER_UNDER_0_5_NEXT_15", "OVER", round(random.uniform(1.40, 2.80), 2)),
            Odds(match_id, "OVER_UNDER_0_5_NEXT_15", "UNDER", round(random.uniform(1.40, 2.80), 2)),
            Odds(match_id, "NEXT_GOAL_NEXT_15", "HOME", round(random.uniform(2.00, 4.50), 2)),
            Odds(match_id, "NEXT_GOAL_NEXT_15", "AWAY", round(random.uniform(2.00, 4.50), 2)),
            Odds(match_id, "NEXT_GOAL_NEXT_15", "NONE", round(random.uniform(1.70, 3.50), 2)),
        ]
        return markets

def to_dict(obj) -> Dict[str, Any]:
    return asdict(obj)

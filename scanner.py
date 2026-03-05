# scanner.py
from typing import List, Dict
import random

# ✅ ligas fuertes (puedes agregar/quitar)
LIGAS_FUERTES = {
    "Premier League",
    "LaLiga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Primeira Liga",
    "Eredivisie",
    "Brasileirão",
    "Primera División",
    "MLS",
}

def filtrar_partidos(partidos: List[Dict], max_partidos: int = 60) -> List[Dict]:
    """
    Filtra solo ligas fuertes y corta a máximo N partidos.
    """
    fuertes = [p for p in partidos if p.get("liga") in LIGAS_FUERTES]
    return fuertes[:max_partidos]


def predecir_next15(partido: Dict) -> Dict:
    """
    🔥 Predicción simple (demo): calcula prob de gol próximo 15 min
    (Luego lo reemplazamos con API real + modelo mejor).
    """
    minuto = int(partido.get("minuto", 0))
    marcador_local = int(partido.get("marcador_local", 0))
    marcador_visitante = int(partido.get("marcador_visitante", 0))

    # base: mientras más tarde, más chance de gol (ejemplo)
    base = min(0.15 + (minuto / 90) * 0.35, 0.60)

    # si está empatado sube un poquito
    if marcador_local == marcador_visitante:
        base += 0.07

    # ruido pequeño para no repetir siempre
    base += random.uniform(-0.03, 0.03)

    prob_gol_15 = max(0.05, min(base, 0.85))

    pred = {
        "pred_next15_more_goals": prob_gol_15,
        "pred_next15_no_goal": 1 - prob_gol_15,
    }
    return pred

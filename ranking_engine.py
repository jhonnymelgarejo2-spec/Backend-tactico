from typing import List, Dict


def calcular_match_score(p: Dict) -> float:
    """
    Score general del partido para detectar partidos calientes.
    """

    goal_pressure = p.get("goal_pressure", {}) or {}
    goal_predictor = p.get("goal_predictor", {}) or {}
    chaos = p.get("chaos", {}) or {}

    pressure_score = float(goal_pressure.get("pressure_score", 0) or 0)
    predictor_score = float(goal_predictor.get("predictor_score", 0) or 0)
    chaos_score = float(chaos.get("chaos_score", 0) or 0)
    xg = float(p.get("xG", 0) or 0)

    momentum = str(p.get("momentum", "MEDIO")).upper()
    minuto = int(p.get("minuto", 0) or 0)

    score = 0

    score += pressure_score * 1.3
    score += predictor_score * 1.6
    score += chaos_score * 1.2
    score += xg * 10

    if momentum == "MUY ALTO":
        score += 12
    elif momentum == "ALTO":
        score += 8
    elif momentum == "MEDIO":
        score += 4

    if 15 <= minuto <= 75:
        score += 6
    elif minuto > 75:
        score += 3

    return round(score, 2)


def rankear_partidos(partidos: List[Dict]) -> List[Dict]:
    """
    Ordena partidos por intensidad táctica.
    """

    for p in partidos:
        p["match_score"] = calcular_match_score(p)

    partidos.sort(
        key=lambda p: float(p.get("match_score", 0)),
        reverse=True
    )

    return partidos


def obtener_partidos_calientes(partidos: List[Dict], limite: int = 3) -> List[Dict]:
    """
    Devuelve los partidos más calientes del sistema.
    """

    partidos_rank = rankear_partidos(partidos)

    return partidos_rank[:limite]


def rankear_senales(senales: List[Dict]) -> List[Dict]:
    """
    Ordena señales por importancia real.
    """

    senales.sort(
        key=lambda s: (
            float(s.get("signal_score", 0)),
            float(s.get("tactical_score", 0)),
            float(s.get("goal_inminente_score", 0)),
            float(s.get("confidence", 0)),
            float(s.get("value", 0))
        ),
        reverse=True
    )

    return senales


def obtener_senal_principal(senales: List[Dict]) -> Dict | None:
    """
    Devuelve la mejor señal del sistema.
    """

    if not senales:
        return None

    senales_rank = rankear_senales(senales)

    return senales_rank[0]

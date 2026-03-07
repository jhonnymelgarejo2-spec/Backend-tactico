# goal_pressure_engine.py

from typing import Dict


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def calcular_goal_pressure(partido: Dict) -> Dict:
    minuto = int(partido.get("minuto", 0) or 0)
    xg = float(partido.get("xG", partido.get("xg", 0)) or 0)
    momentum = str(partido.get("momentum", "medio")).lower()

    marcador_local = int(partido.get("marcador_local", 0) or 0)
    marcador_visitante = int(partido.get("marcador_visitante", 0) or 0)

    diff = abs(marcador_local - marcador_visitante)

    score = 0

    # Minuto útil
    if 18 <= minuto <= 35:
        score += 2
    elif 36 <= minuto <= 75:
        score += 3
    elif 76 <= minuto <= 88:
        score += 2

    # xG
    if xg >= 2.4:
        score += 4
    elif xg >= 1.7:
        score += 3
    elif xg >= 1.0:
        score += 2

    # Momentum
    if "muy alto" in momentum:
        score += 4
    elif "alto" in momentum:
        score += 3
    elif "medio" in momentum:
        score += 1

    # Marcador cerrado
    if diff == 0:
        score += 2
    elif diff == 1:
        score += 1

    # Penalizar partidos muy muertos
    if xg < 0.7 and momentum in ("bajo",):
        score -= 2

    score = clamp(score, 0, 15)

    if score >= 11:
        nivel = "EXTREMA"
    elif score >= 8:
        nivel = "ALTA"
    elif score >= 5:
        nivel = "MEDIA"
    else:
        nivel = "BAJA"

    gol_3_7 = score >= 10
    gol_10_15 = score >= 7

    return {
        "pressure_score": score,
        "pressure_level": nivel,
        "goal_likely_3_7_min": gol_3_7,
        "goal_likely_10_15_min": gol_10_15,
        "reason": construir_razon(score, xg, momentum, minuto, diff)
    }


def construir_razon(score: int, xg: float, momentum: str, minuto: int, diff: int) -> str:
    partes = []

    if xg >= 1.7:
        partes.append("xG alto")
    elif xg >= 1.0:
        partes.append("xG favorable")

    if "muy alto" in momentum:
        partes.append("momentum muy alto")
    elif "alto" in momentum:
        partes.append("momentum alto")

    if 20 <= minuto <= 75:
        partes.append("ventana de minuto ideal")

    if diff <= 1:
        partes.append("marcador cerrado")

    if not partes:
        return "Presión ofensiva limitada"

    return " + ".join(partes)

from typing import Dict


def clamp(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(valor, maximo))


def predecir_gol_inminente(partido: Dict) -> Dict:
    minuto = int(partido.get("minuto", 0) or 0)
    xg = float(partido.get("xG", partido.get("xg", 0)) or 0)
    momentum = str(partido.get("momentum", "medio")).lower()

    marcador_local = int(partido.get("marcador_local", 0) or 0)
    marcador_visitante = int(partido.get("marcador_visitante", 0) or 0)
    diff = abs(marcador_local - marcador_visitante)

    goal_pressure = partido.get("goal_pressure", {}) or {}
    pressure_score = float(goal_pressure.get("pressure_score", 0) or 0)

    scanner_score = float(partido.get("_scanner_score", 0) or 0)

    score = 0.0

    # Minuto útil
    if 18 <= minuto <= 35:
        score += 1.5
    elif 36 <= minuto <= 75:
        score += 2.5
    elif 76 <= minuto <= 88:
        score += 2.0

    # xG
    if xg >= 3.0:
        score += 3.0
    elif xg >= 2.2:
        score += 2.5
    elif xg >= 1.5:
        score += 1.8
    elif xg >= 1.0:
        score += 1.0

    # Momentum
    if "muy alto" in momentum:
        score += 2.5
    elif "alto" in momentum:
        score += 1.8
    elif "medio" in momentum:
        score += 0.8

    # Marcador cerrado
    if diff == 0:
        score += 1.5
    elif diff == 1:
        score += 1.0

    # Goal pressure y scanner
    score += pressure_score * 0.35
    score += scanner_score * 0.15

    # Penalizaciones suaves
    if minuto < 10:
        score -= 1.0
    if minuto > 88:
        score -= 2.0
    if xg < 0.7 and "bajo" in momentum:
        score -= 2.0

    score = clamp(score, 0, 12)

    # Probabilidades
    goal_next_5_prob = round(clamp(score / 12 * 0.82, 0.03, 0.92), 3)
    goal_next_10_prob = round(clamp(goal_next_5_prob + 0.12, 0.08, 0.97), 3)

    # Niveles de alerta
    if goal_next_5_prob >= 0.72:
        alert_level = "ROJA"
    elif goal_next_5_prob >= 0.58:
        alert_level = "NARANJA"
    elif goal_next_5_prob >= 0.42:
        alert_level = "AMARILLA"
    else:
        alert_level = "BAJA"

    alert_reason = construir_razon(
        minuto=minuto,
        xg=xg,
        momentum=momentum,
        diff=diff,
        pressure_score=pressure_score,
        scanner_score=scanner_score
    )

    return {
        "goal_next_5_prob": goal_next_5_prob,
        "goal_next_10_prob": goal_next_10_prob,
        "alert_level": alert_level,
        "alert_reason": alert_reason,
        "predictor_score": round(score, 2)
    }


def construir_razon(
    minuto: int,
    xg: float,
    momentum: str,
    diff: int,
    pressure_score: float,
    scanner_score: float
) -> str:
    partes = []

    if xg >= 2.2:
        partes.append("xG muy alto")
    elif xg >= 1.5:
        partes.append("xG alto")

    if "muy alto" in momentum:
        partes.append("momentum muy alto")
    elif "alto" in momentum:
        partes.append("momentum alto")

    if 20 <= minuto <= 80:
        partes.append("ventana ideal")

    if diff <= 1:
        partes.append("marcador cerrado")

    if pressure_score >= 10:
        partes.append("presión ofensiva fuerte")

    if scanner_score >= 12:
        partes.append("scanner muy favorable")

    if not partes:
        return "Sin condiciones fuertes para gol inmediato"

    return " + ".join(partes)

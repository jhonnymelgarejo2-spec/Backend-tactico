from typing import Dict


def clamp(valor: float, minimo: float, maximo: float) -> float:
    return max(minimo, min(valor, maximo))


def calcular_chaos(partido: Dict) -> Dict:
    minuto = int(partido.get("minuto", 0) or 0)
    xg = float(partido.get("xG", partido.get("xg", 0)) or 0)
    momentum = str(partido.get("momentum", "medio")).lower()

    marcador_local = int(partido.get("marcador_local", 0) or 0)
    marcador_visitante = int(partido.get("marcador_visitante", 0) or 0)
    diff = abs(marcador_local - marcador_visitante)

    goal_pressure = partido.get("goal_pressure", {}) or {}
    pressure_score = float(goal_pressure.get("pressure_score", 0) or 0)
    pressure_level = str(goal_pressure.get("pressure_level", "BAJA")).upper()

    goal_predictor = partido.get("goal_predictor", {}) or {}
    predictor_score = float(goal_predictor.get("predictor_score", 0) or 0)
    goal5 = float(goal_predictor.get("goal_next_5_prob", 0) or 0)
    goal10 = float(goal_predictor.get("goal_next_10_prob", 0) or 0)

    scanner_score = float(partido.get("_scanner_score", 0) or 0)

    chaos_score = 0.0
    razones = []

    # 1. Momento del partido
    if 20 <= minuto <= 35:
        chaos_score += 1.5
        razones.append("primer bloque caliente")
    elif 55 <= minuto <= 75:
        chaos_score += 2.5
        razones.append("segundo tiempo activo")
    elif 76 <= minuto <= 88:
        chaos_score += 3.0
        razones.append("tramo final peligroso")

    # 2. xG acumulado alto
    if xg >= 3.0:
        chaos_score += 3.0
        razones.append("xG muy alto")
    elif xg >= 2.2:
        chaos_score += 2.3
        razones.append("xG alto")
    elif xg >= 1.5:
        chaos_score += 1.5
        razones.append("xG aceptable")

    # 3. Momentum
    if "muy alto" in momentum:
        chaos_score += 2.5
        razones.append("momentum muy alto")
    elif "alto" in momentum:
        chaos_score += 1.8
        razones.append("momentum alto")
    elif "medio" in momentum:
        chaos_score += 0.7

    # 4. Marcador cerrado = más caos potencial
    if diff == 0:
        chaos_score += 2.2
        razones.append("marcador empatado")
    elif diff == 1:
        chaos_score += 1.2
        razones.append("partido abierto por diferencia mínima")

    # 5. Presión ofensiva
    if pressure_score >= 12:
        chaos_score += 3.0
        razones.append("presión ofensiva extrema")
    elif pressure_score >= 9:
        chaos_score += 2.2
        razones.append("presión ofensiva alta")
    elif pressure_score >= 6:
        chaos_score += 1.2

    if pressure_level == "EXTREMA":
        chaos_score += 1.0
    elif pressure_level == "ALTA":
        chaos_score += 0.5

    # 6. Predictor ya ve peligro
    if predictor_score >= 10:
        chaos_score += 2.0
        razones.append("predictor muy alto")
    elif predictor_score >= 8:
        chaos_score += 1.2
        razones.append("predictor favorable")

    if goal5 >= 0.70:
        chaos_score += 2.0
        razones.append("gol probable en 5 min")
    elif goal5 >= 0.55:
        chaos_score += 1.0

    if goal10 >= 0.80:
        chaos_score += 1.0
        razones.append("gol muy probable en 10 min")

    # 7. Scanner fuerte = partido ya seleccionado por inteligencia previa
    if scanner_score >= 14:
        chaos_score += 1.5
        razones.append("scanner muy favorable")
    elif scanner_score >= 10:
        chaos_score += 0.8

    # Penalizaciones suaves
    if minuto < 10:
        chaos_score -= 1.5
    if minuto > 89:
        chaos_score -= 2.0
    if xg < 0.8 and "bajo" in momentum:
        chaos_score -= 2.0
        razones.append("ritmo flojo")

    chaos_score = round(clamp(chaos_score, 0, 15), 2)

    # Niveles
    if chaos_score >= 11:
        chaos_level = "EXTREMO"
        chaos_window_open = True
    elif chaos_score >= 8:
        chaos_level = "ALTO"
        chaos_window_open = True
    elif chaos_score >= 5:
        chaos_level = "MEDIO"
        chaos_window_open = False
    else:
        chaos_level = "BAJO"
        chaos_window_open = False

    if not razones:
        chaos_reason = "Partido estable, sin señales fuertes de ruptura"
    else:
        chaos_reason = " + ".join(razones[:5])

    return {
        "chaos_score": chaos_score,
        "chaos_level": chaos_level,
        "chaos_window_open": chaos_window_open,
        "chaos_reason": chaos_reason
    }

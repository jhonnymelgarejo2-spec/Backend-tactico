from typing import Dict


# =========================================================
# HELPERS
# =========================================================
def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _clamp(value, low, high):
    return max(low, min(high, value))


# =========================================================
# ENGINE PRINCIPAL
# =========================================================
def evaluar_tempo_partido(partido: Dict) -> Dict:
    minuto = _safe_int(partido.get("minuto", 0))
    xg = _safe_float(partido.get("xG", 0), 0.0)
    shots = _safe_int(partido.get("shots", 0))
    shots_on_target = _safe_int(partido.get("shots_on_target", 0))
    dangerous_attacks = _safe_int(partido.get("dangerous_attacks", 0))
    momentum = str(partido.get("momentum", "") or "").strip().upper()

    if minuto <= 0:
        minuto = 1

    xg_per_min = round(xg / minuto, 4)
    shots_per_min = round(shots / minuto, 4)
    dangerous_per_min = round(dangerous_attacks / minuto, 4)

    tempo_score = 0.0
    reason = []

    # xG por minuto
    if xg_per_min >= 0.030:
        tempo_score += 28
        reason.append("xG por minuto muy alto")
    elif xg_per_min >= 0.020:
        tempo_score += 18
        reason.append("xG por minuto alto")
    elif xg_per_min >= 0.012:
        tempo_score += 10
        reason.append("xG por minuto aceptable")

    # tiros
    if shots_per_min >= 0.28:
        tempo_score += 18
        reason.append("Frecuencia de tiros alta")
    elif shots_per_min >= 0.18:
        tempo_score += 10
        reason.append("Tiros constantes")

    # tiros a puerta
    if shots_on_target >= 6:
        tempo_score += 18
        reason.append("Muchos tiros a puerta")
    elif shots_on_target >= 3:
        tempo_score += 10
        reason.append("Varias llegadas claras")

    # ataques peligrosos
    if dangerous_per_min >= 0.75:
        tempo_score += 20
        reason.append("Ataques peligrosos muy frecuentes")
    elif dangerous_per_min >= 0.45:
        tempo_score += 12
        reason.append("Ataques peligrosos constantes")

    # momentum
    if momentum == "MUY ALTO":
        tempo_score += 12
        reason.append("Momentum muy alto")
    elif momentum == "ALTO":
        tempo_score += 8
        reason.append("Momentum ofensivo")

    # castigo por ritmo muerto
    if minuto >= 70 and shots_on_target <= 2 and xg < 1.0:
        tempo_score -= 12
        reason.append("Ritmo bajo en tramo final")

    tempo_score = round(_clamp(tempo_score, 0, 100), 2)

    if tempo_score >= 70:
        tempo_state = "ACELERADO"
    elif tempo_score >= 45:
        tempo_state = "DINAMICO"
    elif tempo_score >= 25:
        tempo_state = "CONTROLADO"
    else:
        tempo_state = "LENTO"

    goal_flow_risk = 0.0
    if tempo_state == "ACELERADO":
        goal_flow_risk = 28.0
    elif tempo_state == "DINAMICO":
        goal_flow_risk = 18.0
    elif tempo_state == "CONTROLADO":
        goal_flow_risk = 10.0
    else:
        goal_flow_risk = 4.0

    return {
        "tempo_score": tempo_score,
        "tempo_state": tempo_state,
        "tempo_reason": " | ".join(reason) if reason else "Sin lectura de ritmo clara",
        "tempo_xg_per_min": xg_per_min,
        "tempo_shots_per_min": shots_per_min,
        "tempo_dangerous_per_min": dangerous_per_min,
        "goal_flow_risk": round(goal_flow_risk, 2),
    }


# =========================================================
# APLICAR A SEÑAL
# =========================================================
def aplicar_tempo_a_senal(senal: Dict, tempo_data: Dict) -> Dict:
    confidence = _safe_float(senal.get("confidence", 0))
    value = _safe_float(senal.get("value", 0))
    market = str(senal.get("market", "") or "").upper()

    tempo_state = tempo_data.get("tempo_state", "CONTROLADO")
    goal_flow_risk = _safe_float(tempo_data.get("goal_flow_risk", 0))

    if tempo_state == "ACELERADO":
        if "OVER" in market or "GOAL" in market:
            confidence += 4.0
            value += 1.2
        elif "HOLD" in market:
            confidence -= 4.0
            value -= 1.0

    elif tempo_state == "DINAMICO":
        if "OVER" in market or "GOAL" in market:
            confidence += 2.2
            value += 0.7
        elif "HOLD" in market:
            confidence -= 2.0
            value -= 0.5

    elif tempo_state == "LENTO":
        if "HOLD" in market:
            confidence += 3.0
            value += 0.8
        elif "OVER" in market or "GOAL" in market:
            confidence -= 3.5
            value -= 0.9

    # refuerzo por riesgo de flujo de gol
    if goal_flow_risk >= 20 and ("OVER" in market or "GOAL" in market):
        confidence += 1.5
        value += 0.4

    senal["confidence"] = round(_clamp(confidence, 0, 100), 2)
    senal["value"] = round(max(0, value), 2)

    senal.update(tempo_data)
    return senal

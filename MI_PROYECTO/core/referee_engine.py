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


# =========================================================
# ENGINE PRINCIPAL
# =========================================================
def evaluar_arbitro(partido: Dict) -> Dict:
    faltas_local = _safe_int(partido.get("faltas_local", 0))
    faltas_visitante = _safe_int(partido.get("faltas_visitante", 0))
    amarillas_local = _safe_int(partido.get("amarillas_local", 0))
    amarillas_visitante = _safe_int(partido.get("amarillas_visitante", 0))
    rojas_local = _safe_int(partido.get("rojas_local", 0))
    rojas_visitante = _safe_int(partido.get("rojas_visitante", 0))
    minuto = _safe_int(partido.get("minuto", 0))

    total_faltas = faltas_local + faltas_visitante
    total_amarillas = amarillas_local + amarillas_visitante
    total_rojas = rojas_local + rojas_visitante

    referee_score = 0.0
    reason = []

    if total_faltas >= 22:
        referee_score += 18
        reason.append("Partido con muchas faltas")
    elif total_faltas >= 14:
        referee_score += 10
        reason.append("Ritmo con interrupciones")

    if total_amarillas >= 5:
        referee_score += 20
        reason.append("Alta tensión disciplinaria")
    elif total_amarillas >= 3:
        referee_score += 10
        reason.append("Varias amarillas acumuladas")

    if total_rojas >= 1:
        referee_score += 25
        reason.append("Hay expulsión, partido alterado")

    if minuto >= 70 and total_amarillas >= 4:
        referee_score += 10
        reason.append("Final caliente")

    if total_faltas <= 8 and total_amarillas == 0:
        referee_score -= 8
        reason.append("Árbitro deja jugar mucho")

    if referee_score >= 45:
        referee_state = "CALIENTE"
    elif referee_score >= 20:
        referee_state = "ACTIVO"
    else:
        referee_state = "NORMAL"

    penalty_risk = 0.0
    if total_faltas >= 18:
        penalty_risk += 12
    if total_amarillas >= 4:
        penalty_risk += 10
    if total_rojas >= 1:
        penalty_risk += 8
    penalty_risk = round(min(penalty_risk, 35), 2)

    return {
        "referee_score": round(referee_score, 2),
        "referee_state": referee_state,
        "referee_reason": " | ".join(reason) if reason else "Sin sesgo arbitral claro",
        "referee_total_fouls": total_faltas,
        "referee_total_yellows": total_amarillas,
        "referee_total_reds": total_rojas,
        "penalty_event_risk": penalty_risk,
    }


# =========================================================
# APLICAR A SEÑAL
# =========================================================
def aplicar_arbitro_a_senal(senal: Dict, referee_data: Dict) -> Dict:
    confidence = _safe_float(senal.get("confidence", 0))
    value = _safe_float(senal.get("value", 0))
    market = str(senal.get("market", "")).upper()

    referee_state = referee_data.get("referee_state", "NORMAL")
    penalty_risk = _safe_float(referee_data.get("penalty_event_risk", 0))

    if referee_state == "CALIENTE":
        if "OVER" in market or "GOAL" in market:
            confidence += 2.5
            value += 0.8
        else:
            confidence -= 1.5

    elif referee_state == "ACTIVO":
        if "OVER" in market or "GOAL" in market:
            confidence += 1.2
            value += 0.4

    if penalty_risk >= 20 and ("OVER" in market or "GOAL" in market):
        confidence += 1.5
        value += 0.5

    senal["confidence"] = round(max(0, min(100, confidence)), 2)
    senal["value"] = round(max(0, value), 2)

    senal.update(referee_data)
    return senal

from typing import Dict


def _safe_float(v, d=0.0):
    try:
        return float(v)
    except:
        return d


def _safe_int(v, d=0):
    try:
        return int(v)
    except:
        return d


def evaluar_chaos_partido(partido: Dict, senal: Dict) -> Dict:
    """
    Detecta partidos impredecibles o engañosos
    """

    xg = _safe_float(partido.get("xG"), 0)
    shots = _safe_int(partido.get("shots"), 0)
    shots_on_target = _safe_int(partido.get("shots_on_target"), 0)
    dangerous = _safe_int(partido.get("dangerous_attacks"), 0)
    minuto = _safe_int(partido.get("minuto"), 0)

    goal_prob_5 = _safe_float(senal.get("goal_prob_5"), 0)
    goal_prob_10 = _safe_float(senal.get("goal_prob_10"), 0)

    confidence = _safe_float(senal.get("confidence"), 0)

    chaos_score = 0
    chaos_reason = []

    # =========================================
    # 1. MUCHAS LLEGADAS PERO POCO GOL
    # =========================================
    if shots > 10 and shots_on_target <= 2:
        chaos_score += 25
        chaos_reason.append("Muchos tiros sin precisión")

    # =========================================
    # 2. XG ALTO PERO SIN GOL
    # =========================================
    if xg >= 1.5 and shots_on_target <= 3:
        chaos_score += 20
        chaos_reason.append("xG alto pero sin efectividad")

    # =========================================
    # 3. ATAQUES SIN CONVERSIÓN
    # =========================================
    if dangerous > 35 and shots_on_target < 3:
        chaos_score += 15
        chaos_reason.append("Ataques peligrosos sin remate claro")

    # =========================================
    # 4. PROBABILIDAD ALTA PERO POCA EVIDENCIA
    # =========================================
    if goal_prob_5 > 40 and shots_on_target <= 2:
        chaos_score += 20
        chaos_reason.append("Probabilidad inflada sin evidencia real")

    # =========================================
    # 5. MINUTO ALTO SIN RESOLUCIÓN
    # =========================================
    if minuto > 70 and shots_on_target <= 3:
        chaos_score += 10
        chaos_reason.append("Tiempo alto sin claridad ofensiva")

    # =========================================
    # CLASIFICACIÓN
    # =========================================
    if chaos_score >= 60:
        chaos_level = "ALTO"
    elif chaos_score >= 30:
        chaos_level = "MEDIO"
    else:
        chaos_level = "BAJO"

    bloquear = False

    # 🔥 REGLA CRÍTICA
    if chaos_level == "ALTO" and confidence < 85:
        bloquear = True

    return {
        "chaos_score": chaos_score,
        "chaos_level": chaos_level,
        "chaos_block_signal": bloquear,
        "chaos_reason": ", ".join(chaos_reason) if chaos_reason else "Partido estable"
  }

# risk_engine.py

from typing import Dict, List


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _upper(value) -> str:
    return str(value or "").strip().upper()


def _contains_over_market(signal: Dict) -> bool:
    market = _upper(signal.get("market"))
    selection = _upper(signal.get("selection"))

    over_keywords = [
        "OVER",
        "NEXT_GOAL",
        "GOAL",
    ]

    return any(k in market or k in selection for k in over_keywords)


def _contains_hold_market(signal: Dict) -> bool:
    market = _upper(signal.get("market"))
    selection = _upper(signal.get("selection"))

    hold_keywords = [
        "RESULT_HOLDS",
        "SE MANTIENE EL RESULTADO",
        "HOLD",
    ]

    return any(k in market or k in selection for k in hold_keywords)


def evaluar_minuto(minuto: int) -> Dict:
    riesgo = 0
    motivos = []

    if minuto >= 88:
        riesgo += 5
        motivos.append("Minuto extremadamente alto")
    elif minuto >= 84:
        riesgo += 4
        motivos.append("Minuto muy alto")
    elif minuto >= 80:
        riesgo += 3
        motivos.append("Minuto alto")
    elif minuto >= 75:
        riesgo += 2
        motivos.append("Tramo final del partido")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def evaluar_estado_partido(match_state: Dict) -> Dict:
    estado = _upper((match_state or {}).get("estado"))
    score_estado = _safe_float((match_state or {}).get("score_estado"), 0)

    riesgo = 0
    motivos = []

    if estado == "MUERTO":
        riesgo += 5
        motivos.append("Partido muerto")
    elif estado == "FRIO":
        riesgo += 3
        motivos.append("Partido frío")
    elif estado == "CONTROLADO":
        riesgo += 2
        motivos.append("Partido controlado")
    elif estado == "TRAMPA":
        riesgo += 5
        motivos.append("Partido trampa detectado")
    elif estado in ("CALIENTE", "EXPLOSIVO", "CAOS"):
        if score_estado < 8:
            riesgo += 1
            motivos.append("Estado fuerte pero con score bajo")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def evaluar_riesgo_por_marcador(match: Dict, signal: Dict) -> Dict:
    ml = _safe_int(match.get("marcador_local"), 0)
    mv = _safe_int(match.get("marcador_visitante"), 0)
    minuto = _safe_int(match.get("minuto"), 0)
    diff = abs(ml - mv)

    riesgo = 0
    motivos = []

    is_over = _contains_over_market(signal)
    is_hold = _contains_hold_market(signal)

    if is_over:
        if diff >= 3 and minuto >= 70:
            riesgo += 4
            motivos.append("Marcador muy abierto pero tramo tardío")
        elif diff >= 2 and minuto >= 75:
            riesgo += 3
            motivos.append("Ventaja amplia en tramo final")
        elif diff == 0 and minuto >= 82:
            riesgo += 2
            motivos.append("Empate tardío con poco margen temporal")

    if is_hold:
        if diff == 0 and minuto < 60:
            riesgo += 1
            motivos.append("Mercado hold demasiado temprano")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def evaluar_presion_falsa(match: Dict) -> Dict:
    goal_pressure = match.get("goal_pressure", {}) or {}
    goal_predictor = match.get("goal_predictor", {}) or {}
    chaos = match.get("chaos", {}) or {}

    dangerous_attacks = _safe_float(match.get("dangerous_attacks"), 0)
    shots = _safe_float(match.get("shots"), 0)
    shots_on_target = _safe_float(match.get("shots_on_target"), 0)
    xg = _safe_float(match.get("xG"), 0)

    pressure_score = _safe_float(goal_pressure.get("pressure_score"), 0)
    predictor_score = _safe_float(goal_predictor.get("predictor_score"), 0)
    chaos_score = _safe_float(chaos.get("chaos_score"), 0)

    riesgo = 0
    motivos = []

    # Mucho “ruido” pero poca producción real
    if dangerous_attacks >= 20 and shots_on_target == 0:
        riesgo += 4
        motivos.append("Muchos ataques sin tiros a puerta")

    if pressure_score >= 7 and shots_on_target == 0 and xg < 0.8:
        riesgo += 4
        motivos.append("Presión aparente sin peligro real")

    if chaos_score >= 8 and predictor_score < 4 and xg < 1.0:
        riesgo += 3
        motivos.append("Caos sin predictor ofensivo claro")

    if shots >= 8 and shots_on_target <= 1 and xg < 1.0:
        riesgo += 3
        motivos.append("Muchos tiros de baja calidad")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def evaluar_goal_window(signal: Dict, match: Dict) -> Dict:
    minuto = _safe_int(match.get("minuto"), 0)

    goal_prob_5 = _safe_float(signal.get("goal_prob_5"), 0)
    goal_prob_10 = _safe_float(signal.get("goal_prob_10"), 0)
    goal_prob_15 = _safe_float(signal.get("goal_prob_15"), 0)

    riesgo = 0
    motivos = []

    is_over = _contains_over_market(signal)

    if is_over:
        if minuto >= 85 and goal_prob_5 < 45:
            riesgo += 4
            motivos.append("Over tardío con baja probabilidad de gol inmediata")

        if minuto >= 80 and goal_prob_10 < 55:
            riesgo += 3
            motivos.append("Ventana corta sin suficiente presión de gol")

        if goal_prob_15 < 50:
            riesgo += 2
            motivos.append("Proyección de gol baja para este mercado")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def evaluar_value(signal: Dict) -> Dict:
    value = _safe_float(signal.get("value"), 0)
    value_score = _safe_float(signal.get("value_score"), 0)
    value_categoria = _upper(signal.get("value_categoria"))
    confidence = _safe_float(signal.get("confidence"), 0)

    riesgo = 0
    motivos = []

    if value < 2:
        riesgo += 4
        motivos.append("Value demasiado bajo")
    elif value < 5:
        riesgo += 2
        motivos.append("Value limitado")

    if value_score < 4:
        riesgo += 3
        motivos.append("Value score débil")
    elif value_score < 6:
        riesgo += 1
        motivos.append("Value score moderado")

    if value_categoria in ("SIN_VALUE", "VALUE_BAJO"):
        riesgo += 3
        motivos.append("Categoría de value débil")

    if confidence < 68:
        riesgo += 3
        motivos.append("Confianza insuficiente")
    elif confidence < 75:
        riesgo += 1
        motivos.append("Confianza media")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def evaluar_signal_strength(signal: Dict) -> Dict:
    signal_score = _safe_float(signal.get("signal_score"), 0)
    tactical_score = _safe_float(signal.get("tactical_score"), 0)
    goal_score = _safe_float(signal.get("goal_inminente_score"), 0)
    signal_rank = _upper(signal.get("signal_rank"))

    riesgo = 0
    motivos = []

    if signal_score < 160:
        riesgo += 4
        motivos.append("Signal score bajo")
    elif signal_score < 210:
        riesgo += 2
        motivos.append("Signal score medio")

    if tactical_score < 8:
        riesgo += 3
        motivos.append("Tactical score bajo")
    elif tactical_score < 12:
        riesgo += 1
        motivos.append("Tactical score moderado")

    if goal_score < 1.5 and _contains_over_market(signal):
        riesgo += 2
        motivos.append("Goal score débil para mercado ofensivo")

    if signal_rank == "NORMAL":
        riesgo += 2
        motivos.append("Rank normal")
    elif signal_rank == "ALTA":
        riesgo += 1
        motivos.append("Rank alta pero no top")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def evaluar_cierre_tactico(match: Dict, signal: Dict) -> Dict:
    minuto = _safe_int(match.get("minuto"), 0)
    momentum = _upper(match.get("momentum"))
    xg = _safe_float(match.get("xG"), 0)

    ml = _safe_int(match.get("marcador_local"), 0)
    mv = _safe_int(match.get("marcador_visitante"), 0)
    diff = abs(ml - mv)

    riesgo = 0
    motivos = []

    is_over = _contains_over_market(signal)

    if is_over:
        if minuto >= 78 and diff >= 1 and momentum in ("BAJO", "MEDIO") and xg < 1.4:
            riesgo += 4
            motivos.append("Posible cierre táctico en tramo final")

        if minuto >= 82 and diff >= 1:
            riesgo += 3
            motivos.append("Equipo ganador puede administrar resultado")

    return {
        "score": riesgo,
        "motivos": motivos
    }


def consolidar_riesgo(scores: List[Dict]) -> Dict:
    total = 0
    motivos: List[str] = []

    for item in scores:
        total += _safe_float(item.get("score"), 0)
        motivos.extend(item.get("motivos", []))

    if total >= 18:
        nivel = "NO_APOSTAR"
        apto = False
    elif total >= 12:
        nivel = "RIESGO_ALTO"
        apto = False
    elif total >= 7:
        nivel = "RIESGO_MEDIO"
        apto = True
    else:
        nivel = "APTO"
        apto = True

    # quitar duplicados conservando orden
    vistos = set()
    motivos_unicos = []
    for m in motivos:
        if m not in vistos:
            vistos.add(m)
            motivos_unicos.append(m)

    return {
        "risk_score": round(total, 2),
        "risk_level": nivel,
        "apto_para_entrar": apto,
        "motivos_riesgo": motivos_unicos
    }


def evaluar_riesgo(match: Dict, signal: Dict) -> Dict:
    """
    Función principal del motor de riesgo V13_ELITE.
    Recibe:
      - match: dict del partido enriquecido
      - signal: dict de la señal generada

    Devuelve:
      {
        "risk_score": 11,
        "risk_level": "RIESGO_MEDIO",
        "apto_para_entrar": True,
        "motivos_riesgo": [...]
      }
    """

    minuto = _safe_int(match.get("minuto"), signal.get("minute", 0))
    match_state = signal.get("estado_partido", {}) or match.get("estado_partido_data", {}) or {}

    bloques = [
        evaluar_minuto(minuto),
        evaluar_estado_partido(match_state),
        evaluar_riesgo_por_marcador(match, signal),
        evaluar_presion_falsa(match),
        evaluar_goal_window(signal, match),
        evaluar_value(signal),
        evaluar_signal_strength(signal),
        evaluar_cierre_tactico(match, signal),
    ]

    return consolidar_riesgo(bloques)

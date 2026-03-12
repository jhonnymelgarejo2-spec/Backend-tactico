from typing import List, Dict
from signal_engine import generar_senal
from risk_engine import evaluar_riesgo


def partido_es_apostable(p: Dict) -> tuple[bool, str]:
    minuto = int(p.get("minuto", 0) or 0)
    estado = str(p.get("estado_partido", "activo")).lower()

    if estado in ["finalizado", "finished", "ft", "ended"]:
        return False, "Partido finalizado"

    if minuto >= 88:
        return False, "Minuto demasiado alto"

    return True, "OK"


def calcular_tactical_score(p: Dict) -> float:
    goal_pressure = p.get("goal_pressure", {}) or {}
    goal_predictor = p.get("goal_predictor", {}) or {}
    chaos = p.get("chaos", {}) or {}

    pressure_score = float(goal_pressure.get("pressure_score", 0) or 0)
    predictor_score = float(goal_predictor.get("predictor_score", 0) or 0)
    chaos_score = float(chaos.get("chaos_score", 0) or 0)
    xg = float(p.get("xG", 0) or 0)
    minuto = int(p.get("minuto", 0) or 0)
    momentum = str(p.get("momentum", "MEDIO")).upper()

    score = 0.0
    score += pressure_score * 1.2
    score += predictor_score * 1.5
    score += chaos_score * 1.0
    score += xg * 8

    if momentum == "MUY ALTO":
        score += 12
    elif momentum == "ALTO":
        score += 8
    elif momentum == "MEDIO":
        score += 4

    if 15 <= minuto <= 75:
        score += 6
    elif 76 <= minuto <= 87:
        score += 3

    return round(score, 2)


def calcular_goal_inminente_score(senal: Dict) -> float:
    gp5 = float(senal.get("goal_prob_5", 0) or 0)
    gp10 = float(senal.get("goal_prob_10", 0) or 0)
    gp15 = float(senal.get("goal_prob_15", 0) or 0)

    estado_partido = senal.get("estado_partido", {}) or {}
    estado = str(estado_partido.get("estado", "")).upper()

    bonus_estado = 0
    if estado in ("EXPLOSIVO", "CAOS"):
        bonus_estado = 15
    elif estado == "CALIENTE":
        bonus_estado = 8
    elif estado == "CONTROLADO":
        bonus_estado = 3

    return round((gp5 * 0.5) + (gp10 * 0.3) + (gp15 * 0.2) + bonus_estado, 2)


def calcular_signal_score(senal: Dict, tactical_score: float) -> float:
    value = float(senal.get("value", 0) or 0)
    confidence = float(senal.get("confidence", 0) or 0)
    confianza_prediccion = float(senal.get("confianza_prediccion", 0) or 0)
    goal_score = calcular_goal_inminente_score(senal)

    score = 0.0
    score += value * 2.2
    score += confidence * 1.4
    score += confianza_prediccion * 0.7
    score += tactical_score * 0.9
    score += goal_score * 0.8

    return round(score, 2)


def calcular_prob_implicita_cuota(odd: float) -> float:
    odd = float(odd or 0)
    if odd <= 0:
        return 0.0
    return round(1 / odd, 4)


def calcular_value_metrics(senal: Dict) -> Dict:
    odd = float(senal.get("odd", 0) or 0)
    prob_real = float(senal.get("prob", 0) or 0)

    prob_implicita = calcular_prob_implicita_cuota(odd)
    edge_pct = round((prob_real - prob_implicita) * 100, 2)
    value_pct = edge_pct

    value_score = 0.0
    if edge_pct >= 15:
        value_score = 10
        value_categoria = "VALUE_ELITE"
        recomendacion_value = "APOSTAR_FUERTE"
        razon_value = "La cuota está muy por encima del valor esperado"
    elif edge_pct >= 8:
        value_score = 8
        value_categoria = "VALUE_ALTO"
        recomendacion_value = "APOSTAR"
        razon_value = "Existe valor positivo claro frente al mercado"
    elif edge_pct >= 4:
        value_score = 6
        value_categoria = "VALUE_MEDIO"
        recomendacion_value = "APOSTAR_SUAVE"
        razon_value = "Existe valor positivo razonable en la cuota"
    elif edge_pct >= 1:
        value_score = 4
        value_categoria = "VALUE_BAJO"
        recomendacion_value = "OBSERVAR"
        razon_value = "Value leve, no tan fuerte para entrada agresiva"
    else:
        value_score = 1
        value_categoria = "SIN_VALUE"
        recomendacion_value = "NO_APOSTAR"
        razon_value = "La cuota no ofrece ventaja real"

    return {
        "prob_implicita_calculada": prob_implicita,
        "edge_pct": edge_pct,
        "value_pct": value_pct,
        "value_score": value_score,
        "value_categoria": value_categoria,
        "recomendacion_value": recomendacion_value,
        "razon_value": razon_value,
    }


def enriquecer_senal(senal: Dict, partido: Dict) -> Dict:
    tactical_score = calcular_tactical_score(partido)
    goal_score = calcular_goal_inminente_score(senal)
    signal_score = calcular_signal_score(senal, tactical_score)

    senal["tactical_score"] = tactical_score
    senal["goal_inminente_score"] = goal_score
    senal["signal_score"] = signal_score

    if signal_score >= 260:
        senal["signal_rank"] = "ELITE"
    elif signal_score >= 210:
        senal["signal_rank"] = "TOP"
    elif signal_score >= 160:
        senal["signal_rank"] = "ALTA"
    else:
        senal["signal_rank"] = "NORMAL"

    value_metrics = calcular_value_metrics(senal)
    senal.update(value_metrics)

    return senal


def filtrar_value_bets_reales(senal: Dict) -> bool:
    value = float(senal.get("value", 0) or 0)
    confidence = float(senal.get("confidence", 0) or 0)
    riesgo = str(senal.get("riesgo_operativo", "MEDIO")).upper()
    value_categoria = str(senal.get("value_categoria", "SIN_VALUE")).upper()

    if value < 2:
        return False

    if confidence < 68:
        return False

    if value_categoria == "SIN_VALUE":
        return False

    if riesgo == "ALTO" and value < 10:
        return False

    return True


def filtrar_por_riesgo_final(senal: Dict) -> bool:
    risk_level = str(senal.get("risk_level", "APTO")).upper()
    apto = bool(senal.get("apto_para_entrar", True))

    if risk_level == "NO_APOSTAR":
        return False

    if risk_level == "RIESGO_ALTO" and not apto:
        return False

    return True


def generar_senales(partidos: List[Dict]) -> List[Dict]:
    senales = []

    for p in partidos:
        ok, _motivo = partido_es_apostable(p)
        if not ok:
            continue

        datos = {
            "id": p.get("id", ""),
            "momentum": p.get("momentum", "MEDIO"),
            "xG": p.get("xG", 0),
            "prob_real": p.get("prob_real", 0.75),
            "prob_implicita": p.get("prob_implicita", 0.54),
            "cuota": p.get("cuota", 1.85),
            "minuto": p.get("minuto", 0),
            "marcador_local": p.get("marcador_local", 0),
            "marcador_visitante": p.get("marcador_visitante", 0),
            "goal_pressure": p.get("goal_pressure", {}),
            "goal_predictor": p.get("goal_predictor", {}),
            "chaos": p.get("chaos", {}),
            "estado_partido": p.get("estado_partido", "activo"),
        }

        senal = generar_senal(datos)

        if not senal:
            continue

        if senal.get("mercado") == "SIN_SEÑAL":
            continue

        if float(senal.get("valor", 0) or 0) <= 0:
            continue

        senal_final = {
            "match_id": p.get("id", ""),
            "home": p.get("local", ""),
            "away": p.get("visitante", ""),
            "league": p.get("liga", ""),
            "country": p.get("pais", ""),
            "minute": p.get("minuto", 0),
            "score": f'{p.get("marcador_local", 0)}-{p.get("marcador_visitante", 0)}',
            "market": senal.get("mercado", ""),
            "selection": senal.get("apuesta", ""),
            "line": senal.get("linea"),
            "odd": senal.get("cuota", 1.85),
            "prob": senal.get("prob_real", 0.0),
            "value": senal.get("valor", 0.0),
            "confidence": senal.get("confianza", 0),
            "reason": senal.get("razon", ""),
            "tier": senal.get("tier", "NORMAL"),

            "estado_partido": senal.get("estado_partido", {}),
            "gol_inminente": senal.get("gol_inminente", {}),
            "signal_status": senal.get("signal_status", "OPEN"),

            "goal_prob_5": senal.get("goal_prob_5", 0),
            "goal_prob_10": senal.get("goal_prob_10", 0),
            "goal_prob_15": senal.get("goal_prob_15", 0),

            "resultado_probable": senal.get("resultado_probable", ""),
            "ganador_probable": senal.get("ganador_probable", ""),
            "doble_oportunidad_probable": senal.get("doble_oportunidad_probable", ""),
            "total_goles_estimado": senal.get("total_goles_estimado", 0),
            "linea_goles_probable": senal.get("linea_goles_probable", ""),
            "over_under_probable": senal.get("over_under_probable", ""),
            "confianza_prediccion": senal.get("confianza_prediccion", 0),
            "recomendacion_final": senal.get("recomendacion_final", "OBSERVAR"),
            "riesgo_operativo": senal.get("riesgo_operativo", "MEDIO"),

            "all_signals": senal.get("senales_posibles", []),
        }

        senal_final = enriquecer_senal(senal_final, p)

        # Motor de riesgo V13_ELITE
        riesgo = evaluar_riesgo(p, senal_final)
        senal_final["risk_score"] = riesgo["risk_score"]
        senal_final["risk_level"] = riesgo["risk_level"]
        senal_final["apto_para_entrar"] = riesgo["apto_para_entrar"]
        senal_final["motivos_riesgo"] = riesgo["motivos_riesgo"]

        if not filtrar_value_bets_reales(senal_final):
            continue

        if not filtrar_por_riesgo_final(senal_final):
            continue

        senales.append(senal_final)

    senales.sort(
        key=lambda s: (
            float(s.get("signal_score", 0) or 0),
            float(s.get("tactical_score", 0) or 0),
            float(s.get("goal_inminente_score", 0) or 0),
            float(s.get("confidence", 0) or 0),
            float(s.get("value", 0) or 0),
        ),
        reverse=True
    )

    return senales

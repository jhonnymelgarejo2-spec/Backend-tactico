# signal_engine.py

def normalizar_texto(valor):
    return str(valor or "").strip().upper()


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def calcular_valor(datos):
    prob_real = float(datos.get("prob_real", 0.75) or 0)
    prob_implicita = float(datos.get("prob_implicita", 0.54) or 0)
    return round((prob_real - prob_implicita) * 100, 2)


def calcular_confianza_base(datos):
    momentum = normalizar_texto(datos.get("momentum"))
    xg = float(datos.get("xG", 0) or 0)
    minuto = int(datos.get("minuto", 0) or 0)

    confianza = 50

    if momentum == "MUY ALTO":
        confianza += 18
    elif momentum == "ALTO":
        confianza += 12
    elif momentum == "MEDIO":
        confianza += 5

    if xg >= 2.5:
        confianza += 18
    elif xg >= 1.8:
        confianza += 12
    elif xg >= 1.2:
        confianza += 8
    elif xg >= 0.8:
        confianza += 4

    if 15 <= minuto <= 35:
        confianza += 4
    elif 36 <= minuto <= 75:
        confianza += 8
    elif 76 <= minuto <= 88:
        confianza += 5

    return clamp(confianza, 40, 95)


def clasificar_partido(datos):
    xg = float(datos.get("xG", 0) or 0)
    momentum = normalizar_texto(datos.get("momentum"))
    minuto = int(datos.get("minuto", 0) or 0)
    ml = int(datos.get("marcador_local", 0) or 0)
    mv = int(datos.get("marcador_visitante", 0) or 0)
    diff = abs(ml - mv)

    pressure_score = float((datos.get("goal_pressure") or {}).get("pressure_score", 0) or 0)
    chaos_score = float((datos.get("chaos") or {}).get("chaos_score", 0) or 0)
    goal5 = float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0) or 0)
    goal10 = float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0) or 0)

    score = 0

    if xg >= 2.5:
        score += 4
    elif xg >= 1.8:
        score += 3
    elif xg >= 1.2:
        score += 2

    if momentum == "MUY ALTO":
        score += 4
    elif momentum == "ALTO":
        score += 3
    elif momentum == "MEDIO":
        score += 1

    if pressure_score >= 10:
        score += 4
    elif pressure_score >= 8:
        score += 3
    elif pressure_score >= 5:
        score += 2

    if chaos_score >= 12:
        score += 4
    elif chaos_score >= 9:
        score += 3
    elif chaos_score >= 6:
        score += 2

    if goal5 >= 0.80:
        score += 4
    elif goal5 >= 0.65:
        score += 3
    elif goal5 >= 0.50:
        score += 2

    if goal10 >= 0.85:
        score += 2
    elif goal10 >= 0.70:
        score += 1

    if diff == 0:
        score += 2
    elif diff == 1:
        score += 1

    if chaos_score >= 14 and pressure_score >= 10:
        return {
            "estado": "CAOS",
            "score_estado": score,
            "razon": "Partido roto con intercambio constante de ataques"
        }

    if minuto >= 85 and xg < 1.0 and momentum in ("BAJO", "MEDIO"):
        return {
            "estado": "MUERTO",
            "score_estado": score,
            "razon": "Ritmo bajo y poco potencial ofensivo en tramo final"
        }

    if score >= 16:
        return {
            "estado": "EXPLOSIVO",
            "score_estado": score,
            "razon": "Alta probabilidad de cambio fuerte en el marcador o de otro gol pronto"
        }

    if score >= 11:
        return {
            "estado": "CALIENTE",
            "score_estado": score,
            "razon": "Presión ofensiva y dinámica favorable para movimientos en el marcador"
        }

    if score >= 7:
        return {
            "estado": "CONTROLADO",
            "score_estado": score,
            "razon": "Partido con actividad moderada pero sin explosión clara"
        }

    return {
        "estado": "FRIO",
        "score_estado": score,
        "razon": "Pocas señales ofensivas relevantes"
    }


def detectar_gol_inminente(datos):
    pressure_score = float((datos.get("goal_pressure") or {}).get("pressure_score", 0) or 0)
    chaos_score = float((datos.get("chaos") or {}).get("chaos_score", 0) or 0)
    goal5 = float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0) or 0)
    goal10 = float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0) or 0)
    momentum = normalizar_texto(datos.get("momentum"))
    xg = float(datos.get("xG", 0) or 0)

    score = 0

    if goal5 >= 0.85:
        score += 5
    elif goal5 >= 0.75:
        score += 4
    elif goal5 >= 0.65:
        score += 3

    if goal10 >= 0.90:
        score += 3
    elif goal10 >= 0.80:
        score += 2

    if pressure_score >= 10:
        score += 3
    elif pressure_score >= 8:
        score += 2

    if chaos_score >= 12:
        score += 3
    elif chaos_score >= 9:
        score += 2

    if momentum in ("ALTO", "MUY ALTO"):
        score += 2

    if xg >= 2.2:
        score += 2

    es_gol = score >= 10

    return {
        "gol_inminente": es_gol,
        "score_gol_inminente": score,
        "label": "GOL MUY PROBABLE" if es_gol else "SIN ALERTA",
        "razon": "Probabilidad inmediata elevada por predictor + presión + caos" if es_gol else "No se detecta gol inminente claro"
    }


def clasificar_tier(confianza, valor):
    if confianza >= 90 and valor >= 10:
        return "PREMIUM"
    if confianza >= 80 and valor >= 6:
        return "FUERTE"
    if confianza >= 70 and valor >= 2:
        return "NORMAL"
    return "DESCARTAR"


def estimar_total_goles(datos):
    ml = int(datos.get("marcador_local", 0) or 0)
    mv = int(datos.get("marcador_visitante", 0) or 0)
    goles_actuales = ml + mv

    xg = float(datos.get("xG", 0) or 0)
    minuto = int(datos.get("minuto", 0) or 0)
    momentum = normalizar_texto(datos.get("momentum"))
    pressure_score = float((datos.get("goal_pressure") or {}).get("pressure_score", 0) or 0)
    chaos_score = float((datos.get("chaos") or {}).get("chaos_score", 0) or 0)
    goal10 = float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0) or 0)

    extra = 0.0

    if xg >= 3.0:
        extra += 1.4
    elif xg >= 2.3:
        extra += 1.1
    elif xg >= 1.6:
        extra += 0.8
    elif xg >= 1.0:
        extra += 0.5
    else:
        extra += 0.2

    if momentum == "MUY ALTO":
        extra += 0.45
    elif momentum == "ALTO":
        extra += 0.30
    elif momentum == "MEDIO":
        extra += 0.15

    if pressure_score >= 10:
        extra += 0.40
    elif pressure_score >= 7:
        extra += 0.25

    if chaos_score >= 10:
        extra += 0.35
    elif chaos_score >= 6:
        extra += 0.20

    if goal10 >= 0.80:
        extra += 0.45
    elif goal10 >= 0.65:
        extra += 0.25

    if minuto >= 75:
        extra -= 0.15
    elif minuto <= 20:
        extra += 0.20

    total_estimado = round(max(goles_actuales, goles_actuales + extra), 2)
    return total_estimado


def predecir_linea_goles(total_estimado):
    if total_estimado >= 4.0:
        return {
            "linea_goles_probable": "OVER_3_5",
            "over_under_probable": "OVER 3.5"
        }
    if total_estimado >= 3.0:
        return {
            "linea_goles_probable": "OVER_2_5",
            "over_under_probable": "OVER 2.5"
        }
    if total_estimado >= 2.3:
        return {
            "linea_goles_probable": "UNDER_3_5",
            "over_under_probable": "UNDER 3.5"
        }
    return {
        "linea_goles_probable": "UNDER_2_5",
        "over_under_probable": "UNDER 2.5"
    }


def predecir_ganador(datos):
    ml = int(datos.get("marcador_local", 0) or 0)
    mv = int(datos.get("marcador_visitante", 0) or 0)
    momentum = normalizar_texto(datos.get("momentum"))
    xg = float(datos.get("xG", 0) or 0)
    pressure_score = float((datos.get("goal_pressure") or {}).get("pressure_score", 0) or 0)
    chaos_score = float((datos.get("chaos") or {}).get("chaos_score", 0) or 0)

    score_local = ml * 1.2
    score_visitante = mv * 1.2

    if momentum in ("ALTO", "MUY ALTO"):
        score_local += 0.6

    if xg >= 2.0:
        score_local += 0.5
    elif xg >= 1.2:
        score_local += 0.25

    if pressure_score >= 8:
        score_local += 0.35

    if chaos_score >= 8:
        score_local += 0.15
        score_visitante += 0.10

    diff = round(score_local - score_visitante, 2)

    if abs(diff) <= 0.35:
        return {
            "ganador_probable": "EMPATE",
            "doble_oportunidad_probable": "LOCAL_O_EMPATE",
            "confianza_prediccion": 68
        }

    if diff > 0:
        return {
            "ganador_probable": "LOCAL",
            "doble_oportunidad_probable": "LOCAL_O_EMPATE",
            "confianza_prediccion": 74 if diff < 1.0 else 81
        }

    return {
        "ganador_probable": "VISITANTE",
        "doble_oportunidad_probable": "EMPATE_O_VISITANTE",
        "confianza_prediccion": 74 if diff > -1.0 else 81
    }


def predecir_resultado_probable(datos, total_estimado, ganador_probable):
    ml = int(datos.get("marcador_local", 0) or 0)
    mv = int(datos.get("marcador_visitante", 0) or 0)
    goles_restantes = max(0, round(total_estimado - (ml + mv)))

    if ganador_probable == "EMPATE":
        if ml == mv:
            return f"{ml}-{mv}"
        objetivo = max(ml, mv)
        return f"{objetivo}-{objetivo}"

    if ganador_probable == "LOCAL":
        nuevo_local = ml + max(1, goles_restantes)
        nuevo_visitante = mv
        if nuevo_local <= nuevo_visitante:
            nuevo_local = nuevo_visitante + 1
        return f"{nuevo_local}-{nuevo_visitante}"

    nuevo_local = ml
    nuevo_visitante = mv + max(1, goles_restantes)
    if nuevo_visitante <= nuevo_local:
        nuevo_visitante = nuevo_local + 1
    return f"{nuevo_local}-{nuevo_visitante}"


def calcular_riesgo_operativo(datos, confianza_prediccion, estado_partido):
    valor = calcular_valor(datos)
    minuto = int(datos.get("minuto", 0) or 0)
    estado = (estado_partido or {}).get("estado", "FRIO")

    riesgo = 0

    if confianza_prediccion < 70:
        riesgo += 2
    elif confianza_prediccion < 80:
        riesgo += 1

    if valor < 4:
        riesgo += 2
    elif valor < 8:
        riesgo += 1

    if minuto >= 80:
        riesgo += 2
    elif minuto >= 70:
        riesgo += 1

    if estado in ("FRIO", "MUERTO"):
        riesgo += 2
    elif estado == "CONTROLADO":
        riesgo += 1

    if riesgo >= 5:
        return "ALTO"
    if riesgo >= 3:
        return "MEDIO"
    return "BAJO"


def generar_senales_posibles(datos):
    minuto = int(datos.get("minuto", 0) or 0)
    if minuto >= 88:
        return []

    xg = float(datos.get("xG", 0) or 0)
    cuota = float(datos.get("cuota", 1.85) or 1.85)
    valor = calcular_valor(datos)
    prob_real = float(datos.get("prob_real", 0.75) or 0.75)
    prob_implicita = float(datos.get("prob_implicita", 0.54) or 0.54)
    momentum = normalizar_texto(datos.get("momentum"))
    ml = int(datos.get("marcador_local", 0) or 0)
    mv = int(datos.get("marcador_visitante", 0) or 0)
    total_goles = ml + mv

    estado = clasificar_partido(datos)
    gol_inminente = detectar_gol_inminente(datos)
    base = calcular_confianza_base(datos)

    senales = []

    confianza_next_goal = base
    if estado["estado"] in ("EXPLOSIVO", "CAOS"):
        confianza_next_goal += 10
    if gol_inminente["gol_inminente"]:
        confianza_next_goal += 10
    confianza_next_goal = clamp(confianza_next_goal, 45, 95)

    if confianza_next_goal >= 72 and valor > 0:
        tier = clasificar_tier(confianza_next_goal, valor)
        if tier != "DESCARTAR":
            senales.append({
                "mercado": "NEXT_GOAL",
                "apuesta": "Habrá gol (próximo)",
                "linea": None,
                "confianza": confianza_next_goal,
                "valor": valor,
                "cuota": cuota,
                "prob_real": 0.65,
                "prob_implicita": prob_implicita,
                "razon": "Alta presión ofensiva + dinámica explosiva",
                "tier": tier
            })

    confianza_next15 = base
    if xg >= 1.2:
        confianza_next15 += 7
    if momentum in ("ALTO", "MUY ALTO"):
        confianza_next15 += 6
    if estado["estado"] in ("EXPLOSIVO", "CALIENTE", "CAOS"):
        confianza_next15 += 6
    if gol_inminente["gol_inminente"]:
        confianza_next15 += 8
    if 20 <= minuto <= 88:
        confianza_next15 += 5

    confianza_next15 = clamp(confianza_next15, 45, 95)

    if confianza_next15 >= 68 and valor > 0:
        linea = total_goles + 0.5
        tier = clasificar_tier(confianza_next15, valor)
        if tier != "DESCARTAR":
            senales.append({
                "mercado": "OVER_NEXT_15_DYNAMIC",
                "apuesta": f"Over {linea} próximos 15 min",
                "linea": linea,
                "confianza": confianza_next15,
                "valor": valor,
                "cuota": cuota,
                "prob_real": 0.64,
                "prob_implicita": prob_implicita,
                "razon": "Momentum ofensivo + presión + xG",
                "tier": tier
            })

    confianza_over_match = base
    if xg >= 1.5:
        confianza_over_match += 8
    if estado["estado"] == "EXPLOSIVO":
        confianza_over_match += 8
    elif estado["estado"] == "CALIENTE":
        confianza_over_match += 5
    if minuto <= 75:
        confianza_over_match += 5

    confianza_over_match = clamp(confianza_over_match, 45, 95)

    if confianza_over_match >= 70 and valor > 0:
        linea_match = max(1.5, total_goles + 0.5)
        tier = clasificar_tier(confianza_over_match, valor)
        if tier != "DESCARTAR":
            senales.append({
                "mercado": "OVER_MATCH_DYNAMIC",
                "apuesta": f"Over {linea_match} partido",
                "linea": linea_match,
                "confianza": confianza_over_match,
                "valor": valor,
                "cuota": cuota,
                "prob_real": prob_real,
                "prob_implicita": prob_implicita,
                "razon": "xG acumulado favorable para más goles en el partido",
                "tier": tier
            })

    confianza_hold = 50
    if momentum in ("BAJO", "MEDIO"):
        confianza_hold += 10
    if xg < 1.2:
        confianza_hold += 10
    if estado["estado"] in ("FRIO", "CONTROLADO"):
        confianza_hold += 8
    if minuto >= 70:
        confianza_hold += 7

    confianza_hold = clamp(confianza_hold, 40, 95)

    if confianza_hold >= 72 and valor > 0:
        tier = clasificar_tier(confianza_hold, valor)
        if tier != "DESCARTAR":
            senales.append({
                "mercado": "RESULT_HOLDS_NEXT_15",
                "apuesta": "Se mantiene el resultado próximos 15 min",
                "linea": None,
                "confianza": confianza_hold,
                "valor": valor,
                "cuota": cuota,
                "prob_real": 0.62,
                "prob_implicita": prob_implicita,
                "razon": "Ritmo controlado + ventana final + menor impulso ofensivo",
                "tier": tier
            })

    return senales


def elegir_mejor_senal(senales):
    if not senales:
        return None

    prioridad_tier = {
        "PREMIUM": 3,
        "FUERTE": 2,
        "NORMAL": 1
    }

    return sorted(
        senales,
        key=lambda s: (
            prioridad_tier.get(s.get("tier", "NORMAL"), 0),
            s.get("confianza", 0),
            s.get("valor", 0)
        ),
        reverse=True
    )[0]


def generar_senal(datos):
    estado = clasificar_partido(datos)
    gol_inminente = detectar_gol_inminente(datos)
    senales = generar_senales_posibles(datos)
    mejor = elegir_mejor_senal(senales)

    total_goles_estimado = estimar_total_goles(datos)
    pred_ganador = predecir_ganador(datos)
    pred_goles = predecir_linea_goles(total_goles_estimado)
    resultado_probable = predecir_resultado_probable(
        datos,
        total_goles_estimado,
        pred_ganador["ganador_probable"]
    )
    riesgo_operativo = calcular_riesgo_operativo(
        datos,
        pred_ganador["confianza_prediccion"],
        estado
    )

    predictor = datos.get("goal_predictor") or {}
    goal_prob_5 = round(float(predictor.get("goal_next_5_prob", 0) or 0) * 100, 2)
    goal_prob_10 = round(float(predictor.get("goal_next_10_prob", 0) or 0) * 100, 2)

    pressure_score = float((datos.get("goal_pressure") or {}).get("pressure_score", 0) or 0)
    chaos_score = float((datos.get("chaos") or {}).get("chaos_score", 0) or 0)
    goal_prob_15 = round(
        clamp((goal_prob_10 / 100) + 0.08 + (pressure_score * 0.01) + (chaos_score * 0.005), 0, 0.97) * 100,
        2
    )

    if mejor is None:
        return {
            "id": datos.get("id", ""),
            "minuto": int(datos.get("minuto", 0) or 0),
            "mercado": "SIN_SEÑAL",
            "apuesta": "Sin oportunidad clara",
            "cuota": float(datos.get("cuota", 1.85) or 1.85),
            "confianza": calcular_confianza_base(datos),
            "valor": calcular_valor(datos),
            "prob_real": float(datos.get("prob_real", 0.75) or 0.75),
            "razon": "No se detectó ventaja suficiente en este momento",
            "tier": "DESCARTAR",
            "estado_partido": estado,
            "gol_inminente": gol_inminente,
            "senales_posibles": [],
            "signal_status": "WAIT",
            "goal_prob_5": goal_prob_5,
            "goal_prob_10": goal_prob_10,
            "goal_prob_15": goal_prob_15,
            "resultado_probable": resultado_probable,
            "ganador_probable": pred_ganador["ganador_probable"],
            "doble_oportunidad_probable": pred_ganador["doble_oportunidad_probable"],
            "total_goles_estimado": total_goles_estimado,
            "linea_goles_probable": pred_goles["linea_goles_probable"],
            "over_under_probable": pred_goles["over_under_probable"],
            "confianza_prediccion": pred_ganador["confianza_prediccion"],
            "recomendacion_final": "OBSERVAR",
            "riesgo_operativo": riesgo_operativo
        }

    resultado = dict(mejor)
    resultado["id"] = datos.get("id", "")
    resultado["minuto"] = int(datos.get("minuto", 0) or 0)
    resultado["estado_partido"] = estado
    resultado["gol_inminente"] = gol_inminente
    resultado["signal_status"] = "OPEN"
    resultado["goal_prob_5"] = goal_prob_5
    resultado["goal_prob_10"] = goal_prob_10
    resultado["goal_prob_15"] = goal_prob_15
    resultado["resultado_probable"] = resultado_probable
    resultado["ganador_probable"] = pred_ganador["ganador_probable"]
    resultado["doble_oportunidad_probable"] = pred_ganador["doble_oportunidad_probable"]
    resultado["total_goles_estimado"] = total_goles_estimado
    resultado["linea_goles_probable"] = pred_goles["linea_goles_probable"]
    resultado["over_under_probable"] = pred_goles["over_under_probable"]
    resultado["confianza_prediccion"] = pred_ganador["confianza_prediccion"]
    resultado["recomendacion_final"] = "APOSTAR"
    resultado["riesgo_operativo"] = riesgo_operativo

    resultado["senales_posibles"] = [
        {
            "mercado": s.get("mercado"),
            "apuesta": s.get("apuesta"),
            "linea": s.get("linea"),
            "confianza": s.get("confianza"),
            "valor": s.get("valor"),
            "cuota": s.get("cuota"),
            "razon": s.get("razon"),
            "tier": s.get("tier")
        }
        for s in senales
    ]

    return resultado

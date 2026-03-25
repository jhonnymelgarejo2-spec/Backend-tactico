from engines.value_engine import evaluar_value


def normalizar_texto(valor):
    return str(valor or "").strip().upper()


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def safe_float(valor, default=0.0):
    try:
        if valor is None or valor == "":
            return default
        return float(valor)
    except Exception:
        return default


def safe_int(valor, default=0):
    try:
        if valor is None or valor == "":
            return default
        return int(float(valor))
    except Exception:
        return default


def calcular_valor(datos):
    prob_real = safe_float(datos.get("prob_real", 0.75), 0.75)
    prob_implicita = safe_float(datos.get("prob_implicita", 0.54), 0.54)
    return round((prob_real - prob_implicita) * 100, 2)


def calcular_confianza_base(datos):
    momentum = normalizar_texto(datos.get("momentum"))
    xg = safe_float(datos.get("xG", 0), 0.0)
    minuto = safe_int(datos.get("minuto", 0), 0)

    shots = safe_int(datos.get("shots", 0), 0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)

    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    chaos_score = safe_float((datos.get("chaos") or {}).get("chaos_score", 0), 0.0)
    goal5 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0), 0.0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)

    confianza = 50

    if momentum == "MUY ALTO":
        confianza += 14
    elif momentum == "ALTO":
        confianza += 10
    elif momentum == "MEDIO":
        confianza += 5

    if xg >= 2.5:
        confianza += 14
    elif xg >= 1.8:
        confianza += 10
    elif xg >= 1.2:
        confianza += 7
    elif xg >= 0.8:
        confianza += 4

    if shots >= 10:
        confianza += 5
    elif shots >= 7:
        confianza += 3

    if shots_on_target >= 5:
        confianza += 7
    elif shots_on_target >= 3:
        confianza += 4
    elif shots_on_target >= 1:
        confianza += 2

    if dangerous_attacks >= 28:
        confianza += 6
    elif dangerous_attacks >= 18:
        confianza += 4
    elif dangerous_attacks >= 10:
        confianza += 2

    if pressure_score >= 8:
        confianza += 5
    elif pressure_score >= 5:
        confianza += 3

    if goal5 >= 0.70:
        confianza += 6
    elif goal5 >= 0.50:
        confianza += 3

    if goal10 >= 0.75:
        confianza += 4
    elif goal10 >= 0.55:
        confianza += 2

    if chaos_score >= 9:
        confianza += 2
    elif chaos_score >= 12:
        confianza += 3

    if 15 <= minuto <= 35:
        confianza += 3
    elif 36 <= minuto <= 75:
        confianza += 6
    elif 76 <= minuto <= 88:
        confianza += 5

    return clamp(confianza, 40, 95)


def clasificar_partido(datos):
    xg = safe_float(datos.get("xG", 0), 0.0)
    momentum = normalizar_texto(datos.get("momentum"))
    minuto = safe_int(datos.get("minuto", 0), 0)
    ml = safe_int(datos.get("marcador_local", 0), 0)
    mv = safe_int(datos.get("marcador_visitante", 0), 0)
    diff = abs(ml - mv)

    shots = safe_int(datos.get("shots", 0), 0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)

    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    chaos_score = safe_float((datos.get("chaos") or {}).get("chaos_score", 0), 0.0)
    goal5 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0), 0.0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)

    score = 0

    if xg >= 2.5:
        score += 4
    elif xg >= 1.8:
        score += 3
    elif xg >= 1.2:
        score += 2
    elif xg >= 0.8:
        score += 1

    if shots >= 12:
        score += 3
    elif shots >= 8:
        score += 2
    elif shots >= 5:
        score += 1

    if shots_on_target >= 5:
        score += 4
    elif shots_on_target >= 3:
        score += 3
    elif shots_on_target >= 1:
        score += 1

    if dangerous_attacks >= 28:
        score += 4
    elif dangerous_attacks >= 18:
        score += 3
    elif dangerous_attacks >= 10:
        score += 1

    if momentum == "MUY ALTO":
        score += 4
    elif momentum == "ALTO":
        score += 3
    elif momentum == "MEDIO":
        score += 1

    if pressure_score >= 8:
        score += 3
    elif pressure_score >= 5:
        score += 2

    if chaos_score >= 12:
        score += 3
    elif chaos_score >= 8:
        score += 2
    elif chaos_score >= 5:
        score += 1

    if goal5 >= 0.75:
        score += 4
    elif goal5 >= 0.55:
        score += 2
    elif goal5 >= 0.35:
        score += 1

    if goal10 >= 0.80:
        score += 2
    elif goal10 >= 0.60:
        score += 1

    if diff == 0:
        score += 2
    elif diff == 1:
        score += 1

    if chaos_score >= 12 and pressure_score >= 8 and shots_on_target >= 4:
        return {
            "estado": "CAOS",
            "score_estado": score,
            "razon": "Partido roto con intercambio constante de ataques"
        }

    if minuto >= 85 and xg < 1.0 and momentum in ("BAJO", "MEDIO") and shots_on_target <= 1:
        return {
            "estado": "MUERTO",
            "score_estado": score,
            "razon": "Ritmo bajo y poco potencial ofensivo en tramo final"
        }

    if score >= 18:
        return {
            "estado": "EXPLOSIVO",
            "score_estado": score,
            "razon": "Alta probabilidad de cambio fuerte en el marcador o de otro gol pronto"
        }

    if score >= 12:
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
    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    chaos_score = safe_float((datos.get("chaos") or {}).get("chaos_score", 0), 0.0)
    goal5 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0), 0.0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)
    momentum = normalizar_texto(datos.get("momentum"))
    xg = safe_float(datos.get("xG", 0), 0.0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)

    score = 0

    if goal5 >= 0.85:
        score += 5
    elif goal5 >= 0.70:
        score += 4
    elif goal5 >= 0.55:
        score += 3
    elif goal5 >= 0.40:
        score += 2

    if goal10 >= 0.90:
        score += 3
    elif goal10 >= 0.78:
        score += 2
    elif goal10 >= 0.60:
        score += 1

    if pressure_score >= 8:
        score += 3
    elif pressure_score >= 5:
        score += 2

    if chaos_score >= 10:
        score += 3
    elif chaos_score >= 7:
        score += 2

    if momentum in ("ALTO", "MUY ALTO"):
        score += 2

    if xg >= 2.2:
        score += 2
    elif xg >= 1.4:
        score += 1

    if shots_on_target >= 4:
        score += 2
    elif shots_on_target >= 2:
        score += 1

    if dangerous_attacks >= 20:
        score += 1

    es_gol = score >= 9

    return {
        "gol_inminente": es_gol,
        "score_gol_inminente": score,
        "label": "GOL MUY PROBABLE" if es_gol else "SIN ALERTA",
        "razon": "Probabilidad inmediata elevada por predictor + presión + contexto" if es_gol else "No se detecta gol inminente claro"
    }


def clasificar_tier(confianza, valor, value_categoria="SIN_VALUE"):
    if confianza >= 88 and valor >= 10:
        return "PREMIUM"

    if confianza >= 80 and valor >= 8:
        return "TOP"

    if confianza >= 74 and valor >= 4:
        return "FUERTE"

    if confianza >= 68 and valor >= 1.5:
        return "NORMAL"

    return "DESCARTAR"


def estimar_total_goles(datos):
    ml = safe_int(datos.get("marcador_local", 0), 0)
    mv = safe_int(datos.get("marcador_visitante", 0), 0)
    goles_actuales = ml + mv

    xg = safe_float(datos.get("xG", 0), 0.0)
    minuto = safe_int(datos.get("minuto", 0), 0)
    momentum = normalizar_texto(datos.get("momentum"))
    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    chaos_score = safe_float((datos.get("chaos") or {}).get("chaos_score", 0), 0.0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)

    extra = 0.0

    if xg >= 3.0:
        extra += 1.3
    elif xg >= 2.3:
        extra += 1.0
    elif xg >= 1.6:
        extra += 0.75
    elif xg >= 1.0:
        extra += 0.45
    else:
        extra += 0.15

    if momentum == "MUY ALTO":
        extra += 0.40
    elif momentum == "ALTO":
        extra += 0.28
    elif momentum == "MEDIO":
        extra += 0.12

    if pressure_score >= 8:
        extra += 0.35
    elif pressure_score >= 5:
        extra += 0.20

    if chaos_score >= 10:
        extra += 0.30
    elif chaos_score >= 6:
        extra += 0.15

    if goal10 >= 0.80:
        extra += 0.40
    elif goal10 >= 0.65:
        extra += 0.22

    if shots_on_target >= 5:
        extra += 0.30
    elif shots_on_target >= 3:
        extra += 0.18

    if minuto >= 80:
        extra -= 0.10
    elif minuto <= 20:
        extra += 0.15

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
    if total_estimado >= 2.2:
        return {
            "linea_goles_probable": "UNDER_3_5",
            "over_under_probable": "UNDER 3.5"
        }
    return {
        "linea_goles_probable": "UNDER_2_5",
        "over_under_probable": "UNDER 2.5"
    }


def predecir_ganador(datos):
    ml = safe_int(datos.get("marcador_local", 0), 0)
    mv = safe_int(datos.get("marcador_visitante", 0), 0)
    momentum = normalizar_texto(datos.get("momentum"))
    xg = safe_float(datos.get("xG", 0), 0.0)
    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    chaos_score = safe_float((datos.get("chaos") or {}).get("chaos_score", 0), 0.0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)

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

    if shots_on_target >= 4:
        score_local += 0.35
    elif shots_on_target >= 2:
        score_local += 0.15

    if chaos_score >= 8:
        score_local += 0.12
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
    ml = safe_int(datos.get("marcador_local", 0), 0)
    mv = safe_int(datos.get("marcador_visitante", 0), 0)
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
    minuto = safe_int(datos.get("minuto", 0), 0)
    estado = (estado_partido or {}).get("estado", "FRIO")

    riesgo = 0

    if confianza_prediccion < 70:
        riesgo += 2
    elif confianza_prediccion < 80:
        riesgo += 1

    if valor < 2:
        riesgo += 2
    elif valor < 6:
        riesgo += 1

    if minuto >= 85:
        riesgo += 2
    elif minuto >= 75:
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


def enriquecer_con_value(senal):
    value_data = evaluar_value(
        senal.get("prob_real", 0.0),
        senal.get("cuota", 0.0)
    )

    senal["prob_implicita_calculada"] = value_data["prob_implicita"]
    senal["value_pct"] = value_data["value_pct"]
    senal["edge_pct"] = value_data["edge_pct"]
    senal["value_score"] = value_data["value_score"]
    senal["value_categoria"] = value_data["value_categoria"]
    senal["recomendacion_value"] = value_data["recomendacion_value"]
    senal["razon_value"] = value_data["razon_value"]

    return senal


def generar_senales_posibles(datos):
    minuto = safe_int(datos.get("minuto", 0), 0)
    if minuto >= 89:
        return []

    xg = safe_float(datos.get("xG", 0), 0.0)
    cuota = safe_float(datos.get("cuota", 1.85), 1.85)
    valor = calcular_valor(datos)
    prob_real = safe_float(datos.get("prob_real", 0.75), 0.75)
    prob_implicita = safe_float(datos.get("prob_implicita", 0.54), 0.54)
    momentum = normalizar_texto(datos.get("momentum"))
    ml = safe_int(datos.get("marcador_local", 0), 0)
    mv = safe_int(datos.get("marcador_visitante", 0), 0)
    total_goles = ml + mv

    shots = safe_int(datos.get("shots", 0), 0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)
    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    goal5 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0), 0.0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)

    estado = clasificar_partido(datos)
    gol_inminente = detectar_gol_inminente(datos)
    base = calcular_confianza_base(datos)

    senales = []

    # =====================================================
    # NEXT GOAL
    # =====================================================
    confianza_next_goal = base
    if estado["estado"] in ("EXPLOSIVO", "CAOS", "CALIENTE"):
        confianza_next_goal += 7
    if gol_inminente["gol_inminente"]:
        confianza_next_goal += 9
    if goal5 >= 0.55:
        confianza_next_goal += 6
    if shots_on_target >= 3:
        confianza_next_goal += 4
    if dangerous_attacks >= 18:
        confianza_next_goal += 3
    if 25 <= minuto <= 82:
        confianza_next_goal += 3

    confianza_next_goal = clamp(confianza_next_goal, 45, 95)

    if confianza_next_goal >= 70 and valor >= 1:
        senal = {
            "mercado": "NEXT_GOAL",
            "apuesta": "Habrá gol (próximo)",
            "linea": None,
            "confianza": confianza_next_goal,
            "valor": valor,
            "cuota": cuota,
            "prob_real": max(0.62, prob_real),
            "prob_implicita": prob_implicita,
            "razon": "Alta presión ofensiva + dinámica de gol próxima",
        }
        senal = enriquecer_con_value(senal)
        senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
        if senal["tier"] != "DESCARTAR":
            senales.append(senal)

    # =====================================================
    # OVER NEXT 15
    # =====================================================
    confianza_next15 = base
    if xg >= 1.2:
        confianza_next15 += 6
    if momentum in ("ALTO", "MUY ALTO"):
        confianza_next15 += 5
    if estado["estado"] in ("EXPLOSIVO", "CALIENTE", "CAOS"):
        confianza_next15 += 5
    if gol_inminente["gol_inminente"]:
        confianza_next15 += 6
    if shots_on_target >= 3:
        confianza_next15 += 3
    if 20 <= minuto <= 85:
        confianza_next15 += 4

    confianza_next15 = clamp(confianza_next15, 45, 95)

    if confianza_next15 >= 69 and valor >= 1:
        linea = total_goles + 0.5
        senal = {
            "mercado": "OVER_NEXT_15_DYNAMIC",
            "apuesta": f"Over {linea} próximos 15 min",
            "linea": linea,
            "confianza": confianza_next15,
            "valor": valor,
            "cuota": cuota,
            "prob_real": max(0.61, prob_real),
            "prob_implicita": prob_implicita,
            "razon": "Momentum ofensivo + presión + ventana operativa",
        }
        senal = enriquecer_con_value(senal)
        senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
        if senal["tier"] != "DESCARTAR":
            senales.append(senal)

    # =====================================================
    # OVER PARTIDO
    # =====================================================
    confianza_over_match = base
    if xg >= 1.5:
        confianza_over_match += 7
    if estado["estado"] == "EXPLOSIVO":
        confianza_over_match += 8
    elif estado["estado"] == "CALIENTE":
        confianza_over_match += 5
    if goal10 >= 0.60:
        confianza_over_match += 4
    if total_goles <= 2:
        confianza_over_match += 2
    if minuto <= 78:
        confianza_over_match += 4

    confianza_over_match = clamp(confianza_over_match, 45, 95)

    if confianza_over_match >= 71 and valor >= 1:
        linea_match = max(1.5, total_goles + 0.5)
        senal = {
            "mercado": "OVER_MATCH_DYNAMIC",
            "apuesta": f"Over {linea_match} partido",
            "linea": linea_match,
            "confianza": confianza_over_match,
            "valor": valor,
            "cuota": cuota,
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "razon": "xG acumulado favorable para más goles en el partido",
        }
        senal = enriquecer_con_value(senal)
        senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
        if senal["tier"] != "DESCARTAR":
            senales.append(senal)

    # =====================================================
    # UNDER PARTIDO
    # =====================================================
    confianza_under_match = 48
    if momentum in ("BAJO", "MEDIO"):
        confianza_under_match += 8
    if xg < 1.15:
        confianza_under_match += 10
    elif xg < 1.5:
        confianza_under_match += 4
    if shots_on_target <= 2:
        confianza_under_match += 6
    if dangerous_attacks < 14:
        confianza_under_match += 4
    if estado["estado"] in ("FRIO", "CONTROLADO", "MUERTO"):
        confianza_under_match += 7
    if 55 <= minuto <= 85:
        confianza_under_match += 5

    confianza_under_match = clamp(confianza_under_match, 40, 95)

    if confianza_under_match >= 72 and valor >= 1:
        linea_under = max(2.5, total_goles + 0.5)
        senal = {
            "mercado": "UNDER_MATCH_DYNAMIC",
            "apuesta": f"Under {linea_under} partido",
            "linea": linea_under,
            "confianza": confianza_under_match,
            "valor": valor,
            "cuota": cuota,
            "prob_real": max(0.60, prob_real),
            "prob_implicita": prob_implicita,
            "razon": "Ritmo controlado + baja producción ofensiva + contexto de cierre",
        }
        senal = enriquecer_con_value(senal)
        senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
        if senal["tier"] != "DESCARTAR":
            senales.append(senal)

    # =====================================================
    # RESULT HOLDS NEXT 15
    # =====================================================
    confianza_hold = 50
    if momentum in ("BAJO", "MEDIO"):
        confianza_hold += 9
    if xg < 1.25:
        confianza_hold += 8
    if shots_on_target <= 2:
        confianza_hold += 5
    if estado["estado"] in ("FRIO", "CONTROLADO", "MUERTO"):
        confianza_hold += 8
    if minuto >= 68:
        confianza_hold += 8
    if goal5 < 0.35:
        confianza_hold += 4
    if goal10 < 0.55:
        confianza_hold += 3

    confianza_hold = clamp(confianza_hold, 40, 95)

    if confianza_hold >= 72 and valor >= 1:
        senal = {
            "mercado": "RESULT_HOLDS_NEXT_15",
            "apuesta": "Se mantiene el resultado próximos 15 min",
            "linea": None,
            "confianza": confianza_hold,
            "valor": valor,
            "cuota": cuota,
            "prob_real": max(0.60, prob_real),
            "prob_implicita": prob_implicita,
            "razon": "Ritmo controlado + ventana final + menor impulso ofensivo",
        }
        senal = enriquecer_con_value(senal)
        senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
        if senal["tier"] != "DESCARTAR":
            senales.append(senal)

    return senales


def score_mercado(senal, datos, estado, gol_inminente):
    mercado = senal.get("mercado")
    confianza = safe_float(senal.get("confianza", 0), 0.0)
    valor = safe_float(senal.get("valor", 0), 0.0)
    value_score = safe_float(senal.get("value_score", 0), 0.0)
    minuto = safe_int(datos.get("minuto", 0), 0)
    xg = safe_float(datos.get("xG", 0), 0.0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    goal5 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0), 0.0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)

    score = 0.0
    score += confianza * 1.25
    score += valor * 2.20
    score += value_score * 1.30

    if mercado == "NEXT_GOAL":
        if gol_inminente.get("gol_inminente"):
            score += 18
        if estado["estado"] in ("EXPLOSIVO", "CAOS", "CALIENTE"):
            score += 12
        if goal5 >= 0.55:
            score += 10
        if shots_on_target >= 3:
            score += 6
        if 25 <= minuto <= 82:
            score += 4

    elif mercado == "OVER_NEXT_15_DYNAMIC":
        if estado["estado"] in ("EXPLOSIVO", "CALIENTE", "CAOS"):
            score += 12
        if goal10 >= 0.60:
            score += 8
        if xg >= 1.4:
            score += 6
        if 20 <= minuto <= 85:
            score += 5

    elif mercado == "OVER_MATCH_DYNAMIC":
        if xg >= 1.6:
            score += 9
        if estado["estado"] in ("EXPLOSIVO", "CALIENTE"):
            score += 8
        if minuto <= 78:
            score += 5

    elif mercado == "UNDER_MATCH_DYNAMIC":
        if estado["estado"] in ("FRIO", "CONTROLADO", "MUERTO"):
            score += 12
        if xg < 1.2:
            score += 10
        if shots_on_target <= 2:
            score += 6
        if minuto >= 55:
            score += 5

    elif mercado == "RESULT_HOLDS_NEXT_15":
        if estado["estado"] in ("FRIO", "CONTROLADO", "MUERTO"):
            score += 12
        if minuto >= 68:
            score += 8
        if goal5 < 0.35:
            score += 6
        if xg < 1.3:
            score += 5

    return round(score, 2)


def elegir_mejor_senal(senales, datos, estado, gol_inminente):
    if not senales:
        return None

    enriquecidas = []
    for s in senales:
        s2 = dict(s)
        s2["_market_score"] = score_mercado(s2, datos, estado, gol_inminente)
        enriquecidas.append(s2)

    return sorted(
        enriquecidas,
        key=lambda s: (
            float(s.get("_market_score", 0) or 0),
            float(s.get("value_score", 0) or 0),
            float(s.get("confianza", 0) or 0),
            float(s.get("valor", 0) or 0)
        ),
        reverse=True
    )[0]


def generar_senal(datos):
    estado = clasificar_partido(datos)
    gol_inminente = detectar_gol_inminente(datos)
    senales = generar_senales_posibles(datos)
    mejor = elegir_mejor_senal(senales, datos, estado, gol_inminente)

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
    goal_prob_5 = round(safe_float(predictor.get("goal_next_5_prob", 0), 0.0) * 100, 2)
    goal_prob_10 = round(safe_float(predictor.get("goal_next_10_prob", 0), 0.0) * 100, 2)

    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    chaos_score = safe_float((datos.get("chaos") or {}).get("chaos_score", 0), 0.0)
    goal_prob_15 = round(
        clamp((goal_prob_10 / 100) + 0.08 + (pressure_score * 0.01) + (chaos_score * 0.005), 0, 0.97) * 100,
        2
    )

    if mejor is None:
        return {
            "id": datos.get("id", ""),
            "minuto": safe_int(datos.get("minuto", 0), 0),
            "mercado": "SIN_SEÑAL",
            "apuesta": "Sin oportunidad clara",
            "cuota": safe_float(datos.get("cuota", 1.85), 1.85),
            "confianza": calcular_confianza_base(datos),
            "valor": calcular_valor(datos),
            "prob_real": safe_float(datos.get("prob_real", 0.75), 0.75),
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
            "riesgo_operativo": riesgo_operativo,
            "prob_implicita_calculada": 0.0,
            "value_pct": 0.0,
            "edge_pct": 0.0,
            "value_score": 0.0,
            "value_categoria": "SIN_VALUE",
            "recomendacion_value": "NO_APOSTAR",
            "razon_value": "No se detectó value suficiente"
        }

    resultado = dict(mejor)
    resultado.pop("_market_score", None)

    resultado["id"] = datos.get("id", "")
    resultado["minuto"] = safe_int(datos.get("minuto", 0), 0)
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
            "tier": s.get("tier"),
            "value_pct": s.get("value_pct"),
            "value_score": s.get("value_score"),
            "value_categoria": s.get("value_categoria"),
            "recomendacion_value": s.get("recomendacion_value")
        }
        for s in senales
    ]

    return resultado

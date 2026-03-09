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


def generar_senales_posibles(datos):
    minuto = int(datos.get("minuto", 0) or 0)
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

    # OVER DINAMICO PROX 15
    confianza_next15 = base
    if xg >= 1.2:
        confianza_next15 += 7
    if momentum in ("ALTO", "MUY ALTO"):
        confianza_next15 += 6
    if estado["estado"] in ("EXPLOSIVO", "CALIENTE"):
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
                "prob_real": prob_real,
                "prob_implicita": prob_implicita,
                "razon": "Momentum alto + presión ofensiva + ventana favorable",
                "tier": tier
            })

    # OVER PARTIDO DINAMICO
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

    # RESULTADO SE MANTIENE
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
                "prob_real": prob_real,
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
            "senales_posibles": []
        }

    resultado = dict(mejor)
    resultado["id"] = datos.get("id", "")
    resultado["minuto"] = int(datos.get("minuto", 0) or 0)
    resultado["estado_partido"] = estado
    resultado["gol_inminente"] = gol_inminente
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

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


# ==============================
# CLASIFICACION DEL PARTIDO
# ==============================

def clasificar_partido(datos):

    xg = float(datos.get("xG", 0) or 0)
    momentum = normalizar_texto(datos.get("momentum"))
    minuto = int(datos.get("minuto", 0) or 0)

    pressure_score = float((datos.get("goal_pressure") or {}).get("pressure_score", 0) or 0)
    chaos_score = float((datos.get("chaos") or {}).get("chaos_score", 0) or 0)

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

    if chaos_score >= 14 and pressure_score >= 10:
        return {
            "estado": "CAOS",
            "score_estado": score,
            "razon": "Partido roto con intercambio constante de ataques"
        }

    if minuto >= 85 and xg < 1.0:
        return {
            "estado": "MUERTO",
            "score_estado": score,
            "razon": "Tramo final sin presión ofensiva clara"
        }

    if score >= 16:
        return {
            "estado": "EXPLOSIVO",
            "score_estado": score,
            "razon": "Alta probabilidad de cambios en el marcador"
        }

    if score >= 11:
        return {
            "estado": "CALIENTE",
            "score_estado": score,
            "razon": "Presión ofensiva notable"
        }

    if score >= 7:
        return {
            "estado": "CONTROLADO",
            "score_estado": score,
            "razon": "Actividad moderada"
        }

    return {
        "estado": "FRIO",
        "score_estado": score,
        "razon": "Pocas señales ofensivas"
    }


# ==============================
# DETECTOR DE GOL
# ==============================

def detectar_gol_inminente(datos):

    pressure_score = float((datos.get("goal_pressure") or {}).get("pressure_score", 0) or 0)
    chaos_score = float((datos.get("chaos") or {}).get("chaos_score", 0) or 0)
    goal5 = float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0) or 0)

    score = 0

    if goal5 >= 0.85:
        score += 5
    elif goal5 >= 0.75:
        score += 4
    elif goal5 >= 0.65:
        score += 3

    if pressure_score >= 10:
        score += 3
    elif pressure_score >= 8:
        score += 2

    if chaos_score >= 12:
        score += 3
    elif chaos_score >= 9:
        score += 2

    es_gol = score >= 9

    return {
        "gol_inminente": es_gol,
        "score_gol_inminente": score,
        "label": "GOL MUY PROBABLE" if es_gol else "SIN ALERTA",
    }


# ==============================
# EQUIPO CON MAS PELIGRO
# ==============================

def detectar_equipo_peligro(datos):

    pressure = datos.get("goal_pressure", {})
    predictor = datos.get("goal_predictor", {})

    home_pressure = float(pressure.get("home_pressure", pressure.get("pressure_score", 0)))
    away_pressure = float(pressure.get("away_pressure", pressure.get("pressure_score", 0)))

    home_prob = float(predictor.get("home_goal_prob", 0.50))
    away_prob = float(predictor.get("away_goal_prob", 0.50))

    home_score = home_pressure + (home_prob * 10)
    away_score = away_pressure + (away_prob * 10)

    if home_score > away_score + 2:
        return "HOME"

    if away_score > home_score + 2:
        return "AWAY"

    return "EQUILIBRADO"


# ==============================
# DETECTOR REMONTADA
# ==============================

def detectar_remontada(datos):

    ml = int(datos.get("marcador_local", 0))
    mv = int(datos.get("marcador_visitante", 0))

    momentum = normalizar_texto(datos.get("momentum"))
    xg = float(datos.get("xG", 0))

    if ml < mv and momentum in ("ALTO", "MUY ALTO") and xg > 1.6:
        return {
            "remontada_posible": True,
            "equipo": "LOCAL"
        }

    if mv < ml and momentum in ("ALTO", "MUY ALTO") and xg > 1.6:
        return {
            "remontada_posible": True,
            "equipo": "VISITANTE"
        }

    return {
        "remontada_posible": False
    }


# ==============================
# CLASIFICACION TIER
# ==============================

def clasificar_tier(confianza, valor):

    if confianza >= 90 and valor >= 10:
        return "PREMIUM"

    if confianza >= 80 and valor >= 6:
        return "FUERTE"

    if confianza >= 70 and valor >= 2:
        return "NORMAL"

    return "DESCARTAR"


# ==============================
# GENERAR MERCADOS
# ==============================

def generar_senales_posibles(datos):

    minuto = int(datos.get("minuto", 0) or 0)

    if minuto >= 88:
        return []

    xg = float(datos.get("xG", 0) or 0)
    cuota = float(datos.get("cuota", 1.85) or 1.85)

    ml = int(datos.get("marcador_local", 0) or 0)
    mv = int(datos.get("marcador_visitante", 0) or 0)

    total_goles = ml + mv

    valor = calcular_valor(datos)

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
                "prob_implicita": 0.54,
                "razon": "Alta presión ofensiva + dinámica explosiva",
                "tier": tier
            })

    confianza_next15 = base

    if xg >= 1.2:
        confianza_next15 += 7

    if estado["estado"] in ("EXPLOSIVO", "CALIENTE", "CAOS"):
        confianza_next15 += 6

    if gol_inminente["gol_inminente"]:
        confianza_next15 += 8

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
                "prob_implicita": 0.54,
                "razon": "Momentum ofensivo + presión + xG",
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

    equipo_peligro = detectar_equipo_peligro(datos)
    remontada = detectar_remontada(datos)

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
            "razon": "No se detectó ventaja suficiente",
            "tier": "DESCARTAR",
            "estado_partido": estado,
            "gol_inminente": gol_inminente,
            "equipo_con_mas_peligro": equipo_peligro,
            "remontada": remontada,
            "senales_posibles": []
        }

    resultado = dict(mejor)

    resultado["id"] = datos.get("id", "")
    resultado["minuto"] = int(datos.get("minuto", 0) or 0)

    resultado["estado_partido"] = estado
    resultado["gol_inminente"] = gol_inminente
    resultado["equipo_con_mas_peligro"] = equipo_peligro
    resultado["remontada"] = remontada

    resultado["senales_posibles"] = senales

    return resultado

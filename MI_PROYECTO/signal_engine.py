# signal_engine.py

from engines.value_engine import evaluar_value as evaluar_value_engine
import config


# =========================================================
# HELPERS
# =========================================================
def normalizar_texto(valor):
    return str(valor or "").strip().upper()


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


def safe_float(valor, default=0.0):
    try:
        if valor is None or valor == "":
            return default
        if isinstance(valor, str):
            valor = valor.replace("%", "").strip()
        return float(valor)
    except Exception:
        return default


def safe_int(valor, default=0):
    try:
        if valor is None or valor == "":
            return default
        if isinstance(valor, str):
            valor = valor.replace("%", "").strip()
        return int(float(valor))
    except Exception:
        return default


# =========================================================
# HELPERS DE PARTIDO
# =========================================================
def diff_partido(datos):
    ml = safe_int(datos.get("marcador_local", 0), 0)
    mv = safe_int(datos.get("marcador_visitante", 0), 0)
    return abs(ml - mv)


def total_goles_actuales(datos):
    ml = safe_int(datos.get("marcador_local", 0), 0)
    mv = safe_int(datos.get("marcador_visitante", 0), 0)
    return ml + mv


def cuota_en_rango(cuota, minimo=None, maximo=None):
    cuota = safe_float(cuota, 0.0)
    if minimo is None:
        minimo = config.ODD_MIN_GLOBAL
    if maximo is None:
        maximo = config.ODD_MAX_GLOBAL
    return minimo <= cuota <= maximo


def under_es_fragil(total_goles, linea_under):
    try:
        margen = float(linea_under) - float(total_goles)
        return margen <= 1.0
    except Exception:
        return True


# =========================================================
# VALUE / CONFIANZA
# =========================================================
def calcular_valor(datos):
    prob_real = safe_float(datos.get("prob_real", config.DEFAULT_PROB_REAL), config.DEFAULT_PROB_REAL)
    prob_implicita = safe_float(datos.get("prob_implicita", config.DEFAULT_PROB_IMPLICITA), config.DEFAULT_PROB_IMPLICITA)
    return round((prob_real - prob_implicita) * 100, 2)


def calcular_confianza_base(datos):
    momentum = normalizar_texto(datos.get("momentum", config.DEFAULT_MOMENTUM))
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

    if shots >= 12:
        confianza += 5
    elif shots >= 8:
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

    if chaos_score >= 12:
        confianza += 3
    elif chaos_score >= 8:
        confianza += 2

    if 15 <= minuto <= 35:
        confianza += 3
    elif 36 <= minuto <= 75:
        confianza += 6
    elif 76 <= minuto <= 88:
        confianza += 5

    return clamp(confianza, 35, 95)


# =========================================================
# CLASIFICACION DEL PARTIDO
# =========================================================
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


# =========================================================
# GOL INMINENTE
# =========================================================
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


# =========================================================
# TIERS
# =========================================================
def clasificar_tier(confianza, valor, value_categoria="SIN_VALUE"):
    if confianza >= 88 and valor >= 8:
        return "PREMIUM"
    if confianza >= 81 and valor >= 5:
        return "TOP"
    if confianza >= 74 and valor >= 2.5:
        return "FUERTE"
    if confianza >= 60 and valor >= 0.5:
        return "NORMAL"
    return "BAJA"


# =========================================================
# PREDICCIONES AUXILIARES
# =========================================================
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
    minuto = safe_int(datos.get("minuto", 0), 0)
    xg = safe_float(datos.get("xG", 0), 0.0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    diff = ml - mv

    base = diff * 1.8

    if xg >= 2.0:
        base += 0.4 if diff >= 0 else -0.1
    elif xg <= 0.9:
        base -= 0.2

    if shots_on_target >= 4:
        base += 0.3 if diff >= 0 else 0.0

    if minuto >= 75 and abs(diff) == 1:
        base += 0.4 if diff > 0 else -0.4

    if abs(base) <= 0.45:
        return {
            "ganador_probable": "EMPATE",
            "doble_oportunidad_probable": "LOCAL_O_EMPATE",
            "confianza_prediccion": 66
        }

    if base > 0:
        return {
            "ganador_probable": "LOCAL",
            "doble_oportunidad_probable": "LOCAL_O_EMPATE",
            "confianza_prediccion": 72 if abs(base) < 1.2 else 79
        }

    return {
        "ganador_probable": "VISITANTE",
        "doble_oportunidad_probable": "EMPATE_O_VISITANTE",
        "confianza_prediccion": 72 if abs(base) < 1.2 else 79
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


# =========================================================
# RIESGO AUXILIAR INTERNO
# =========================================================
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


def riesgo_operativo_a_score(riesgo_operativo, datos=None, estado_partido=None):
    score = 3.5

    if normalizar_texto(riesgo_operativo) == "BAJO":
        score = 3.2
    elif normalizar_texto(riesgo_operativo) == "MEDIO":
        score = 5.1
    elif normalizar_texto(riesgo_operativo) == "ALTO":
        score = 7.4

    if datos:
        minuto = safe_int(datos.get("minuto", 0), 0)
        xg = safe_float(datos.get("xG", 0), 0.0)
        shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
        dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)

        if minuto >= 84:
            score += 0.8
        elif minuto >= 78:
            score += 0.4

        if xg < 1.0:
            score += 0.5
        if shots_on_target <= 1:
            score += 0.5
        if dangerous_attacks < 10:
            score += 0.4

    if estado_partido:
        estado = normalizar_texto((estado_partido or {}).get("estado", ""))
        if estado in ("FRIO", "MUERTO"):
            score += 0.6
        elif estado in ("EXPLOSIVO", "CAOS"):
            score -= 0.3

    return round(clamp(score, 1.0, 10.0), 2)


# =========================================================
# SCORES
# =========================================================
def calcular_tactical_score(datos, estado_partido=None, gol_inminente=None):
    xg = safe_float(datos.get("xG", 0), 0.0)
    shots = safe_int(datos.get("shots", 0), 0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)
    minuto = safe_int(datos.get("minuto", 0), 0)
    momentum = normalizar_texto(datos.get("momentum"))

    pressure_score = safe_float((datos.get("goal_pressure") or {}).get("pressure_score", 0), 0.0)
    predictor_score = safe_float((datos.get("goal_predictor") or {}).get("predictor_score", 0), 0.0)
    goal5 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_5_prob", 0), 0.0) * 100
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0) * 100
    chaos_score = safe_float((datos.get("chaos") or {}).get("chaos_score", 0), 0.0)

    score = 0.0
    score += xg * 18.0
    score += shots * 0.8
    score += shots_on_target * 4.0
    score += dangerous_attacks * 0.25
    score += pressure_score * 2.5
    score += predictor_score * 2.0
    score += chaos_score * 1.4
    score += goal5 * 0.25
    score += goal10 * 0.15

    if momentum == "MUY ALTO":
        score += 16
    elif momentum == "ALTO":
        score += 11
    elif momentum == "MEDIO":
        score += 5

    if config.is_operable_minute(minuto):
        score += 8 if minuto <= 75 else 5

    if estado_partido:
        estado = normalizar_texto((estado_partido or {}).get("estado", ""))
        if estado == "EXPLOSIVO":
            score += 14
        elif estado == "CALIENTE":
            score += 9
        elif estado == "CONTROLADO":
            score += 4
        elif estado in ("FRIO", "MUERTO"):
            score -= 6

    if gol_inminente and gol_inminente.get("gol_inminente"):
        score += 10

    return round(max(0.0, score), 2)


def calcular_signal_score(senal, datos, estado_partido=None, gol_inminente=None):
    confianza = safe_float(senal.get("confianza", 0), 0.0)
    valor = safe_float(senal.get("valor", 0), 0.0)
    value_score = safe_float(senal.get("value_score", 0), 0.0)
    ai_decision_score = safe_float(senal.get("ai_decision_score", 0), 0.0)
    confianza_prediccion = safe_float(senal.get("confianza_prediccion", 0), 0.0)

    tactical_score = calcular_tactical_score(datos, estado_partido, gol_inminente)
    riesgo_operativo = calcular_riesgo_operativo(datos, confianza_prediccion or confianza, estado_partido or {})
    risk_score = riesgo_operativo_a_score(riesgo_operativo, datos, estado_partido)

    score = 0.0
    score += confianza * 1.30
    score += valor * 2.40
    score += value_score * 1.20
    score += tactical_score * 0.90
    score += confianza_prediccion * 0.55
    score += ai_decision_score * 0.35
    score -= risk_score * 5.00

    return round(score, 2)


def signal_rank_desde_score(signal_score):
    if signal_score >= config.SIGNAL_SCORE_MIN_ELITE:
        return "ELITE"
    if signal_score >= config.SIGNAL_SCORE_MIN_TOP:
        return "TOP"
    if signal_score >= 160:
        return "FUERTE"
    return "NORMAL"


# =========================================================
# VALUE ENGINE
# =========================================================
def enriquecer_con_value(senal):
    value_data = evaluar_value_engine(
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


# =========================================================
# CONSTRUCTORES DE MERCADO
# =========================================================
def build_over_next_15_signal(datos, estado, gol_inminente, base, valor, prob_real, prob_implicita, cuota, total_goles):
    minuto = safe_int(datos.get("minuto", 0), 0)
    xg = safe_float(datos.get("xG", 0), 0.0)
    momentum = normalizar_texto(datos.get("momentum"))
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)

    confianza = base

    if xg >= 1.2:
        confianza += 7
    if momentum in ("ALTO", "MUY ALTO"):
        confianza += 6
    if estado["estado"] in ("EXPLOSIVO", "CALIENTE", "CAOS"):
        confianza += 7
    if gol_inminente["gol_inminente"]:
        confianza += 8
    if shots_on_target >= 3:
        confianza += 4
    if dangerous_attacks >= 18:
        confianza += 3
    if config.OVER_NEXT_15_MIN_MINUTE <= minuto <= config.OVER_NEXT_15_MAX_MINUTE:
        confianza += 4

    confianza = clamp(confianza, 45, 95)

    if confianza < config.OVER_NEXT_15_MIN_CONFIDENCE:
        return None
    if minuto < config.OVER_NEXT_15_MIN_MINUTE or minuto > config.OVER_NEXT_15_MAX_MINUTE:
        return None

    linea = total_goles + 0.5

    senal = {
        "mercado": "OVER_NEXT_15_DYNAMIC",
        "apuesta": f"Over {linea} próximos 15 min",
        "linea": linea,
        "confianza": confianza,
        "valor": valor,
        "cuota": cuota,
        "prob_real": max(0.62, prob_real),
        "prob_implicita": prob_implicita,
        "razon": "Presión real + ritmo alto + ventana operativa",
    }

    senal = enriquecer_con_value(senal)
    senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
    return senal


def build_over_match_signal(datos, estado, gol_inminente, base, valor, prob_real, prob_implicita, cuota, total_goles):
    minuto = safe_int(datos.get("minuto", 0), 0)
    xg = safe_float(datos.get("xG", 0), 0.0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)

    confianza = base

    if xg >= 1.5:
        confianza += 8
    if estado["estado"] == "EXPLOSIVO":
        confianza += 9
    elif estado["estado"] == "CALIENTE":
        confianza += 6
    if goal10 >= 0.60:
        confianza += 5
    if shots_on_target >= 3:
        confianza += 3
    if total_goles <= 2:
        confianza += 3
    if minuto <= config.OVER_MATCH_MAX_MINUTE:
        confianza += 4

    confianza = clamp(confianza, 45, 95)

    if confianza < config.OVER_MATCH_MIN_CONFIDENCE:
        return None
    if minuto < config.OVER_MATCH_MIN_MINUTE or minuto > config.OVER_MATCH_MAX_MINUTE:
        return None

    linea_match = max(1.5, total_goles + 0.5)

    senal = {
        "mercado": "OVER_MATCH_DYNAMIC",
        "apuesta": f"Over {linea_match} partido",
        "linea": linea_match,
        "confianza": confianza,
        "valor": valor,
        "cuota": cuota,
        "prob_real": prob_real,
        "prob_implicita": prob_implicita,
        "razon": "Proyección de más goles por ritmo, xG y contexto",
    }

    senal = enriquecer_con_value(senal)
    senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
    return senal


def build_under_match_signal(datos, estado, gol_inminente, valor, prob_real, prob_implicita, cuota, total_goles):
    minuto = safe_int(datos.get("minuto", 0), 0)
    xg = safe_float(datos.get("xG", 0), 0.0)
    momentum = normalizar_texto(datos.get("momentum"))
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)

    confianza = 44

    if momentum in ("BAJO", "MEDIO"):
        confianza += 6

    if xg < 1.00:
        confianza += 8
    elif xg < 1.25:
        confianza += 4

    if shots_on_target <= 1:
        confianza += 5
    elif shots_on_target == 2:
        confianza += 2

    if dangerous_attacks < 12:
        confianza += 4
    elif dangerous_attacks < 16:
        confianza += 2

    if estado["estado"] in ("FRIO", "MUERTO"):
        confianza += 7
    elif estado["estado"] == "CONTROLADO":
        confianza += 4

    if config.UNDER_MATCH_MIN_MINUTE <= minuto <= 85:
        confianza += 5

    linea_under = max(2.5, total_goles + 0.5)

    if gol_inminente["gol_inminente"]:
        confianza -= 10
    if goal10 >= 0.60:
        confianza -= 7
    if shots_on_target >= 4:
        confianza -= 6
    if dangerous_attacks >= 18:
        confianza -= 6
    if xg >= 1.70:
        confianza -= 7
    if momentum in ("ALTO", "MUY ALTO"):
        confianza -= 4

    if under_es_fragil(total_goles, linea_under):
        confianza -= 12

    if total_goles >= 3 and linea_under <= 3.5:
        confianza -= 15

    if total_goles >= 2 and linea_under <= 2.5:
        confianza -= 16

    confianza = clamp(confianza, 35, 95)

    if confianza < config.UNDER_MATCH_MIN_CONFIDENCE:
        return None
    if minuto < config.UNDER_MATCH_MIN_MINUTE:
        return None

    senal = {
        "mercado": "UNDER_MATCH_DYNAMIC",
        "apuesta": f"Under {linea_under} partido",
        "linea": linea_under,
        "confianza": confianza,
        "valor": valor,
        "cuota": cuota,
        "prob_real": max(0.60, prob_real),
        "prob_implicita": prob_implicita,
        "razon": "Cierre controlado + baja producción ofensiva real",
    }

    senal = enriquecer_con_value(senal)
    senal["tier"] = clasificar_tier(senal["confianza"], senal["valor"], senal["value_categoria"])
    return senal


# =========================================================
# GENERACION DE SENALES POSIBLES
# =========================================================
def generar_senales_posibles(datos):
    minuto = safe_int(datos.get("minuto", 0), 0)
    if minuto >= 89:
        return []

    cuota = safe_float(datos.get("cuota", 0.0), 0.0)
    if cuota <= 0:
        cuota = config.DEFAULT_ODD

    valor = calcular_valor(datos)
    prob_real = safe_float(datos.get("prob_real", config.DEFAULT_PROB_REAL), config.DEFAULT_PROB_REAL)
    prob_implicita = safe_float(datos.get("prob_implicita", config.DEFAULT_PROB_IMPLICITA), config.DEFAULT_PROB_IMPLICITA)
    total_goles = total_goles_actuales(datos)

    estado = clasificar_partido(datos)
    gol_inminente = detectar_gol_inminente(datos)
    base = calcular_confianza_base(datos)

    senales = []

    over_next15 = build_over_next_15_signal(
        datos, estado, gol_inminente, base, valor, prob_real, prob_implicita, cuota, total_goles
    )
    if over_next15:
        senales.append(over_next15)

    over_match = build_over_match_signal(
        datos, estado, gol_inminente, base, valor, prob_real, prob_implicita, cuota, total_goles
    )
    if over_match:
        senales.append(over_match)

    under_match = build_under_match_signal(
        datos, estado, gol_inminente, valor, prob_real, prob_implicita, cuota, total_goles
    )
    if under_match:
        senales.append(under_match)

    return senales


# =========================================================
# SCORE POR MERCADO
# =========================================================
def score_mercado(senal, datos, estado, gol_inminente):
    mercado = senal.get("mercado")
    confianza = safe_float(senal.get("confianza", 0), 0.0)
    valor = safe_float(senal.get("valor", 0), 0.0)
    value_score = safe_float(senal.get("value_score", 0), 0.0)
    minuto = safe_int(datos.get("minuto", 0), 0)
    xg = safe_float(datos.get("xG", 0), 0.0)
    shots_on_target = safe_int(datos.get("shots_on_target", 0), 0)
    dangerous_attacks = safe_int(datos.get("dangerous_attacks", 0), 0)
    goal10 = safe_float((datos.get("goal_predictor") or {}).get("goal_next_10_prob", 0), 0.0)
    total_goles = total_goles_actuales(datos)
    linea = safe_float(senal.get("linea"), 0.0)

    score = 0.0
    score += confianza * 1.25
    score += valor * 2.20
    score += value_score * 1.30

    if mercado == "OVER_NEXT_15_DYNAMIC":
        if estado["estado"] in ("EXPLOSIVO", "CALIENTE", "CAOS"):
            score += 15
        if gol_inminente.get("gol_inminente"):
            score += 12
        if goal10 >= 0.60:
            score += 9
        if xg >= 1.4:
            score += 7
        if shots_on_target >= 3:
            score += 5
        if config.OVER_NEXT_15_MIN_MINUTE <= minuto <= config.OVER_NEXT_15_MAX_MINUTE:
            score += 5

    elif mercado == "OVER_MATCH_DYNAMIC":
        if xg >= 1.6:
            score += 10
        if estado["estado"] in ("EXPLOSIVO", "CALIENTE"):
            score += 9
        if goal10 >= 0.60:
            score += 6
        if minuto <= config.OVER_MATCH_MAX_MINUTE:
            score += 5

    elif mercado == "UNDER_MATCH_DYNAMIC":
        if estado["estado"] in ("FRIO", "CONTROLADO", "MUERTO"):
            score += 12
        if xg < 1.2:
            score += 10
        if shots_on_target <= 2:
            score += 6
        if minuto >= config.UNDER_MATCH_MIN_MINUTE:
            score += 5

        if (goal10 * 100) >= config.UNDER_MATCH_MAX_GOAL_PROB_10:
            score -= 12
        if xg >= config.UNDER_MATCH_MAX_XG:
            score -= 12
        if shots_on_target >= 3:
            score -= 10
        if dangerous_attacks >= config.UNDER_MATCH_MAX_DANGEROUS_ATTACKS:
            score -= 10
        if gol_inminente.get("gol_inminente"):
            score -= 12
        if under_es_fragil(total_goles, linea):
            score -= 15

    return round(score, 2)


# =========================================================
# BALANCE DE MERCADOS
# =========================================================
def aplicar_balance_mercados(senales_ordenadas):
    if not senales_ordenadas:
        return []

    max_por_mercado = {
        "OVER_NEXT_15_DYNAMIC": 2,
        "OVER_MATCH_DYNAMIC": 2,
        "UNDER_MATCH_DYNAMIC": 2,
    }

    usados = {}
    resultado = []

    for senal in senales_ordenadas:
        mercado = senal.get("mercado", "")
        usados.setdefault(mercado, 0)

        limite = max_por_mercado.get(mercado, 2)
        if usados[mercado] >= limite:
            continue

        resultado.append(senal)
        usados[mercado] += 1

        if len(resultado) >= config.PUBLISH_MAX_SIGNALS:
            break

    return resultado


# =========================================================
# GENERADOR PRINCIPAL
# =========================================================
def generar_senal(datos):
    estado = clasificar_partido(datos)
    gol_inminente = detectar_gol_inminente(datos)
    senales = generar_senales_posibles(datos)

    senales_filtradas = [
        s for s in senales
        if s.get("mercado") in config.MARKETS_ALLOWED
    ]

    senales_enriquecidas = []
    for s in senales_filtradas:
        s2 = dict(s)
        s2["_market_score"] = score_mercado(s2, datos, estado, gol_inminente)
        senales_enriquecidas.append(s2)

    senales_ordenadas = sorted(
        senales_enriquecidas,
        key=lambda s: (
            float(s.get("_market_score", 0) or 0),
            float(s.get("value_score", 0) or 0),
            float(s.get("confianza", 0) or 0),
            float(s.get("valor", 0) or 0)
        ),
        reverse=True
    )

    mejor = senales_ordenadas[0] if senales_ordenadas else None

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
        tactical_score = calcular_tactical_score(datos, estado, gol_inminente)
        risk_score = riesgo_operativo_a_score(riesgo_operativo, datos, estado)

        return {
            "id": datos.get("id", ""),
            "minuto": safe_int(datos.get("minuto", 0), 0),
            "mercado": "SIN_SEÑAL",
            "apuesta": "Sin oportunidad clara",
            "cuota": safe_float(datos.get("cuota", config.DEFAULT_ODD), config.DEFAULT_ODD) or config.DEFAULT_ODD,
            "confianza": calcular_confianza_base(datos),
            "valor": calcular_valor(datos),
            "prob_real": safe_float(datos.get("prob_real", config.DEFAULT_PROB_REAL), config.DEFAULT_PROB_REAL),
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
            "risk_score": risk_score,
            "tactical_score": tactical_score,
            "signal_score": 0.0,
            "signal_rank": "NORMAL",
            "ai_decision_score": 0.0,
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

    tactical_score = calcular_tactical_score(datos, estado, gol_inminente)

    base_decision_score = round(
        (safe_float(resultado.get("confianza", 0), 0.0) * 0.65) +
        (safe_float(resultado.get("valor", 0), 0.0) * 1.2) +
        (tactical_score * 0.25),
        2
    )

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
    resultado["recomendacion_final"] = "PENDIENTE_VALIDACION"
    resultado["riesgo_operativo"] = riesgo_operativo

    resultado["tactical_score"] = tactical_score
    resultado["ai_decision_score"] = base_decision_score
    resultado["risk_score"] = riesgo_operativo_a_score(riesgo_operativo, datos, estado)
    resultado["signal_score"] = calcular_signal_score(resultado, datos, estado, gol_inminente)
    resultado["signal_rank"] = signal_rank_desde_score(resultado["signal_score"])

    senales_balanceadas = aplicar_balance_mercados(senales_ordenadas)

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
        for s in senales_balanceadas
    ]

    return resultado

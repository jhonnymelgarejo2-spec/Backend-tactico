# signal_engine.py

# ------------------------------
# Utilidades base
# ------------------------------

def normalizar_texto(valor):
    return str(valor or "").strip().upper()


def clamp(valor, minimo, maximo):
    return max(minimo, min(valor, maximo))


# ------------------------------
# Confianza táctica
# ------------------------------

def calcular_confianza_base(datos):
    momentum = normalizar_texto(datos.get("momentum"))
    xg = float(datos.get("xG", 0) or 0)
    minuto = int(datos.get("minuto", 0) or 0)

    confianza = 50

    if momentum == "ALTO":
        confianza += 12
    elif momentum == "MUY ALTO":
        confianza += 18
    elif momentum == "MEDIO":
        confianza += 5

    if xg >= 2.0:
        confianza += 15
    elif xg >= 1.2:
        confianza += 10
    elif xg >= 0.8:
        confianza += 5

    if 15 <= minuto <= 35:
        confianza += 4
    elif 36 <= minuto <= 75:
        confianza += 7
    elif minuto > 75:
        confianza += 3

    return clamp(confianza, 40, 95)


def calcular_valor(datos):
    prob_real = float(datos.get("prob_real", 0.75) or 0)
    prob_implicita = float(datos.get("prob_implicita", 0.54) or 0)
    return round((prob_real - prob_implicita) * 100, 2)


# ------------------------------
# Detectores por ID
# ------------------------------

def detectar_liga(id_partido):
    texto = normalizar_texto(id_partido)

    if "UEFA" in texto:
        return "Champions League"
    elif "CONMEBOL" in texto:
        return "Copa Libertadores"
    elif "FIFA" in texto:
        return "Fútbol Internacional"
    elif "ATP" in texto:
        return "ATP Tour"
    elif "NBA" in texto:
        return "NBA"
    else:
        return "Liga desconocida"


def detectar_equipos(id_partido: str):
    texto = normalizar_texto(id_partido).replace("_", "-").replace(" ", "-")

    ligas = {
        "FIFA": {
            "FINAL-2025": ("Brasil", "Argentina"),
            "GRUPO-2025": ("Francia", "Alemania"),
            "SEMIS-2025": ("España", "Inglaterra")
        },
        "UEFA": {
            "FINAL-2025": ("Real Madrid", "Manchester City"),
            "SF-2025": ("Bayern Munich", "PSG"),
            "QF-2025": ("Chelsea", "Barcelona"),
            "2025": ("España", "Italia")
        },
        "CONMEBOL": {
            "FINAL-2025": ("Boca Juniors", "Palmeiras"),
            "SF-2025": ("Flamengo", "River Plate"),
            "GRUPO-2025": ("Colo-Colo", "Atlético Nacional")
        },
        "ATP": {
            "2025-001": ("Djokovic", "Alcaraz"),
            "2025-002": ("Medvedev", "Sinner")
        },
        "NBA": {
            "2025-001": ("Lakers", "Warriors"),
            "2025-002": ("Celtics", "Heat")
        }
    }

    partes = texto.split("-", 1)
    if len(partes) != 2:
        return ("Equipo A", "Equipo B")

    prefijo, sufijo = partes
    liga = ligas.get(prefijo)
    if liga:
        return liga.get(sufijo, ("Equipo A", "Equipo B"))

    return ("Equipo A", "Equipo B")


def detectar_evento(id_partido):
    texto = normalizar_texto(id_partido)

    if "FINAL" in texto:
        return "Final"
    elif "SEMIS" in texto or "SF" in texto:
        return "Semifinal"
    elif "QF" in texto or "CUARTOS" in texto:
        return "Cuartos de final"
    elif "GRUPO" in texto:
        return "Fase de grupos"
    else:
        return "Partido regular"


# ------------------------------
# Mercados tácticos
# ------------------------------

def generar_senales_posibles(datos):
    id_partido = datos.get("id", "000")
    liga = detectar_liga(id_partido)
    equipoA, equipoB = detectar_equipos(id_partido)
    tipo_evento = detectar_evento(id_partido)

    minuto = int(datos.get("minuto", 0) or 0)
    xg = float(datos.get("xG", 0) or 0)
    cuota = float(datos.get("cuota", 1.85) or 1.85)
    valor = calcular_valor(datos)
    prob_real = float(datos.get("prob_real", 0.75) or 0.75)
    prob_implicita = float(datos.get("prob_implicita", 0.54) or 0.54)
    momentum = normalizar_texto(datos.get("momentum"))

    base = calcular_confianza_base(datos)
    senales = []

    # 1) OVER 0.5 NEXT 15
    confianza_over15 = base
    if xg >= 1.2:
        confianza_over15 += 8
    if momentum in ("ALTO", "MUY ALTO"):
        confianza_over15 += 6
    if 20 <= minuto <= 80:
        confianza_over15 += 5

    confianza_over15 = clamp(confianza_over15, 45, 95)

    if confianza_over15 >= 62:
        senales.append({
            "id": id_partido,
            "liga": liga,
            "tipo_evento": tipo_evento,
            "equipoA": equipoA,
            "equipoB": equipoB,
            "minuto": minuto,
            "mercado": "OVER_0_5_NEXT_15",
            "apuesta": "Over 0.5 próximos 15 min",
            "cuota": cuota,
            "confianza": confianza_over15,
            "valor": valor,
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "razon": "Momentum alto + presión ofensiva + ventana favorable"
        })

    # 2) OVER 1.5 MATCH
    confianza_over_match = base
    if xg >= 1.5:
        confianza_over_match += 10
    if minuto <= 70:
        confianza_over_match += 6

    confianza_over_match = clamp(confianza_over_match, 45, 95)

    if confianza_over_match >= 64:
        senales.append({
            "id": id_partido,
            "liga": liga,
            "tipo_evento": tipo_evento,
            "equipoA": equipoA,
            "equipoB": equipoB,
            "minuto": minuto,
            "mercado": "OVER_1_5_MATCH",
            "apuesta": "Over 1.5 goles partido",
            "cuota": cuota,
            "confianza": confianza_over_match,
            "valor": valor,
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "razon": "xG acumulado favorable para más goles en el partido"
        })

    # 3) HOME WIN
    confianza_home = base
    if valor > 0:
        confianza_home += 5
    if prob_real > prob_implicita:
        confianza_home += 5

    confianza_home = clamp(confianza_home, 40, 95)

    if confianza_home >= 68:
        senales.append({
            "id": id_partido,
            "liga": liga,
            "tipo_evento": tipo_evento,
            "equipoA": equipoA,
            "equipoB": equipoB,
            "minuto": minuto,
            "mercado": "HOME_WIN",
            "apuesta": f"{equipoA} gana",
            "cuota": cuota,
            "confianza": confianza_home,
            "valor": valor,
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "razon": "Ventaja táctica del local + value positivo"
        })

    # 4) AWAY WIN
    confianza_away = base - 2
    if valor > 3:
        confianza_away += 7

    confianza_away = clamp(confianza_away, 40, 95)

    if confianza_away >= 70:
        senales.append({
            "id": id_partido,
            "liga": liga,
            "tipo_evento": tipo_evento,
            "equipoA": equipoA,
            "equipoB": equipoB,
            "minuto": minuto,
            "mercado": "AWAY_WIN",
            "apuesta": f"{equipoB} gana",
            "cuota": cuota,
            "confianza": confianza_away,
            "valor": valor,
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "razon": "Visitante con condiciones de valor y presión competitiva"
        })

    # 5) RESULTADO SE MANTIENE
    confianza_hold = 50
    if momentum in ("BAJO", "MEDIO"):
        confianza_hold += 10
    if xg < 1.0:
        confianza_hold += 12
    if minuto >= 70:
        confianza_hold += 8

    confianza_hold = clamp(confianza_hold, 40, 95)

    if confianza_hold >= 63:
        senales.append({
            "id": id_partido,
            "liga": liga,
            "tipo_evento": tipo_evento,
            "equipoA": equipoA,
            "equipoB": equipoB,
            "minuto": minuto,
            "mercado": "RESULT_HOLDS_NEXT_15",
            "apuesta": "Se mantiene el resultado próximos 15 min",
            "cuota": cuota,
            "confianza": confianza_hold,
            "valor": valor,
            "prob_real": prob_real,
            "prob_implicita": prob_implicita,
            "razon": "Bajo ritmo ofensivo + xG moderado + ventana final"
        })

    return senales


# ------------------------------
# Escoger mejor señal
# ------------------------------

def elegir_mejor_senal(senales):
    if not senales:
        return None

    senales_ordenadas = sorted(
        senales,
        key=lambda s: (s.get("confianza", 0), s.get("valor", 0)),
        reverse=True
    )
    return senales_ordenadas[0]


# ------------------------------
# Motor principal
# ------------------------------

def generar_senal(datos):
    senales = generar_senales_posibles(datos)
    mejor = elegir_mejor_senal(senales)

    if mejor is None:
        id_partido = datos.get("id", "000")
        liga = detectar_liga(id_partido)
        equipoA, equipoB = detectar_equipos(id_partido)
        tipo_evento = detectar_evento(id_partido)

        return {
            "id": id_partido,
            "liga": liga,
            "tipo_evento": tipo_evento,
            "equipoA": equipoA,
            "equipoB": equipoB,
            "minuto": int(datos.get("minuto", 0) or 0),
            "mercado": "SIN_SEÑAL",
            "apuesta": "Sin oportunidad clara",
            "cuota": float(datos.get("cuota", 1.85) or 1.85),
            "confianza": calcular_confianza_base(datos),
            "valor": calcular_valor(datos),
            "prob_real": float(datos.get("prob_real", 0.75) or 0.75),
            "razon": "No se detectó ventaja suficiente en este momento",
            "senales_posibles": []
        }

    mejor["senales_posibles"] = senales
    return mejor


# ------------------------------
# Narrativa táctica
# ------------------------------

def formatear_senal_narrativa(senal, hora_local="19:59 BOL", numero=1):
    equipoA = senal.get("equipoA", "Equipo A")
    equipoB = senal.get("equipoB", "Equipo B")
    minuto = senal.get("minuto", 0)
    liga = senal.get("liga", "Liga desconocida")
    tipo = senal.get("tipo_evento", "Partido")
    confianza = senal.get("confianza", 0)
    cuota = senal.get("cuota", 1.85)
    razon = senal.get("razon", "Sin razón definida")
    valor = senal.get("valor", 0)
    prob_real = senal.get("prob_real", 0.75)
    apuesta = senal.get("apuesta", "Sin apuesta")
    mercado = senal.get("mercado", "SIN_MERCADO")

    return f"""
📊 DATOS PARTIDO [{senal.get("id", "SIN-ID")}]
⚽ {equipoA} vs {equipoB} — Min {minuto}°
🏆 {liga} — {tipo}
🎯 Mercado: {mercado}

---

🎯 SEÑAL #{numero} — {hora_local}
⚽ {equipoA} vs {equipoB} — Min {minuto}°
💡 APUESTA: {apuesta} @{cuota}
🎯 CONFIANZA: {confianza}%
📈 VALOR: +{valor}% margen
🎲 PROB REAL: {round(prob_real * 100, 2)}%
🔍 RAZÓN: {razon}
""".strip()

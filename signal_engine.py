# 📊 Calcular confianza táctica
def calcular_confianza(datos):
    if datos.get("momentum") == "ALTO" and datos.get("xG", 0) > 1.2:
        return 85
    return 60

# 💡 Calcular valor esperado
def calcular_valor(datos):
    prob_real = float(datos.get("prob_real", 0.75))
    prob_implicita = float(datos.get("prob_implicita", 0.54))
    return round((prob_real - prob_implicita) * 100, 2)

# 🧠 Detectar liga según prefijo
def detectar_liga(id):
    if id.startswith("ATP"):
        return "ATP Tour"
    elif id.startswith("WTA"):
        return "WTA Tour"
    elif id.startswith("NBA"):
        return "NBA"
    elif id.startswith("FIFA"):
        return "Fútbol Internacional"
    else:
        return "Desconocida"

# ⚔️ Detectar equipos según ID
def detectar_equipos(id):
    mapa = {
        "ATP-2025-001": ("Djokovic", "Alcaraz"),
        "ATP-2025-002": ("Medvedev", "Sinner"),
        "NBA-2025-001": ("Lakers", "Warriors"),
        "FIFA-2025-001": ("Brasil", "Argentina")
    }
    return mapa.get(id, ("Equipo A", "Equipo B"))

# 🏆 Detectar tipo de evento según ID
def detectar_evento(id):
    id = id.upper()
    if "FINAL" in id:
        return "Final"
    elif "SEMIS" in id or "SF" in id:
        return "Semifinal"
    elif "QF" in id or "CUARTOS" in id:
        return "Cuartos de final"
    elif "GRUPO" in id or "G" in id:
        return "Fase de grupos"
    else:
        return "Partido regular"

# 🎯 Generar señal táctica
def generar_senal(datos):
    confianza = calcular_confianza(datos)
    liga = detectar_liga(datos.get("id", "000"))
    equipoA, equipoB = detectar_equipos(datos.get("id", "000"))
    tipo_evento = detectar_evento(datos.get("id", "000"))
    valor = calcular_valor(datos)
    razon = "Momentum alto + xG > 1.2" if confianza >= 75 else "Condiciones tácticas estándar"

    return {
        "id": datos.get("id", "000"),
        "liga": liga,
        "tipo_evento": tipo_evento,
        "equipoA": equipoA,
        "equipoB": equipoB,
        "minuto": int(datos.get("minuto", 0)),
        "apuesta": "Ganador",
        "cuota": float(datos.get("cuota", 1.85)),
        "confianza": confianza,
        "valor": valor,
        "prob_real": float(datos.get("prob_real", 0.75)),
        "razon": razon
    }

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
    id = id.upper()
    if "UEFA" in id:
        return "Champions League"
    elif "CONMEBOL" in id:
        return "Copa Libertadores"
    elif "FIFA" in id:
        return "Fútbol Internacional"
    elif "ATP" in id:
        return "ATP Tour"
    elif "NBA" in id:
        return "NBA"
    else:
        return "Liga desconocida"

# ⚔️ Detectar equipos según ID
def detectar_equipos(id: str):
    id = id.upper().strip()
    ligas = {
        "FIFA": {
            "FINAL-2025": ("Brasil", "Argentina"),
            "GRUPO-2025": ("Francia", "Alemania"),
            "SEMIS-2025": ("España", "Inglaterra")
        },
        "UEFA": {
            "FINAL-2025": ("Real Madrid", "Manchester City"),
            "SF-2025": ("Bayern Munich", "PSG"),
            "QF-2025": ("Chelsea", "Barcelona")
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

    partes = id.split("-", 1)
    if len(partes) != 2:
        return ("Equipo A", "Equipo B")

    prefijo, sufijo = partes
    liga = ligas.get(prefijo)
    if liga:
        return liga.get(sufijo, ("Equipo A", "Equipo B"))
    return ("Equipo A", "Equipo B")

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

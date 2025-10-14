def generar_senal(datos):
    confianza = calcular_confianza(datos)
    return {
        "id": datos.get("id", "000"),
        "liga": datos.get("liga", "Desconocida"),
        "equipoA": datos.get("equipoA", "Equipo A"),
        "equipoB": datos.get("equipoB", "Equipo B"),
        "minuto": datos.get("minuto", 0),
        "apuesta": "Ganador",
        "cuota": datos.get("cuota", 1.85),
        "confianza": confianza,
        "valor": calcular_valor(datos),
        "prob_real": datos.get("prob_real", 0.75),
        "razon": "Momentum alto + xG > 1.2"
    }

def calcular_confianza(datos):
    if datos.get("momentum") == "ALTO" and datos.get("xG", 0) > 1.2:
        return 85
    return 60

def calcular_valor(datos):
    prob_real = datos.get("prob_real", 0.75)
    prob_implicita = datos.get("prob_implicita", 0.54)
    return round((prob_real - prob_implicita) * 100, 2)
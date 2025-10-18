def enviar_notificacion(senal: dict):
    if not isinstance(senal, dict):
        print("⚠️ Señal inválida: no es un diccionario")
        return

    try:
        equipoA = str(senal.get("equipoA", "Equipo A"))
        equipoB = str(senal.get("equipoB", "Equipo B"))
        apuesta = str(senal.get("apuesta", "N/A"))
        cuota = float(senal.get("cuota", 0))
        confianza = int(senal.get("confianza", 0))
        valor = float(senal.get("valor", 0))
        prob_real = float(senal.get("prob_real", 0))
        razon = str(senal.get("razon", "Sin razón definida"))

        print("🔔 Señal activada:")
        print(f"{equipoA} vs {equipoB}")
        print(f"Apuesta: {apuesta} @ {cuota}")
        print(f"Confianza: {confianza}%")
        print(f"Valor: {valor}%")
        print(f"Probabilidad real: {prob_real}%")
        print(f"Razón: {razon}")

    except Exception as e:
        print(f"⚠️ Error al enviar notificación: {e}")

def enviar_notificacion(senal: dict):
    try:
        equipoA = senal.get("equipoA", "Equipo A")
        equipoB = senal.get("equipoB", "Equipo B")
        apuesta = senal.get("apuesta", "N/A")
        cuota = senal.get("cuota", "N/A")
        confianza = senal.get("confianza", 0)
        valor = senal.get("valor", 0)
        prob_real = senal.get("prob_real", 0)
        razon = senal.get("razon", "Sin razón definida")

        print("🔔 Señal activada:")
        print(f"{equipoA} vs {equipoB}")
        print(f"Apuesta: {apuesta} @ {cuota}")
        print(f"Confianza: {confianza}%")
        print(f"Valor: {valor}%")
        print(f"Probabilidad real: {prob_real}%")
        print(f"Razón: {razon}")

    except Exception as e:
        print(f"⚠️ Error al enviar notificación: {e}")

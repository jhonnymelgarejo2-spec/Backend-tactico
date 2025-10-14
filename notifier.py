def enviar_notificacion(senal):
    print("🔔 Señal activada:")
    print(f"{senal['equipoA']} vs {senal['equipoB']}")
    print(f"Apuesta: {senal['apuesta']} @ {senal['cuota']}")
    print(f"Confianza: {senal['confianza']}%")
    print(f"Valor: {senal['valor']}%")
    print(f"Probabilidad real: {senal['prob_real']}%")
    print(f"Razón: {senal['razon']}")
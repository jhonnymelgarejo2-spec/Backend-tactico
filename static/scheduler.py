# ⏱️ Módulo de escaneo automático de señales
from apscheduler.schedulers.background import BackgroundScheduler
from sofascore_fetcher import obtener_partidos_en_vivo
from signal_engine import generar_senal
from notifier import enviar_notificacion

def escanear_partidos():
    try:
        partidos = obtener_partidos_en_vivo()
        for p in partidos:
            datos = {
                "id": str(p["id"]),
                "momentum": "Dominio total",  # Puedes ajustar según lógica real
                "xG": 1.2,  # Simulado o extraído si la API lo permite
                "prob_real": 0.75,
                "prob_implicita": 0.60,
                "cuota": 1.8,
                "minuto": p.get("minuto", 15)
            }

            senal = generar_senal(datos)
            if senal.get("confianza", 0) >= 75:
                enviar_notificacion(senal)
                print(f"✅ Señal lanzada: {senal}")
            else:
                print(f"🔍 Sin señal: {senal.get('confianza', 0)}%")
    except Exception as e:
        print(f"⚠️ Error en escaneo automático: {e}")

def iniciar_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(escanear_partidos, 'interval', seconds=30)
    scheduler.start()
    print("🧠 Escaneo táctico activado cada 30 segundos")

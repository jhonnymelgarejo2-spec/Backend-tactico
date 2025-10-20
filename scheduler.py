from apscheduler.schedulers.background import BackgroundScheduler
from signal_engine import generar_senal  # o el módulo que genera tus señales

def escanear_tactico():
    # Aquí va tu lógica de escaneo
    print("🔍 Escaneo táctico ejecutado")
    # Puedes llamar a generar_senal() o cualquier otra función

def iniciar_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(escanear_tactico, 'interval', seconds=30)
    scheduler.start()
    print("✅ Scheduler táctico activado")

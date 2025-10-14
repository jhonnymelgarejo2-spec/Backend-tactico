from fastapi import FastAPI
from signal_engine import generar_senal
from notifier import enviar_notificacion

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Sistema JHONNY ELITE V7.0 activo"}

@app.post("/analizar/")
def analizar_partido(datos: dict):
    senal = generar_senal(datos)
    if senal["confianza"] >= 75:
        enviar_notificacion(senal)

    return senal

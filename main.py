from fastapi import FastAPI
from signal_engine import generar_señal
from notifier import enviar_notificacion

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Sistema JHONNY ELITE V7.0 activo"}

@app.post("/analizar/")
def analizar_partido(datos: dict):
    señal = generar_señal(datos)
    if señal["confianza"] >= 75:
        enviar_notificacion(señal)
    return señal
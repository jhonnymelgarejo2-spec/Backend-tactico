from fastapi import FastAPI
from pydantic import BaseModel
from signal_engine import generar_senal
from notifier import enviar_notificacion

app = FastAPI()

class Datos(BaseModel):
    id: str
    momentum: str
    valor: float
    prob_real: float
    prob_implicita: float

@app.get("/")
def home():
    return {"status": "Sistema JHONNY ELITE V7.0 activo"}

@app.post("/analizar/")
def analizar_partido(datos: Datos):
    senal = generar_senal(datos.dict())
    if senal.get("confianza", 0) >= 75:
        enviar_notificacion(senal)
    return senal

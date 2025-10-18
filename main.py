from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from signalengine import generarsenal
from notifier import enviar_notificacion

app = FastAPI()

Montar carpeta estática
app.mount("/static", StaticFiles(directory="static"), name="static")

Servir index.html directamente en "/"
@app.get("/", response_class=FileResponse)
def serve_index():
    return "static/index.html"

Modelo de datos para análisis
class Datos(BaseModel):
    id: str
    momentum: str
    valor: float
    prob_real: float
    prob_implicita: float

Endpoint de análisis táctico
@app.post("/analizar/")
def analizar_partido(datos: Datos):
    senal = generar_senal(datos.dict())
    if senal.get("confianza", 0) >= 75:
        enviar_notificacion(senal)
    return senal

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from signal_engine import generar_senal
from notifier import enviar_notificacion

app = FastAPI()

# 📁 Montar carpeta estática para frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🖥️ Servir index.html directamente en "/"
@app.get("/")
def read_index():
    return FileResponse("static/index.html")

# 📊 Modelo de datos para análisis táctico
class DatosDeAnalisisTactico(BaseModel):
    id: str
    momentum: str
    xG: float
    prob_real: float
    prob_implicita: float
    cuota: float
    minuto: int

# 🎯 Endpoint de análisis táctico
@app.post("/analizar/")
def analizar_partido(datos: DatosDeAnalisisTactico):
    senal = generar_senal(datos.dict())
    if senal.get("confianza", 0) >= 75:
        enviar_notificacion(senal)
    return senal

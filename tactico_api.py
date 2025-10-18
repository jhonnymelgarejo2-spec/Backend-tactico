# 📦 Importaciones principales
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# ⚙️ Módulos internos
from signal_engine import generar_senal
from notifier import enviar_notificacion

# 🧩 Integración con router de Sofascore
try:
    from live_router import router as live_router
except Exception as e:
    live_router = None
    print(f"⚠️ No se pudo cargar live_router: {e}")

# 🚀 Inicializar FastAPI
app = FastAPI()

# 📁 Montar carpeta estática para frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🖥️ Servir index.html directamente en "/"
@app.get("/")
def read_index():
    return FileResponse("static/index.html")

# 🧪 Endpoint de prueba para confirmar vida del backend
@app.get("/ping")
def ping():
    return {"status": "ok"}

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
    try:
        if senal.get("confianza", 0) >= 75:
            enviar_notificacion(senal)
    except Exception as e:
        print(f"⚠️ Error al enviar notificación: {e}")
    return senal

# 🔗 Activar router de Sofascore si fue cargado correctamente
if live_router:
    app.include_router(live_router)

# 🚀 Bloque final para ejecución en Render
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

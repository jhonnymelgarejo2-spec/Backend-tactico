from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import os

# Módulos internos
from signal_engine import generar_senal
from notifier import enviar_notificacion
from scheduler import iniciar_scheduler

# Integración con router de Sofascore
try:
    from live_router import router as live_router
except Exception as e:
    live_router = None
    print(f"⚠️ Error: No se pudo cargar live_router: {e}")

# Inicializar FastAPI
app = FastAPI(
    title="JHONNY_ELITE V7.0",
    description="Backend táctico para análisis de apuestas deportivas",
    version="1.0"
)

# Activar escaneo táctico en segundo plano
iniciar_scheduler()

# Activar CORS para permitir conexión desde frontend externo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://69.14.103.144:3000",
        "http://69.14.103.144:3001",
        "http://69.14.103.144:3002"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta estática para frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir index.html directamente en "/"
@app.get("/")
def read_index():
    ruta = Path(__file__).parent / "static" / "index.html"
    return FileResponse(ruta)

# Modelo de datos para análisis táctico
class DatosDeAnalisisTactico(BaseModel):
    id: str
    momentum: str
    xG: float
    prob_real: float
    prob_implicita: float
    cuota: float
    minuto: int

# Endpoint de análisis táctico
@app.post("/analizar_datos")
def analizar_datos(datos: DatosDeAnalisisTactico):
    try:
        resultado = generar_senal(datos.dict())
        return resultado
    except Exception as e:
        return {"error": str(e)}

# Endpoint para enviar señal directa
@app.post("/enviar/")
def enviar_senal_directa(datos: DatosDeAnalisisTactico):
    try:
        enviar_notificacion(datos.dict())
        return {"status": "enviada"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)}

# Activar router de Sofascore si fue cargado correctamente
if live_router:
    app.include_router(live_router)

# Endpoint de diagnóstico para confirmar vida del backend
@app.get("/status")
def get_status():
    return {"status": "ok", "mensaje": "Backend táctico operativo"}

# Endpoint de prueba HTML
@app.get("/html-test", response_class=HTMLResponse)
def html_test():
    return """
    <html>
        <head><title>Test HTML</title></head>
        <body style="background-color:#111;color:#0f0;font-family:sans-serif;">
            <h1>✅ Backend táctico operativo</h1>
            <p>Este contenido fue servido directamente por FastAPI.</p>
        </body>
    </html>
    """

# Bloque final para ejecución en Render
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

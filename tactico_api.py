# 📦 Importaciones principales
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path  # 🛡️ Nueva importación para ruta segura

# ⚙️ Módulos internos
from signal_engine import generar_senal
from notifier import enviar_notificacion

# ⏱️ Activar escaneo automático de señales
from scheduler import iniciar_scheduler

# 🧩 Integración con router de Sofascore
try:
    from live_router import router as live_router
except Exception as e:
    live_router = None
    print(f"⚠️ No se pudo cargar live_router: {e}")

# 🚀 Inicializar FastAPI
app = FastAPI()
iniciar_scheduler()  # 🧠 Activar escaneo táctico en segundo plano

# 🔓 Activar CORS para permitir conexión desde frontend externo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes reemplazar "*" por tu dominio exacto si prefieres seguridad
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Montar carpeta estática para frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

# 🖥️ Servir index.html directamente en "/"
@app.get("/")
def read_index():
    ruta = Path(__file__).parent / "static" / "index.html"
    return FileResponse(ruta)

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

# 🧪 Endpoint de diagnóstico para confirmar vida del backend
@app.get("/debug")
def debug():
    return {"status": "ok", "mensaje": "Backend táctico activo y operativo"}

# 🧩 Endpoint de verificación modular
@app.get("/status")
def status():
    return {
        "backend": "activo",
        "sofascore_router": bool(live_router),
        "mensaje": "Sistema táctico operativo"
    }

# 🧪 Endpoint de prueba HTML
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

# 🚀 Bloque final para ejecución en Render
if __name__ == "__main__":
    import uvicorn, os
    port = int(os.environ.get("PORT", 8000))  # 🛠️ Cambio: usar variable dinámica
    uvicorn.run(app, host="0.0.0.0", port=port)

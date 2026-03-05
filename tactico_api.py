from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import os

# Cargar variables .env
from dotenv import load_dotenv
load_dotenv()

# NUEVO: para escaneo automático
import asyncio
from scanner import Scanner
from providers import MockProvider

# Módulos internos
from signal_engine import generar_senal
from notifier import enviar_notificacion

# Routers externos
try:
    from live_router import router as live_router
except Exception as e:
    live_router = None
    print(f"⚠️ Error: No se pudo cargar live_router: {e}")

try:
    from scan_fixtures import router as fixtures_router
except Exception as e:
    fixtures_router = None
    print(f"⚠️ Error: No se pudo cargar scan_fixtures: {e}")

# Routers tácticos
from partidos_en_vivo import router as partidos_router
from footapi import router as footapi_router

# Inicializar FastAPI
app = FastAPI(
    title="JHONNY_ELITE V7.0",
    description="Backend táctico para análisis de apuestas deportivas",
    version="1.0"
)

# Inicializar scanner
scanner = Scanner(provider=MockProvider(), max_matches=60)

# Arrancar escáner automático
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(scanner.loop(interval_sec=60))

# CORS
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

# Carpeta estática
app.mount("/static", StaticFiles(directory="static"), name="static")

# Servir index.html
@app.get("/")
def read_index():
    ruta = Path(__file__).parent / "static" / "index.html"
    return FileResponse(ruta)

# Modelo análisis
class DatosDeAnalisisTactico(BaseModel):
    id: str
    momentum: str
    xG: float
    prob_real: float
    prob_implicita: float
    cuota: float
    minuto: int

# Endpoint análisis
@app.post("/analizar_datos")
def analizar_datos(datos: DatosDeAnalisisTactico):
    try:
        resultado = generar_senal(datos.dict())
        return resultado
    except Exception as e:
        return {"error": str(e)}

# Endpoint enviar señal
@app.post("/enviar/")
def enviar_senal_directa(datos: DatosDeAnalisisTactico):
    try:
        enviar_notificacion(datos.dict())
        return {"status": "enviada"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)}

# Routers externos
if live_router:
    app.include_router(live_router)

if fixtures_router:
    app.include_router(fixtures_router)

# Routers tácticos
app.include_router(partidos_router)
app.include_router(footapi_router)

# ENDPOINT SCANNER
@app.get("/scan")
def get_scan():
    return scanner.last_snapshot

@app.post("/scan/now")
async def scan_now():
    snap = await scanner.run_once()
    return snap

@app.get("/signals")
def get_signals():
    return {"signals": scanner.last_snapshot.get("signals", [])}

# Status
@app.get("/status")
def get_status():
    return {"status": "ok", "mensaje": "Backend táctico operativo"}

# Test HTML
@app.get("/html-test", response_class=HTMLResponse)
def html_test():
    return """
    <html>
        <head><title>Test HTML</title></head>
        <body style="background-color:#111;color:#0f0;font-family:sans-serif;">
            <h1>Backend táctico operativo</h1>
        </body>
    </html>
    """

# Ejecutar
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)        

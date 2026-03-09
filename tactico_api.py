from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

# =========================
# IMPORTS INTERNOS
# =========================
from signal_engine import generar_senal
from notifier import enviar_notificacion

# Routers opcionales
try:
    from live_router import router as live_router
except Exception as e:
    live_router = None
    print(f"⚠️ No se pudo cargar live_router: {e}")

try:
    from scan_fixtures import router as fixtures_router
except Exception as e:
    fixtures_router = None
    print(f"⚠️ No se pudo cargar scan_fixtures: {e}")

try:
    from partidos_en_vivo import router as partidos_router
except Exception as e:
    partidos_router = None
    print(f"⚠️ No se pudo cargar partidos_en_vivo: {e}")

try:
    from footapi import router as footapi_router
except Exception as e:
    footapi_router = None
    print(f"⚠️ No se pudo cargar footapi: {e}")


# =========================
# APP
# =========================
app = FastAPI(
    title="JHONNY_ELITE V10",
    description="Backend táctico para análisis de apuestas deportivas",
    version="10.0"
)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
else:
    print(f"⚠️ Carpeta static no encontrada en: {STATIC_DIR}")


# =========================
# MODELOS
# =========================
class DatosDeAnalisisTactico(BaseModel):
    id: str = ""
    momentum: str = "MEDIO"
    xG: float = 0.0
    prob_real: float = 0.75
    prob_implicita: float = 0.54
    cuota: float = 1.85
    minuto: int = 0


# =========================
# STARTUP
# =========================
@app.on_event("startup")
async def startup_event():
    print("🚀 Iniciando backend táctico...")

    # AUTO-SCAN
    try:
        from scan_fixtures import auto_scan_start
        resultado = await auto_scan_start()
        print(f"✅ AUTO-SCAN arrancado al iniciar el backend: {resultado}")
    except Exception as e:
        print(f"⚠️ No se pudo iniciar AUTO-SCAN: {e}")

    # AUTO RESULT ENGINE
    try:
        from auto_result_engine import loop_auto_result
        asyncio.create_task(loop_auto_result())
        print("🧠 MOTOR DE RESULTADOS AUTOMÁTICOS iniciado")
    except Exception as e:
        print(f"⚠️ No se pudo iniciar AUTO RESULT ENGINE: {e}")

    print("✅ Backend listo")


# =========================
# RUTAS PRINCIPALES
# =========================
@app.get("/")
def read_index():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return HTMLResponse(
        content="""
        <html>
            <head><title>JHONNY_ELITE V10</title></head>
            <body style="background:#07111f;color:#fff;font-family:Arial;padding:30px;">
                <h1>⚠️ index.html no encontrado</h1>
                <p>El backend está activo, pero falta <b>static/index.html</b>.</p>
            </body>
        </html>
        """,
        status_code=200
    )


@app.head("/")
def head_index():
    return JSONResponse(content={"status": "ok"})


@app.get("/status")
def get_status():
    return {
        "status": "ok",
        "mensaje": "Backend táctico operativo"
    }


@app.get("/html-test", response_class=HTMLResponse)
def html_test():
    return """
    <html>
        <head><title>Test HTML</title></head>
        <body style="background-color:#111;color:#0f0;font-family:Arial,sans-serif;padding:30px;">
            <h1>✅ Backend táctico operativo</h1>
            <p>El servicio HTML responde correctamente.</p>
        </body>
    </html>
    """


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/ping")
def ping():
    return {"pong": True}


# =========================
# RUTAS DE ANALISIS
# =========================
@app.post("/analizar_datos")
def analizar_datos(datos: DatosDeAnalisisTactico):
    try:
        resultado = generar_senal(datos.dict())
        return resultado
    except Exception as e:
        return {"status": "error", "detalle": str(e)}


@app.post("/enviar/")
def enviar_senal_directa(datos: DatosDeAnalisisTactico):
    try:
        enviar_notificacion(datos.dict())
        return {"status": "enviada"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)}


# =========================
# INCLUIR ROUTERS
# =========================
if live_router:
    app.include_router(live_router)

if fixtures_router:
    app.include_router(fixtures_router)

if partidos_router:
    app.include_router(partidos_router)

if footapi_router:
    app.include_router(footapi_router)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)

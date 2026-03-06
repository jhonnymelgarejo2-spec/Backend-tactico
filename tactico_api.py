from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import os

from dotenv import load_dotenv
load_dotenv()

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


app = FastAPI(
    title="JHONNY_ELITE V7.0",
    description="Backend táctico para análisis de apuestas deportivas",
    version="1.0"
)

# 🚀 AUTO-SCAN al iniciar el backend
@app.on_event("startup")
async def startup_event():
    try:
        from scan_fixtures import auto_scan_start
        await auto_scan_start()
        print("✅ AUTO-SCAN arrancado al iniciar el backend")
    except Exception as e:
        print(f"⚠️ No se pudo iniciar AUTO-SCAN: {e}")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def read_index():
    ruta = Path(__file__).parent / "static" / "index.html"
    return FileResponse(ruta)


# evita error 405 cuando Render hace chequeo HEAD
@app.head("/")
def head_index():
    return


class DatosDeAnalisisTactico(BaseModel):
    id: str
    momentum: str
    xG: float
    prob_real: float
    prob_implicita: float
    cuota: float
    minuto: int


@app.post("/analizar_datos")
def analizar_datos(datos: DatosDeAnalisisTactico):
    try:
        resultado = generar_senal(datos.dict())
        return resultado
    except Exception as e:
        return {"error": str(e)}


@app.post("/enviar/")
def enviar_senal_directa(datos: DatosDeAnalisisTactico):
    try:
        enviar_notificacion(datos.dict())
        return {"status": "enviada"}
    except Exception as e:
        return {"status": "error", "detalle": str(e)}


if live_router:
    app.include_router(live_router)

if fixtures_router:
    app.include_router(fixtures_router)

app.include_router(partidos_router)
app.include_router(footapi_router)


@app.get("/status")
def get_status():
    return {"status": "ok", "mensaje": "Backend táctico operativo"}


@app.get("/html-test", response_class=HTMLResponse)
def html_test():
    return """
    <html>
        <head><title>Test HTML</title></head>
        <body style="background-color:#111;color:#0f0;font-family:sans-serif;">
            <h1>✅ Backend táctico operativo</h1>
        </body>
    </html>
    """


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

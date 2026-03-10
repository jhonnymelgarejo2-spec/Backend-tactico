from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path

from live_router import router as live_router

app = FastAPI(
    title="JHONNY_ELITE V10 API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

# Servir archivos estáticos
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Conectar rutas del backend
app.include_router(live_router)


# ------------------------------
# RUTA PRINCIPAL DEL DASHBOARD
# ------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return HTMLResponse(
        content="""
        <html>
          <head><title>JHONNY_ELITE V10</title></head>
          <body style="background:#07111f;color:white;font-family:Arial;padding:30px;">
            <h1>Dashboard no encontrado</h1>
            <p>Falta el archivo <strong>static/index.html</strong>.</p>
          </body>
        </html>
        """
    )


# ------------------------------
# ESTADO DEL BACKEND
# ------------------------------
@app.get("/status")
def estado_backend():
    return {
        "status": "ok",
        "mensaje": "Backend táctico operativo"
    }


# ------------------------------
# PING
# ------------------------------
@app.get("/ping")
def ping():
    return {
        "ping": "pong",
        "mensaje": "Servidor activo"
    }


# ------------------------------
# DEBUG DE RUTAS
# ------------------------------
@app.get("/debug-routes")
def debug_routes():
    rutas = []
    for route in app.routes:
        rutas.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods) if hasattr(route, "methods") else []
        })

    return {
        "total_rutas": len(rutas),
        "rutas": rutas
}

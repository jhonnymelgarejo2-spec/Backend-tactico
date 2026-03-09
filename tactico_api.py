from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# importar router de partidos y señales
from live_router import router as live_router

app = FastAPI(
    title="JHONNY_ELITE V10 API",
    version="1.0"
)

# permitir acceso desde frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# conectar router
app.include_router(live_router, prefix="/api")

# ------------------------------
# RUTA PRINCIPAL
# ------------------------------

@app.get("/")
def home():
    return {
        "status": "ok",
        "mensaje": "Backend táctico funcionando",
        "rutas_disponibles": [
            "/signals",
            "/scan",
            "/history",
            "/learning-stats",
            "/status",
            "/auto-scan/status"
        ]
    }

# ------------------------------
# ESTADO DEL BACKEND
# ------------------------------

@app.get("/status")
def estado_backend():
    return {
        "backend": "activo",
        "motor": "tactico",
        "estado": "ok"
    }

# ------------------------------
# PING TEST
# ------------------------------

@app.get("/ping")
def ping():
    return {
        "ping": "pong",
        "mensaje": "Servidor activo"
    }


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

# Conectar router
app.include_router(live_router)


@app.get("/")
def home():
    return {
        "status": "ok",
        "mensaje": "Backend táctico funcionando"
    }


@app.get("/status")
def estado_backend():
    return {
        "backend": "activo",
        "motor": "tactico",
        "estado": "ok"
    }


@app.get("/ping")
def ping():
    return {
        "ping": "pong",
        "mensaje": "Servidor activo"
    }


@app.get("/debug-routes")
def debug_routes():
    rutas = []
    for route in app.routes:
        methods = list(route.methods) if hasattr(route, "methods") else []
        rutas.append({
            "path": route.path,
            "methods": methods,
            "name": route.name
        })

    return {
        "total_rutas": len(rutas),
        "rutas": rutas
    }

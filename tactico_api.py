from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from live_router import router as live_router
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

app = FastAPI(
    title="JHONNY ELITE API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# router adicional
app.include_router(live_router)


@app.get("/")
def home():
    return {
        "ok": True,
        "mensaje": "Backend táctico funcionando",
        "version": "V1_REAL"
    }


@app.get("/status")
def status():
    return {
        "status": "ok",
        "service": "backend-tactico",
        "version": "V1_REAL"
    }


@app.get("/debug-routes")
def debug_routes():
    return {
        "ok": True,
        "routes": [
            "/",
            "/status",
            "/debug-routes",
            "/partidos-en-vivo",
            "/scan",
            "/signals"
        ],
        "version": "V1_REAL"
    }


@app.get("/scan")
def scan():
    try:
        partidos = obtener_partidos_en_vivo()
        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "partidos_analizados": len(partidos),
            "partidos": partidos
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "partidos": []
        }


@app.get("/signals")
def signals_endpoint():
    try:
        partidos = obtener_partidos_en_vivo()
        senales = generar_senales(partidos)

        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "total_senales": len(senales),
            "signals": senales
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "signals": []
}

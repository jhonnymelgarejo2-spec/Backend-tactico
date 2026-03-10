from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from live_router import router as live_router
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

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

# router
app.include_router(live_router)

# cache simple
CACHE_PARTIDOS = []
CACHE_SENALES = []

# ------------------------------
# HOME
# ------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h2>Backend táctico funcionando</h2>"

# ------------------------------
# STATUS
# ------------------------------

@app.get("/status")
def estado_backend():
    return {
        "status": "ok",
        "backend": "activo"
    }

# ------------------------------
# SCAN
# ------------------------------

@app.get("/scan")
def scan():

    partidos = obtener_partidos_en_vivo()
    senales = generar_senales(partidos)

    global CACHE_PARTIDOS
    global CACHE_SENALES

    CACHE_PARTIDOS = partidos
    CACHE_SENALES = senales

    return {
        "estado": "OK",
        "partidos_analizados": len(partidos),
        "partidos": partidos
    }

# ------------------------------
# SIGNALS
# ------------------------------

@app.get("/signals")
def signals():

    if not CACHE_PARTIDOS:
        partidos = obtener_partidos_en_vivo()
        senales = generar_senales(partidos)

        CACHE_PARTIDOS.extend(partidos)
        CACHE_SENALES.extend(senales)

    return {
        "estado": "OK",
        "total_partidos": len(CACHE_PARTIDOS),
        "total_senales": len(CACHE_SENALES),
        "signals": CACHE_SENALES
    }

# ------------------------------
# HISTORY
# ------------------------------

@app.get("/history")
def history():
    return []

# ------------------------------
# LEARNING STATS
# ------------------------------

@app.get("/learning-stats")
def learning_stats():
    return {
        "total_senales": len(CACHE_SENALES),
        "win_rate": 0,
        "roi_percent": 0,
        "ganadas": 0,
        "perdidas": 0
    }

# ------------------------------
# AUTO SCAN
# ------------------------------

@app.get("/auto-scan/status")
def auto_scan_status():
    return {
        "auto_scan_activo": True,
        "intervalo_segundos": 30
    }


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from threading import Thread
import time
import traceback

from live_router import router as live_router
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

# Historial opcional
try:
    from history_store import cargar_historial, obtener_estadisticas_historial
except Exception:
    cargar_historial = None
    obtener_estadisticas_historial = None


app = FastAPI(
    title="JHONNY ELITE API",
    version="V1_REAL"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router adicional
app.include_router(live_router)

# ---------------------------------
# RUTAS DE ARCHIVOS
# ---------------------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

# ---------------------------------
# MEMORIA GLOBAL DEL SISTEMA
# ---------------------------------
AUTO_SCAN_DATA = {
    "partidos": [],
    "signals": [],
    "last_scan": None,
    "auto_scan_activo": True,
    "intervalo_segundos": 60
}


# ---------------------------------
# FUNCION DE AUTO-SCAN
# ---------------------------------
def auto_scan_loop():
    while True:
        try:
            partidos = obtener_partidos_en_vivo()
            signals = generar_senales(partidos)

            AUTO_SCAN_DATA["partidos"] = partidos if isinstance(partidos, list) else []
            AUTO_SCAN_DATA["signals"] = signals if isinstance(signals, list) else []
            AUTO_SCAN_DATA["last_scan"] = int(time.time())

            print("AUTO SCAN ejecutado correctamente")

        except Exception as e:
            print("Error en auto scan:", str(e))
            print(traceback.format_exc())

        time.sleep(AUTO_SCAN_DATA["intervalo_segundos"])


@app.on_event("startup")
def startup_event():
    thread = Thread(target=auto_scan_loop, daemon=True)
    thread.start()


# ---------------------------------
# FRONTEND
# ---------------------------------
@app.get("/")
def home():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse({
        "ok": True,
        "mensaje": "Backend táctico funcionando",
        "version": "V1_REAL",
        "frontend": "index.html no encontrado en /static"
    })


# ---------------------------------
# ESTADO
# ---------------------------------
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
            "/signals",
            "/history",
            "/learning-stats",
            "/auto-scan/status"
        ],
        "version": "V1_REAL"
    }


# Alias en español por si los quieres probar también
@app.get("/estado")
def estado_alias():
    return status()


@app.get("/rutas-de-depuracion")
def debug_routes_alias():
    return {
        "ok": True,
        "rutas": [
            "/",
            "/estado",
            "/rutas-de-depuracion",
            "/partidos-en-vivo",
            "/escanear",
            "/senales"
        ],
        "version": "V1_REAL"
    }


# ---------------------------------
# RUTAS PRINCIPALES
# ---------------------------------
@app.get("/scan")
def scan():
    try:
        partidos = AUTO_SCAN_DATA["partidos"]

        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "partidos_analizados": len(partidos),
            "partidos": partidos,
            "last_scan": AUTO_SCAN_DATA["last_scan"]
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
        partidos = AUTO_SCAN_DATA["partidos"]
        senales = AUTO_SCAN_DATA["signals"]

        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "total_senales": len(senales),
            "signals": senales,
            "last_scan": AUTO_SCAN_DATA["last_scan"]
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "signals": []
        }


# Alias en español
@app.get("/escanear")
def scan_alias():
    return scan()


@app.get("/senales")
def signals_alias():
    return signals_endpoint()


# ---------------------------------
# HISTORIAL
# ---------------------------------
@app.get("/history")
def history():
    try:
        if cargar_historial:
            data = cargar_historial()
            if isinstance(data, list):
                return data
            return {"data": data}

        return []
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e)
        }


@app.get("/learning-stats")
def learning_stats():
    try:
        if obtener_estadisticas_historial:
            stats = obtener_estadisticas_historial()
            if isinstance(stats, dict):
                return stats

        total = len(AUTO_SCAN_DATA["signals"])

        return {
            "total_senales": total,
            "ganadas": 0,
            "perdidas": 0,
            "win_rate": 0,
            "roi_percent": 0
        }

    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e)
        }


# ---------------------------------
# AUTO SCAN STATUS
# ---------------------------------
@app.get("/auto-scan/status")
def auto_scan_status():
    return {
        "status": "ok",
        "auto_scan_activo": AUTO_SCAN_DATA["auto_scan_activo"],
        "intervalo_segundos": AUTO_SCAN_DATA["intervalo_segundos"],
        "ultimo_scan": AUTO_SCAN_DATA["last_scan"],
        "partidos_cache": len(AUTO_SCAN_DATA["partidos"]),
        "senales_cache": len(AUTO_SCAN_DATA["signals"])
}

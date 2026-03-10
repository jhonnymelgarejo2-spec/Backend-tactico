from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from datetime import datetime
import traceback

from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

try:
    from history_store import (
        cargar_historial,
        guardar_senales_en_historial,
        obtener_estadisticas_historial,
    )
except Exception:
    cargar_historial = None
    guardar_senales_en_historial = None
    obtener_estadisticas_historial = None


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

# ------------------------------
# CACHE SIMPLE EN MEMORIA
# ------------------------------

CACHE_PARTIDOS = []
CACHE_SENALES = []
ULTIMO_SCAN = None
AUTO_SCAN_ACTIVO = True
INTERVALO_SEGUNDOS = 30

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"


def ahora_iso():
    return datetime.utcnow().isoformat()


def scan_interno():
    global CACHE_PARTIDOS, CACHE_SENALES, ULTIMO_SCAN

    partidos = obtener_partidos_en_vivo()
    senales = generar_senales(partidos)

    CACHE_PARTIDOS = partidos if isinstance(partidos, list) else []
    CACHE_SENALES = senales if isinstance(senales, list) else []
    ULTIMO_SCAN = ahora_iso()

    if guardar_senales_en_historial:
        try:
            guardar_senales_en_historial(CACHE_SENALES)
        except Exception:
            pass

    return CACHE_PARTIDOS, CACHE_SENALES


# ------------------------------
# FRONTEND
# ------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)

    return HTMLResponse("""
    <html>
      <head>
        <meta charset="utf-8">
        <title>Backend táctico</title>
      </head>
      <body style="background:#07111f;color:white;font-family:Arial;padding:20px">
        <h2>Backend táctico funcionando</h2>
        <p>No se encontró static/index.html</p>
      </body>
    </html>
    """)


@app.get("/favicon.ico")
def favicon():
    return HTMLResponse(status_code=204, content="")


# ------------------------------
# DEBUG / ESTADO
# ------------------------------

@app.get("/status")
def estado_backend():
    return {
        "status": "ok",
        "backend": "activo",
        "motor": "tactico",
        "auto_scan": "activo" if AUTO_SCAN_ACTIVO else "inactivo",
        "ultimo_scan": ULTIMO_SCAN,
        "partidos_cache": len(CACHE_PARTIDOS),
        "senales_cache": len(CACHE_SENALES),
    }


@app.get("/ping")
def ping():
    return {
        "ping": "pong",
        "mensaje": "Servidor activo"
    }


@app.get("/debug-routes")
def debug_routes():
    return {
        "status": "ok",
        "rutas": [
            "/",
            "/status",
            "/ping",
            "/debug-routes",
            "/partidos-en-vivo",
            "/scan",
            "/signals",
            "/history",
            "/learning-stats",
            "/auto-scan/status",
        ]
    }


# ------------------------------
# PARTIDOS EN VIVO
# ------------------------------

@app.get("/partidos-en-vivo")
def partidos_en_vivo():
    try:
        partidos = obtener_partidos_en_vivo()

        return {
            "estado": "OK",
            "total_partidos": len(partidos) if isinstance(partidos, list) else 0,
            "partidos": partidos if isinstance(partidos, list) else []
        }

    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "trace": traceback.format_exc()
        }


# ------------------------------
# SCAN
# ------------------------------

@app.get("/scan")
def scan():
    try:
        partidos, senales = scan_interno()

        return {
            "estado": "OK",
            "mensaje": "Scan ejecutado correctamente",
            "partidos_analizados": len(partidos),
            "senales_detectadas": len(senales),
            "ultimo_scan": ULTIMO_SCAN,
            "partidos": partidos,
            "signals": senales
        }

    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "trace": traceback.format_exc(),
            "partidos": [],
            "signals": []
        }


# ------------------------------
# SIGNALS
# ------------------------------

@app.get("/signals")
def signals():
    try:
        global CACHE_PARTIDOS, CACHE_SENALES

        if not CACHE_PARTIDOS:
            scan_interno()

        return {
            "estado": "OK",
            "total_partidos": len(CACHE_PARTIDOS),
            "total_senales": len(CACHE_SENALES),
            "ultimo_scan": ULTIMO_SCAN,
            "signals": CACHE_SENALES
        }

    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "trace": traceback.format_exc(),
            "signals": []
        }


# ------------------------------
# HISTORIAL
# ------------------------------

@app.get("/history")
def history():
    try:
        if cargar_historial:
            data = cargar_historial()

            if isinstance(data, list):
                return data

            return {
                "estado": "OK",
                "data": data
            }

        return []

    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "trace": traceback.format_exc()
        }


# ------------------------------
# LEARNING STATS
# ------------------------------

@app.get("/learning-stats")
def learning_stats():
    try:
        if obtener_estadisticas_historial:
            stats = obtener_estadisticas_historial()
            if isinstance(stats, dict):
                return stats

        total = len(CACHE_SENALES)
        confianza_prom = 0
        value_prom = 0

        if total > 0:
            confianza_prom = round(
                sum(float(s.get("confidence", 0) or 0) for s in CACHE_SENALES) / total,
                2
            )
            value_prom = round(
                sum(float(s.get("value", 0) or 0) for s in CACHE_SENALES) / total,
                2
            )

        return {
            "total_senales": total,
            "pendientes": total,
            "ganadas": 0,
            "perdidas": 0,
            "nulas": 0,
            "win_rate": 0,
            "roi_percent": 0,
            "profit_units": 0,
            "confianza_promedio": confianza_prom,
            "value_promedio": value_prom,
            "ligas_top": [],
            "mercados_top": []
        }

    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "trace": traceback.format_exc()
        }


# ------------------------------
# AUTO SCAN STATUS
# ------------------------------

@app.get("/auto-scan/status")
def auto_scan_status():
    return {
        "status": "ok",
        "auto_scan_activo": AUTO_SCAN_ACTIVO,
        "intervalo_segundos": INTERVALO_SEGUNDOS,
        "ultimo_scan": ULTIMO_SCAN,
        "partidos_cache": len(CACHE_PARTIDOS),
        "senales_cache": len(CACHE_SENALES),
    }

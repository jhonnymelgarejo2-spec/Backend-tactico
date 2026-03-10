from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from datetime import datetime
import traceback

from live_router import router as live_router
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

# Si estos imports fallan en tu proyecto, me pegas el error exacto
# y te doy la versión adaptada a tus nombres reales.
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

# Router pequeño: solo partidos en vivo
app.include_router(live_router)

# Cache simple en memoria
CACHE_PARTIDOS = []
CACHE_SENALES = []
ULTIMO_SCAN = None
AUTO_SCAN_ACTIVO = True
INTERVALO_SEGUNDOS = 30


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"


def _ahora_iso():
    return datetime.utcnow().isoformat()


def _scan_interno():
    global CACHE_PARTIDOS, CACHE_SENALES, ULTIMO_SCAN

    partidos = obtener_partidos_en_vivo()
    senales = generar_senales(partidos)

    CACHE_PARTIDOS = partidos
    CACHE_SENALES = senales
    ULTIMO_SCAN = _ahora_iso()

    # Guardado opcional en historial
    if guardar_senales_en_historial:
        try:
            guardar_senales_en_historial(senales)
        except Exception:
            pass

    return partidos, senales


# ------------------------------
# FRONTEND
# ------------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return HTMLResponse("""
    <html>
      <head><title>Backend táctico</title></head>
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
            "/scan",
            "/signals",
            "/history",
            "/learning-stats",
            "/auto-scan/status",
            "/partidos-en-vivo",
            "/debug-routes",
        ]
    }


# ------------------------------
# SCAN / SIGNALS
# ------------------------------

@app.get("/scan")
def scan():
    try:
        partidos, _ = _scan_interno()
        return {
            "estado": "OK",
            "partidos_analizados": len(partidos),
            "ultimo_scan": ULTIMO_SCAN,
            "partidos": partidos
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "trace": traceback.format_exc()
        }


@app.get("/signals")
def signals():
    try:
        # Si no hay cache, escanea
        if not CACHE_PARTIDOS:
            _scan_interno()

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
            "trace": traceback.format_exc()
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


@app.get("/learning-stats")
def learning_stats():
    try:
        if obtener_estadisticas_historial:
            stats = obtener_estadisticas_historial()
            if isinstance(stats, dict):
                return stats

        # fallback simple si no existe función real
        total = len(CACHE_SENALES)
        confianza_prom = 0
        value_prom = 0

        if total > 0:
            confianza_prom = round(
                sum(float(s.get("confidence", 0) or 0) for s in CACHE_SENALES) / total, 2
            )
            value_prom = round(
                sum(float(s.get("value", 0) or 0) for s in CACHE_SENALES) / total, 2
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

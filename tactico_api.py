from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from threading import Thread, Lock
from datetime import datetime
import time
import traceback

from live_router import router as live_router
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

# Historial opcional
try:
    from history_store import (
        cargar_historial,
        obtener_estadisticas_historial,
        guardar_senales_en_historial,
    )
except Exception:
    cargar_historial = None
    obtener_estadisticas_historial = None
    guardar_senales_en_historial = None


app = FastAPI(
    title="JHONNY ELITE API",
    version="V11_PRO"
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
DATA_LOCK = Lock()

AUTO_SCAN_DATA = {
    "partidos": [],
    "signals": [],
    "last_scan": None,
    "last_scan_iso": None,
    "auto_scan_activo": True,
    "intervalo_segundos": 60,
    "errores": 0,
    "ultimo_error": None,
    "backend_version": "V11_PRO"
}


# ---------------------------------
# UTILIDADES
# ---------------------------------
def ahora_ts() -> int:
    return int(time.time())


def ahora_iso() -> str:
    return datetime.utcnow().isoformat()


def normalizar_partido_crudo(p: dict) -> dict:
    """
    Convierte diferentes formatos de partido a uno solo.
    """
    local = p.get("local") or p.get("equipo_local") or p.get("home") or "Local"
    visitante = p.get("visitante") or p.get("equipo_visitante") or p.get("away") or "Visitante"
    liga = p.get("liga") or p.get("torneo") or p.get("league") or "Liga desconocida"
    pais = p.get("pais") or p.get("country") or "País desconocido"
    minuto = int(p.get("minuto", p.get("minute", 0)) or 0)
    estado_partido = p.get("estado_partido") or p.get("estado") or "en_juego"
    match_id = p.get("id", f"{local}-{visitante}-{minuto}")

    score_raw = str(
        p.get("score")
        or f"{p.get('marcador_local', 0)}-{p.get('marcador_visitante', 0)}"
    ).replace("–", "-")

    partes = score_raw.split("-")
    marcador_local = int(str(partes[0]).strip()) if len(partes) > 0 and str(partes[0]).strip().isdigit() else 0
    marcador_visitante = int(str(partes[1]).strip()) if len(partes) > 1 and str(partes[1]).strip().isdigit() else 0

    goal_pressure = p.get("goal_pressure") or {}
    goal_predictor = p.get("goal_predictor") or {}
    chaos = p.get("chaos") or {}

    return {
        "id": match_id,
        "liga": liga,
        "pais": pais,
        "local": local,
        "visitante": visitante,
        "minuto": minuto,
        "marcador_local": marcador_local,
        "marcador_visitante": marcador_visitante,
        "estado_partido": estado_partido,
        "xG": float(p.get("xG", p.get("xg", 0)) or 0),
        "momentum": p.get("momentum", "MEDIO"),
        "cuota": float(p.get("cuota", 1.85) or 1.85),
        "prob_real": float(p.get("prob_real", 0.75) or 0.75),
        "prob_implicita": float(p.get("prob_implicita", 0.54) or 0.54),
        "goal_pressure": {
            "pressure_score": float(goal_pressure.get("pressure_score", 0) or 0),
            "pressure_level": goal_pressure.get("pressure_level", "BAJA"),
            "pressure_reason": goal_pressure.get("pressure_reason", "Sin datos de presión"),
        },
        "goal_predictor": {
            "goal_next_5_prob": float(goal_predictor.get("goal_next_5_prob", 0) or 0),
            "goal_next_10_prob": float(goal_predictor.get("goal_next_10_prob", 0) or 0),
            "predictor_score": float(goal_predictor.get("predictor_score", 0) or 0),
            "alert_level": goal_predictor.get("alert_level", "BAJA"),
            "alert_reason": goal_predictor.get("alert_reason", "Sin datos de predictor"),
        },
        "chaos": {
            "chaos_score": float(chaos.get("chaos_score", 0) or 0),
            "chaos_level": chaos.get("chaos_level", "BAJO"),
            "chaos_reason": chaos.get("chaos_reason", "Sin datos de caos"),
        },
    }


def escanear_y_actualizar_memoria():
    partidos_crudos = obtener_partidos_en_vivo()
    if not isinstance(partidos_crudos, list):
        partidos_crudos = []

    partidos = [normalizar_partido_crudo(p) for p in partidos_crudos]
    senales = generar_senales(partidos)
    if not isinstance(senales, list):
        senales = []

    ts = ahora_ts()
    iso = ahora_iso()

    with DATA_LOCK:
        AUTO_SCAN_DATA["partidos"] = partidos
        AUTO_SCAN_DATA["signals"] = senales
        AUTO_SCAN_DATA["last_scan"] = ts
        AUTO_SCAN_DATA["last_scan_iso"] = iso
        AUTO_SCAN_DATA["ultimo_error"] = None

    if guardar_senales_en_historial:
        try:
            guardar_senales_en_historial(senales)
        except Exception:
            pass

    return partidos, senales


# ---------------------------------
# FUNCION DE AUTO-SCAN
# ---------------------------------
def auto_scan_loop():
    while True:
        try:
            escanear_y_actualizar_memoria()
            print("AUTO SCAN ejecutado correctamente")
        except Exception as e:
            with DATA_LOCK:
                AUTO_SCAN_DATA["errores"] += 1
                AUTO_SCAN_DATA["ultimo_error"] = str(e)

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
        "version": "V11_PRO",
        "frontend": "index.html no encontrado en /static"
    })


# ---------------------------------
# ESTADO
# ---------------------------------
@app.get("/status")
def status():
    with DATA_LOCK:
        return {
            "status": "ok",
            "service": "backend-tactico",
            "version": AUTO_SCAN_DATA["backend_version"],
            "auto_scan_activo": AUTO_SCAN_DATA["auto_scan_activo"],
            "ultimo_scan": AUTO_SCAN_DATA["last_scan"],
            "ultimo_scan_iso": AUTO_SCAN_DATA["last_scan_iso"],
            "partidos_cache": len(AUTO_SCAN_DATA["partidos"]),
            "senales_cache": len(AUTO_SCAN_DATA["signals"]),
            "errores": AUTO_SCAN_DATA["errores"],
            "ultimo_error": AUTO_SCAN_DATA["ultimo_error"],
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
            "/auto-scan/status",
            "/estado",
            "/rutas-de-depuracion",
            "/escanear",
            "/senales",
        ],
        "version": "V11_PRO"
    }


# Alias en español
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
            "/senales",
            "/history",
            "/learning-stats",
            "/auto-scan/status",
        ],
        "version": "V11_PRO"
    }


# ---------------------------------
# RUTAS PRINCIPALES
# ---------------------------------
@app.get("/scan")
def scan():
    try:
        with DATA_LOCK:
            partidos = list(AUTO_SCAN_DATA["partidos"])
            last_scan = AUTO_SCAN_DATA["last_scan"]
            last_scan_iso = AUTO_SCAN_DATA["last_scan_iso"]

        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "partidos_analizados": len(partidos),
            "partidos": partidos,
            "last_scan": last_scan,
            "last_scan_iso": last_scan_iso,
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
        with DATA_LOCK:
            partidos = list(AUTO_SCAN_DATA["partidos"])
            senales = list(AUTO_SCAN_DATA["signals"])
            last_scan = AUTO_SCAN_DATA["last_scan"]
            last_scan_iso = AUTO_SCAN_DATA["last_scan_iso"]

        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "total_senales": len(senales),
            "signals": senales,
            "last_scan": last_scan,
            "last_scan_iso": last_scan_iso,
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "signals": []
        }


@app.get("/partidos-en-vivo")
def partidos_en_vivo():
    return scan()


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

        with DATA_LOCK:
            senales = list(AUTO_SCAN_DATA["signals"])

        total = len(senales)

        confianza_promedio = 0
        value_promedio = 0

        if total > 0:
            confianza_promedio = round(
                sum(float(s.get("confidence", 0) or 0) for s in senales) / total,
                2
            )
            value_promedio = round(
                sum(float(s.get("value", 0) or 0) for s in senales) / total,
                2
            )

        return {
            "total_senales": total,
            "ganadas": 0,
            "perdidas": 0,
            "win_rate": 0,
            "roi_percent": 0,
            "confianza_promedio": confianza_promedio,
            "value_promedio": value_promedio,
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
    with DATA_LOCK:
        return {
            "status": "ok",
            "auto_scan_activo": AUTO_SCAN_DATA["auto_scan_activo"],
            "intervalo_segundos": AUTO_SCAN_DATA["intervalo_segundos"],
            "ultimo_scan": AUTO_SCAN_DATA["last_scan"],
            "ultimo_scan_iso": AUTO_SCAN_DATA["last_scan_iso"],
            "partidos_cache": len(AUTO_SCAN_DATA["partidos"]),
            "senales_cache": len(AUTO_SCAN_DATA["signals"]),
            "errores": AUTO_SCAN_DATA["errores"],
            "ultimo_error": AUTO_SCAN_DATA["ultimo_error"],
    }

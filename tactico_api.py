from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from threading import Thread, Lock
from datetime import datetime
import time
import traceback

from live_router import router as live_router
from api_football_fetcher import obtener_partidos_en_vivo
from signals import generar_senales
from ranking_engine import (
    rankear_senales,
    obtener_senal_principal,
    obtener_partidos_calientes,
)

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
    version="V13_ELITE"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(live_router)

# ---------------------------------
# RUTAS DE ARCHIVOS
# ---------------------------------
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

# ---------------------------------
# MEMORIA GLOBAL
# ---------------------------------
DATA_LOCK = Lock()

AUTO_SCAN_DATA = {
    "partidos": [],
    "signals": [],
    "hot_matches": [],
    "hero_signal": None,
    "league_explorer": {},
    "last_scan": None,
    "last_scan_iso": None,
    "auto_scan_activo": True,
    "intervalo_segundos": 60,
    "errores": 0,
    "ultimo_error": None,
    "backend_version": "V13_ELITE"
}


# ---------------------------------
# UTILIDADES
# ---------------------------------
def ahora_ts() -> int:
    return int(time.time())


def ahora_iso() -> str:
    return datetime.utcnow().isoformat()


def construir_league_explorer(partidos, senales):
    """
    Agrupa por región/país/liga para el panel estilo Sofascore.
    """
    regiones = {
        "Europa": [],
        "Sudamérica": [],
        "Norteamérica": [],
        "Asia": [],
        "África": [],
        "Otros": [],
    }

    mapa_pais_region = {
        # Europa
        "England": "Europa",
        "Spain": "Europa",
        "Italy": "Europa",
        "Germany": "Europa",
        "France": "Europa",
        "Portugal": "Europa",
        "Netherlands": "Europa",
        "Belgium": "Europa",
        "Turkey": "Europa",
        "Scotland": "Europa",
        "Croatia": "Europa",
        "Austria": "Europa",
        "Switzerland": "Europa",
        "Czech-Republic": "Europa",
        "Poland": "Europa",
        "Greece": "Europa",
        "Romania": "Europa",
        "Serbia": "Europa",
        "Denmark": "Europa",
        "Norway": "Europa",
        "Sweden": "Europa",
        "Finland": "Europa",
        "Ukraine": "Europa",
        "Europe": "Europa",

        # Sudamérica
        "Argentina": "Sudamérica",
        "Brazil": "Sudamérica",
        "Chile": "Sudamérica",
        "Colombia": "Sudamérica",
        "Uruguay": "Sudamérica",
        "Paraguay": "Sudamérica",
        "Peru": "Sudamérica",
        "Bolivia": "Sudamérica",
        "Ecuador": "Sudamérica",
        "Venezuela": "Sudamérica",
        "South-America": "Sudamérica",

        # Norteamérica
        "USA": "Norteamérica",
        "Mexico": "Norteamérica",
        "Canada": "Norteamérica",
        "Costa-Rica": "Norteamérica",
        "Honduras": "Norteamérica",
        "Guatemala": "Norteamérica",
        "El-Salvador": "Norteamérica",
        "Panama": "Norteamérica",
        "North-America": "Norteamérica",

        # Asia
        "Japan": "Asia",
        "China": "Asia",
        "South-Korea": "Asia",
        "Saudi-Arabia": "Asia",
        "Qatar": "Asia",
        "UAE": "Asia",
        "India": "Asia",
        "Iran": "Asia",
        "Iraq": "Asia",
        "Asia": "Asia",

        # África
        "Morocco": "África",
        "Egypt": "África",
        "Algeria": "África",
        "Tunisia": "África",
        "South-Africa": "África",
        "Africa": "África",
    }

    contador = {}

    for p in partidos:
        liga = p.get("liga", "Liga desconocida")
        pais = p.get("pais", "Otros")
        region = mapa_pais_region.get(pais, "Otros")

        key = (region, pais, liga)
        if key not in contador:
            contador[key] = {
                "region": region,
                "country": pais,
                "league": liga,
                "matches": 0,
                "signals": 0,
                "elite": 0,
                "top": 0,
            }

        contador[key]["matches"] += 1

    for s in senales:
        liga = s.get("league", "Liga desconocida")
        pais = s.get("country", "Otros")
        region = mapa_pais_region.get(pais, "Otros")
        rank = str(s.get("signal_rank", "NORMAL")).upper()

        key = (region, pais, liga)
        if key not in contador:
            contador[key] = {
                "region": region,
                "country": pais,
                "league": liga,
                "matches": 0,
                "signals": 0,
                "elite": 0,
                "top": 0,
            }

        contador[key]["signals"] += 1
        if rank == "ELITE":
            contador[key]["elite"] += 1
        elif rank == "TOP":
            contador[key]["top"] += 1

    for item in contador.values():
        regiones[item["region"]].append(item)

    for region in regiones:
        regiones[region].sort(
            key=lambda x: (x["signals"], x["matches"], x["elite"], x["top"]),
            reverse=True
        )

    return regiones


def normalizar_partido_crudo(p: dict) -> dict:
    """
    Normalización defensiva por si algún fetcher devuelve claves distintas.
    """
    local = p.get("local") or p.get("equipo_local") or p.get("home") or "Local"
    visitante = p.get("visitante") or p.get("equipo_visitante") or p.get("away") or "Visitante"
    liga = p.get("liga") or p.get("torneo") or p.get("league") or "Liga desconocida"
    pais = p.get("pais") or p.get("country") or "Otros"
    minuto = int(p.get("minuto", p.get("minute", 0)) or 0)
    estado_partido = p.get("estado_partido") or p.get("estado") or "en_juego"
    match_id = p.get("id", f"{local}-{visitante}-{minuto}")

    score_raw = str(
        p.get("score")
        or f"{p.get('marcador_local', 0)}-{p.get('marcador_visitante', 0)}"
    ).replace("–", "-")

    partes = score_raw.split("-")
    marcador_local = int(str(partes[0]).strip()) if len(partes) > 0 and str(partes[0]).strip().isdigit() else int(p.get("marcador_local", 0) or 0)
    marcador_visitante = int(str(partes[1]).strip()) if len(partes) > 1 and str(partes[1]).strip().isdigit() else int(p.get("marcador_visitante", 0) or 0)

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
        "goal_pressure": p.get("goal_pressure", {}) or {},
        "goal_predictor": p.get("goal_predictor", {}) or {},
        "chaos": p.get("chaos", {}) or {},
        "shots": float(p.get("shots", 0) or 0),
        "shots_on_target": float(p.get("shots_on_target", 0) or 0),
        "dangerous_attacks": float(p.get("dangerous_attacks", 0) or 0),
    }


def escanear_y_actualizar_memoria():
    partidos_crudos = obtener_partidos_en_vivo()
    if not isinstance(partidos_crudos, list):
        partidos_crudos = []

    partidos = [normalizar_partido_crudo(p) for p in partidos_crudos]

    senales = generar_senales(partidos)
    if not isinstance(senales, list):
        senales = []

    senales_rank = rankear_senales(senales)
    hero_signal = obtener_senal_principal(senales_rank)
    hot_matches = obtener_partidos_calientes(partidos, limite=6)
    league_explorer = construir_league_explorer(partidos, senales_rank)

    ts = ahora_ts()
    iso = ahora_iso()

    with DATA_LOCK:
        AUTO_SCAN_DATA["partidos"] = partidos
        AUTO_SCAN_DATA["signals"] = senales_rank
        AUTO_SCAN_DATA["hot_matches"] = hot_matches
        AUTO_SCAN_DATA["hero_signal"] = hero_signal
        AUTO_SCAN_DATA["league_explorer"] = league_explorer
        AUTO_SCAN_DATA["last_scan"] = ts
        AUTO_SCAN_DATA["last_scan_iso"] = iso
        AUTO_SCAN_DATA["ultimo_error"] = None

    if guardar_senales_en_historial:
        try:
            guardar_senales_en_historial(senales_rank)
        except Exception:
            pass

    return partidos, senales_rank, hero_signal, hot_matches, league_explorer


# ---------------------------------
# AUTO SCAN
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
        "version": "V13_ELITE",
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
            "hot_matches_cache": len(AUTO_SCAN_DATA["hot_matches"]),
            "hero_signal_disponible": AUTO_SCAN_DATA["hero_signal"] is not None,
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
            "/hero-signal",
            "/hot-matches",
            "/league-explorer",
            "/history",
            "/learning-stats",
            "/auto-scan/status",
            "/estado",
            "/rutas-de-depuracion",
            "/escanear",
            "/senales",
        ],
        "version": "V13_ELITE"
    }


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
            "/hero-signal",
            "/hot-matches",
            "/league-explorer",
            "/history",
            "/learning-stats",
            "/auto-scan/status",
        ],
        "version": "V13_ELITE"
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


@app.get("/hero-signal")
def hero_signal():
    try:
        with DATA_LOCK:
            hero = AUTO_SCAN_DATA["hero_signal"]
            last_scan = AUTO_SCAN_DATA["last_scan"]
            last_scan_iso = AUTO_SCAN_DATA["last_scan_iso"]

        return {
            "estado": "OK",
            "hero_signal": hero,
            "last_scan": last_scan,
            "last_scan_iso": last_scan_iso,
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "hero_signal": None
        }


@app.get("/hot-matches")
def hot_matches():
    try:
        with DATA_LOCK:
            partidos = list(AUTO_SCAN_DATA["hot_matches"])
            last_scan = AUTO_SCAN_DATA["last_scan"]
            last_scan_iso = AUTO_SCAN_DATA["last_scan_iso"]

        return {
            "estado": "OK",
            "total_hot_matches": len(partidos),
            "hot_matches": partidos,
            "last_scan": last_scan,
            "last_scan_iso": last_scan_iso,
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "hot_matches": []
        }


@app.get("/league-explorer")
def league_explorer():
    try:
        with DATA_LOCK:
            data = dict(AUTO_SCAN_DATA["league_explorer"])
            last_scan = AUTO_SCAN_DATA["last_scan"]
            last_scan_iso = AUTO_SCAN_DATA["last_scan_iso"]

        return {
            "estado": "OK",
            "league_explorer": data,
            "last_scan": last_scan,
            "last_scan_iso": last_scan_iso,
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "league_explorer": {}
        }


@app.get("/partidos-en-vivo")
def partidos_en_vivo():
    return scan()


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
        riesgo_medio = 0

        if total > 0:
            confianza_promedio = round(
                sum(float(s.get("confidence", 0) or 0) for s in senales) / total,
                2
            )
            value_promedio = round(
                sum(float(s.get("value", 0) or 0) for s in senales) / total,
                2
            )
            riesgo_medio = round(
                sum(float(s.get("risk_score", 0) or 0) for s in senales) / total,
                2
            )

        elite = sum(1 for s in senales if str(s.get("signal_rank", "")).upper() == "ELITE")
        top = sum(1 for s in senales if str(s.get("signal_rank", "")).upper() == "TOP")

        return {
            "total_senales": total,
            "ganadas": 0,
            "perdidas": 0,
            "win_rate": 0,
            "roi_percent": 0,
            "confianza_promedio": confianza_promedio,
            "value_promedio": value_promedio,
            "riesgo_medio": riesgo_medio,
            "signals_elite": elite,
            "signals_top": top,
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
            "hot_matches_cache": len(AUTO_SCAN_DATA["hot_matches"]),
            "hero_signal_disponible": AUTO_SCAN_DATA["hero_signal"] is not None,
            "errores": AUTO_SCAN_DATA["errores"],
            "ultimo_error": AUTO_SCAN_DATA["ultimo_error"],
}

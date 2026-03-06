from fastapi import APIRouter
from providers import obtener_partidos_demo
from scanner import filtrar_partidos
from signals import generar_senales
from history_store import (
    guardar_senales_en_historial,
    cargar_historial,
    obtener_estadisticas_historial
)
import asyncio
from datetime import datetime

router = APIRouter()

CACHE_PARTIDOS = []
CACHE_SENALES = []
AUTO_SCAN_ACTIVO = False
ULTIMO_SCAN = None
INTERVALO_SEGUNDOS = 30


def ejecutar_scan(max_partidos: int = 40):
    global CACHE_PARTIDOS, CACHE_SENALES, ULTIMO_SCAN

    partidos = obtener_partidos_demo()
    partidos = filtrar_partidos(partidos, max_partidos=max_partidos)

    CACHE_PARTIDOS = partidos
    CACHE_SENALES = generar_senales(partidos)
    ULTIMO_SCAN = datetime.utcnow().isoformat()

    guardar_senales_en_historial(CACHE_SENALES)

    return {
        "status": "ok",
        "scanned": len(CACHE_PARTIDOS),
        "signals": len(CACHE_SENALES),
        "ultimo_scan": ULTIMO_SCAN,
        "partidos": CACHE_PARTIDOS,
    }


async def loop_auto_scan():
    global AUTO_SCAN_ACTIVO

    while AUTO_SCAN_ACTIVO:
        try:
            ejecutar_scan(max_partidos=40)
        except Exception as e:
            print(f"⚠️ Error en AUTO-SCAN: {e}")

        await asyncio.sleep(INTERVALO_SEGUNDOS)


@router.get("/scan")
def scan():
    return ejecutar_scan(max_partidos=40)


@router.get("/signals")
def signals():
    return CACHE_SENALES


@router.get("/history")
def history():
    return cargar_historial()


@router.get("/learning-stats")
def learning_stats():
    return obtener_estadisticas_historial()


@router.post("/auto-scan/start")
async def auto_scan_start():
    global AUTO_SCAN_ACTIVO

    if AUTO_SCAN_ACTIVO:
        return {
            "status": "ok",
            "message": "AUTO-SCAN ya estaba activo",
            "intervalo_segundos": INTERVALO_SEGUNDOS
        }

    AUTO_SCAN_ACTIVO = True
    asyncio.create_task(loop_auto_scan())

    return {
        "status": "ok",
        "message": "AUTO-SCAN iniciado",
        "intervalo_segundos": INTERVALO_SEGUNDOS
    }


@router.post("/auto-scan/stop")
def auto_scan_stop():
    global AUTO_SCAN_ACTIVO
    AUTO_SCAN_ACTIVO = False

    return {
        "status": "ok",
        "message": "AUTO-SCAN detenido"
    }


@router.get("/auto-scan/status")
def auto_scan_status():
    return {
        "status": "ok",
        "auto_scan_activo": AUTO_SCAN_ACTIVO,
        "intervalo_segundos": INTERVALO_SEGUNDOS,
        "ultimo_scan": ULTIMO_SCAN,
        "partidos_cache": len(CACHE_PARTIDOS),
        "senales_cache": len(CACHE_SENALES)
    }

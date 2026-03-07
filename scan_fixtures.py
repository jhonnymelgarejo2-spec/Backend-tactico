from fastapi import APIRouter
from pydantic import BaseModel
from providers import obtener_partidos_demo
from scanner import filtrar_partidos
from signals import generar_senales
from history_store import (
    guardar_senales_en_historial,
    cargar_historial,
    obtener_estadisticas_historial,
    actualizar_resultado_senal
)
import asyncio
from datetime import datetime

router = APIRouter()

CACHE_PARTIDOS = []
CACHE_SENALES = []
AUTO_SCAN_ACTIVO = False
ULTIMO_SCAN = None
INTERVALO_SEGUNDOS = 30
MAX_TOP_SIGNALS = 12


class ResolverResultadoRequest(BaseModel):
    index: int
    estado_resultado: str
    resultado_real: str | None = None


def limpiar_senal_para_api(s):
    """
    Devuelve una versión limpia de la señal para el dashboard/API.
    """
    return {
        "match_id": s.get("match_id", ""),
        "home": s.get("home", ""),
        "away": s.get("away", ""),
        "league": s.get("league", ""),
        "event_type": s.get("event_type", ""),
        "minute": s.get("minute", 0),
        "score": s.get("score", "0-0"),
        "market": s.get("market", ""),
        "selection": s.get("selection", ""),
        "odd": s.get("odd", 0),
        "prob": s.get("prob", 0),
        "value": s.get("value", 0),
        "confidence": s.get("confidence", 0),
        "reason": s.get("reason", "")
    }


def obtener_top_senales(senales, limite=MAX_TOP_SIGNALS):
    """
    Ordena y selecciona las mejores señales.
    """
    if not senales:
        return []

    ordenadas = sorted(
        senales,
        key=lambda s: (
            float(s.get("confidence", 0) or 0),
            float(s.get("value", 0) or 0),
            float(s.get("prob", 0) or 0)
        ),
        reverse=True
    )

    limpias = [limpiar_senal_para_api(s) for s in ordenadas[:limite]]
    return limpias


def ejecutar_scan(max_partidos: int = 40):
    global CACHE_PARTIDOS, CACHE_SENALES, ULTIMO_SCAN

    partidos = obtener_partidos_demo()
    partidos = filtrar_partidos(partidos, max_partidos=max_partidos)

    CACHE_PARTIDOS = partidos

    try:
        senales_generadas = generar_senales(partidos)
        CACHE_SENALES = obtener_top_senales(senales_generadas, limite=MAX_TOP_SIGNALS)
    except Exception as e:
        print(f"⚠️ Error generando señales: {e}")
        CACHE_SENALES = []

    ULTIMO_SCAN = datetime.utcnow().isoformat()

    try:
        guardar_senales_en_historial(CACHE_SENALES)
    except Exception as e:
        print(f"⚠️ Error guardando historial: {e}")

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
    try:
        return CACHE_SENALES if CACHE_SENALES is not None else []
    except Exception as e:
        return {
            "status": "error",
            "detalle": str(e),
            "signals": []
        }


@router.get("/history")
def history():
    return cargar_historial()


@router.get("/learning-stats")
def learning_stats():
    return obtener_estadisticas_historial()


@router.post("/history/resolve")
def history_resolve(payload: ResolverResultadoRequest):
    return actualizar_resultado_senal(
        index=payload.index,
        estado_resultado=payload.estado_resultado,
        resultado_real=payload.resultado_real
    )


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

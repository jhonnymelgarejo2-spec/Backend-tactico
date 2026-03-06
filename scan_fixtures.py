from fastapi import APIRouter
from providers import obtener_partidos_demo
from scanner import filtrar_partidos
from signals import generar_senales
from history_store import (
    guardar_senales_en_historial,
    cargar_historial,
    obtener_estadisticas_historial
)

router = APIRouter()

CACHE_PARTIDOS = []
CACHE_SENALES = []

@router.get("/scan")
def scan():
    global CACHE_PARTIDOS, CACHE_SENALES

    partidos = obtener_partidos_demo()
    partidos = filtrar_partidos(partidos, max_partidos=40)

    CACHE_PARTIDOS = partidos
    CACHE_SENALES = generar_senales(partidos)

    # guardar señales detectadas en memoria/historial
    guardar_senales_en_historial(CACHE_SENALES)

    return {
        "status": "ok",
        "scanned": len(CACHE_PARTIDOS),
        "signals": len(CACHE_SENALES),
        "partidos": CACHE_PARTIDOS,
    }

@router.get("/signals")
def signals():
    return CACHE_SENALES

@router.get("/history")
def history():
    return cargar_historial()

@router.get("/learning-stats")
def learning_stats():
    return obtener_estadisticas_historial()

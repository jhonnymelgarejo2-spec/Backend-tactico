from fastapi import APIRouter
from providers import obtener_partidos_demo
from scanner import filtrar_partidos
from signals import generar_senales

router = APIRouter()

# guarda cache simple en memoria
CACHE_PARTIDOS = []
CACHE_SENALES = []

@router.get("/scan")
def scan():
    global CACHE_PARTIDOS, CACHE_SENALES
    partidos = obtener_partidos_demo()
    partidos = filtrar_partidos(partidos, max_partidos=60)

    CACHE_PARTIDOS = partidos
    CACHE_SENALES = generar_senales(partidos)

    return {
        "status": "ok",
        "scanned": len(CACHE_PARTIDOS),
        "signals": len(CACHE_SENALES),
        "partidos": CACHE_PARTIDOS,
    }

@router.get("/signals")
def signals():
    return CACHE_SENALES

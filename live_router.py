from fastapi import APIRouter
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales
from history_store import cargar_historial, obtener_estadisticas_historial

router = APIRouter()


@router.get("/partidos-en-vivo")
def partidos_en_vivo():
    try:
        partidos = obtener_partidos_en_vivo()
        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "partidos": partidos
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e)
        }


@router.get("/signals")
def obtener_signals():
    try:
        partidos = obtener_partidos_en_vivo()
        senales = generar_senales(partidos)
        return {
            "estado": "OK",
            "total_partidos": len(partidos),
            "total_senales": len(senales),
            "signals": senales
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "signals": []
        }


@router.get("/scan")
def scan():
    try:
        partidos = obtener_partidos_en_vivo()
        senales = generar_senales(partidos)
        return {
            "estado": "OK",
            "mensaje": "Scan ejecutado correctamente",
            "partidos_analizados": len(partidos),
            "senales_detectadas": len(senales),
            "partidos": partidos,
            "signals": senales
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "partidos": [],
            "signals": []
        }


@router.get("/history")
def history():
    try:
        historial = cargar_historial()
        return {
            "estado": "OK",
            "total": len(historial),
            "data": historial
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "total": 0,
            "data": []
        }


@router.get("/learning-stats")
def learning_stats():
    try:
        stats = obtener_estadisticas_historial()
        return {
            "estado": "OK",
            **stats
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "total_senales": 0,
            "pendientes": 0,
            "resueltas": 0,
            "ganadas": 0,
            "perdidas": 0,
            "nulas": 0,
            "win_rate": 0,
            "roi_percent": 0,
            "profit_units": 0,
            "confidence_promedio": 0,
            "value_promedio": 0,
            "ligas_top": [],
            "mercados_top": []
        }


@router.get("/auto-scan/status")
def auto_scan_status():
    return {
        "estado": "OK",
        "auto_scan_activo": True,
        "mensaje": "AUTO-SCAN operativo"
        }

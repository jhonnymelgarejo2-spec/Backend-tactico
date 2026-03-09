from fastapi import APIRouter
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

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
        return {
            "estado": "OK",
            "data": []
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "data": []
        }


@router.get("/learning-stats")
def learning_stats():
    try:
        return {
            "estado": "OK",
            "total_senales": 0,
            "ganadas": 0,
            "perdidas": 0,
            "win_rate": 0,
            "roi_percent": 0
        }
    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e),
            "total_senales": 0,
            "ganadas": 0,
            "perdidas": 0,
            "win_rate": 0,
            "roi_percent": 0
        }


@router.get("/auto-scan/status")
def auto_scan_status():
    return {
        "estado": "OK",
        "auto_scan_activo": True,
        "mensaje": "AUTO-SCAN operativo"
        }

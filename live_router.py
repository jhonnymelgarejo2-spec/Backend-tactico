from fastapi import APIRouter
from sofascore_fetcher import obtener_partidos_en_vivo
from signals import generar_senales

router = APIRouter()


# PARTIDOS EN VIVO
@router.get("/partidos-en-vivo")
def partidos_en_vivo():
    try:
        datos = obtener_partidos_en_vivo()

        return {
            "estado": "OK",
            "total_partidos": len(datos),
            "partidos": datos
        }

    except Exception as e:
        return {
            "estado": "error",
            "detalle": str(e)
        }


# SEÑALES DEL SISTEMA
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
            "detalle": str(e)
        }

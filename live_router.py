from fastapi import APIRouter
from sofascore_fetcher import obtener_partidos_en_vivo

router = APIRouter()

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

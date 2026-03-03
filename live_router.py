from fastapi import APIRouter
from sofascore_fetcher import obtener_partidos_en_vivo

router = APIRouter()

@router.get("/partidos-en-vivo")
async def partidos_en_vivo():
    try:
        datos = obtener_partidos_en_vivo()
        return {"estado": "OK", "partidos": datos}
    except Exception as e:
        print(f"⚠ Error al obtener partidos en vivo: {e}")
        return {"estado": "error", "detalle": str(e)}

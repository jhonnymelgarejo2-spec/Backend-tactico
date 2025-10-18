from fastapi import APIRouter
from sofascore_fetcher import obtener_partidos_en_vivo

router = APIRouter()

@router.get("/partidos-en-vivo")
async def partidos_en_vivo():
    return await obtener_partidos_en_vivo()

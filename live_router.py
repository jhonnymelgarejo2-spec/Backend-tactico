# 📦 Importaciones necesarias
from fastapi import APIRouter
from sofascore_fetcher import obtener_partidos_en_vivo

# 🚀 Inicializar router táctico
router = APIRouter()

# 📡 Endpoint para consultar partidos en vivo desde Sofascore
@router.get("/partidos-en-vivo")
async def partidos_en_vivo():
    try:
        datos = await obtener_partidos_en_vivo()
        return {"status": "ok", "partidos": datos}
    except Exception as e:
        print(f"⚠️ Error al obtener partidos en vivo: {e}")
        return {"status": "error", "detalle": str(e)}

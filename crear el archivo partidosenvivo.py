from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/partidos-en-vivo")
def partidos_en_vivo():
    # Simulación de respuesta o conexión con tu API real
    return {
        "status": "ok",
        "partidos": [
            {
                "torneo": "Elite League",
                "equipo_local": "Argentina",
                "equipo_visitante": "Brasil",
                "minuto": 67,
                "score": "2–1",
                "estado": "en_juego",
                "id": 12345
            }
        ]
    }

import requests
import os
from fastapi import APIRouter

router = APIRouter()

@router.get("/partidos-en-vivo")
def partidos_en_vivo():
    url = "https://footapi7.p.rapidapi.com/api/matches/live"

    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": os.getenv("RAPIDAPI_HOST")
    }

    response = requests.get(url, headers=headers)
    data = response.json()

    partidos = []
    for match in data.get("matches", []):
        partidos.append({
            "torneo": match["tournament"]["name"],
            "equipo_local": match["homeTeam"]["name"],
            "equipo_visitante": match["awayTeam"]["name"],
            "minuto": match["time"]["minute"],
            "score": f'{match["homeScore"]["current"]}–{match["awayScore"]["current"]}',
            "estado": match["status"]["type"],
            "logo_local": match["homeTeam"]["logo"],
            "logo_visitante": match["awayTeam"]["logo"]
        })

    return {"status": "ok", "partidos": partidos}

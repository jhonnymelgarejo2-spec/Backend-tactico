import os
import requests
from fastapi import APIRouter

router = APIRouter()

@router.get("/scan-fixtures")
def scan_fixtures():
    url = "https://free-football-soccer-videos.p.rapidapi.com/fixtures"
    headers = {
        "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": os.getenv("RAPIDAPI_HOST")
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return {"error": "No se pudo obtener los datos", "status": response.status_code}

    data = response.json()
    fixtures = []

    for match in data.get("fixtures", []):
        fixture = {
            "fecha": match.get("date"),
            "liga": match.get("league", {}).get("name"),
            "local": match.get("homeTeam", {}).get("name"),
            "visitante": match.get("awayTeam", {}).get("name"),
            "estado": match.get("status"),
            "goles_local": match.get("goals", {}).get("home"),
            "goles_visitante": match.get("goals", {}).get("away")
        }
        fixtures.append(fixture)

    return {"partidos": fixtures}

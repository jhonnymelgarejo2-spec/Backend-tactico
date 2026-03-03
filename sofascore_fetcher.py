import requests

def obtener_partidos_en_vivo():
    url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json()

        resultados = []
        for match in data.get("events", []):
            resultados.append({
                "torneo": match["tournament"]["name"],
                "equipo_local": match["homeTeam"]["name"],
                "equipo_visitante": match["awayTeam"]["name"],
                "minuto": match.get("time", {}).get("currentPeriodStartMinute", 0),
                "score": f"{match['homeScore']['current']}–{match['awayScore']['current']}",
                "estado": match["status"]["type"],
                "id": match["id"]
            })

        if not resultados:
            return [{
                "torneo": "Sin partidos",
                "equipo_local": "-",
                "equipo_visitante": "-",
                "minuto": 0,
                "score": "0–0",
                "estado": "sin_eventos",
                "id": 0
            }]

        return resultados

    except Exception as e:
        print(f"⚠ Error en Sofascore: {e}")
        return [{
            "torneo": "Error",
            "equipo_local": "Sin datos",
            "equipo_visitante": "Sin datos",
            "minuto": 0,
            "score": "0–0",
            "estado": "error",
            "id": 0
        }]

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

        return resultados if resultados else []

    except Exception as e:
        print(f"⚠ Error en Sofascore: {e}")
        return []

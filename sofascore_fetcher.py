import requests

def obtener_partidos_en_vivo():
    url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.sofascore.com/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()

        resultados = []
        for match in data.get("events", []):
            resultados.append({
                "torneo": match["tournament"]["name"],
                "equipo_local": match["homeTeam"]["name"],
                "equipo_visitante": match["awayTeam"]["name"],
                "minuto": match.get("time", {}).get("currentPeriodStartMinute", 0),
                "score": f'{match["homeScore"]["current"]}–{match["awayScore"]["current"]}',
                "estado": match["status"]["type"],
                "id": match["id"]
            })

        return resultados

    except Exception as e:
        print("⚠️ Sofascore bloqueó o falló:", e)
        return []

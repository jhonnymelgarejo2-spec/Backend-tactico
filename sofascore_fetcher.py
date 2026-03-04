import requests

def obtener_partidos_en_vivo():
    url = "https://api.sofascore.com/api/v1/sport/football/events/live"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Referer": "https://www.sofascore.com/"
    }

    try:
        r = requests.get(url, headers=headers, timeout=15)

        # Si Sofascore bloquea (403), hacemos fallback
        if r.status_code == 403:
            return [{
                "torneo": "Demo (Sofascore bloqueado)",
                "equipo_local": "Argentina",
                "equipo_visitante": "Brasil",
                "minuto": 45,
                "score": "2–1",
                "estado": "en_juego",
                "id": 99999
            }]

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

        # Si no hay eventos, no es error
        if not resultados:
            return []

        return resultados

    except Exception as e:
        print("⚠️ Error Sofascore:", e)
        # fallback por error general
        return [{
            "torneo": "Demo (Error)",
            "equipo_local": "Equipo A",
            "equipo_visitante": "Equipo B",
            "minuto": 0,
            "score": "0–0",
            "estado": "sin_datos",
            "id": 0
        }]

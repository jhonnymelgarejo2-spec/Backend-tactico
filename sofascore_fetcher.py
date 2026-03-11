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

        # Si Sofascore bloquea
        if r.status_code == 403:
            return [{
                "id": 99999,
                "liga": "Demo (Sofascore bloqueado)",
                "pais": "Demo",
                "local": "Argentina",
                "visitante": "Brasil",
                "minuto": 45,
                "marcador_local": 2,
                "marcador_visitante": 1,
                "estado_partido": "en_juego",
                "xG": 0,
                "momentum": "MEDIO",
                "cuota": 1.85,
                "prob_real": 0.75,
                "prob_implicita": 0.54,
                "goal_pressure": {
                    "pressure_score": 0,
                    "pressure_level": "BAJA"
                },
                "goal_predictor": {
                    "goal_next_5_prob": 0.0,
                    "goal_next_10_prob": 0.0,
                    "predictor_score": 0,
                    "alert_level": "BAJA",
                    "alert_reason": "Sin datos de predictor"
                },
                "chaos": {
                    "chaos_score": 0,
                    "chaos_level": "BAJO",
                    "chaos_reason": "Sin datos de caos"
                }
            }]

        r.raise_for_status()
        data = r.json()

        resultados = []

        for match in data.get("events", []):
            home_score = (match.get("homeScore") or {}).get("current", 0)
            away_score = (match.get("awayScore") or {}).get("current", 0)

            tournament = match.get("tournament") or {}
            country = tournament.get("category") or {}
            status = match.get("status") or {}
            time_data = match.get("time") or {}

            resultados.append({
                "id": match.get("id", 0),
                "liga": tournament.get("name", "Liga desconocida"),
                "pais": country.get("name", "País desconocido"),
                "local": (match.get("homeTeam") or {}).get("name", "Local"),
                "visitante": (match.get("awayTeam") or {}).get("name", "Visitante"),
                "minuto": time_data.get("currentPeriodStartMinute", 0),
                "marcador_local": home_score,
                "marcador_visitante": away_score,
                "estado_partido": status.get("type", "en_juego"),
                "xG": 0,
                "momentum": "MEDIO",
                "cuota": 1.85,
                "prob_real": 0.75,
                "prob_implicita": 0.54,
                "goal_pressure": {
                    "pressure_score": 0,
                    "pressure_level": "BAJA"
                },
                "goal_predictor": {
                    "goal_next_5_prob": 0.0,
                    "goal_next_10_prob": 0.0,
                    "predictor_score": 0,
                    "alert_level": "BAJA",
                    "alert_reason": "Sin datos de predictor"
                },
                "chaos": {
                    "chaos_score": 0,
                    "chaos_level": "BAJO",
                    "chaos_reason": "Sin datos de caos"
                }
            })

        return resultados

    except Exception as e:
        print("⚠️ Error Sofascore:", e)
        return [{
            "id": 0,
            "liga": "Demo (Error)",
            "pais": "Demo",
            "local": "Equipo A",
            "visitante": "Equipo B",
            "minuto": 0,
            "marcador_local": 0,
            "marcador_visitante": 0,
            "estado_partido": "sin_datos",
            "xG": 0,
            "momentum": "MEDIO",
            "cuota": 1.85,
            "prob_real": 0.75,
            "prob_implicita": 0.54,
            "goal_pressure": {
                "pressure_score": 0,
                "pressure_level": "BAJA"
            },
            "goal_predictor": {
                "goal_next_5_prob": 0.0,
                "goal_next_10_prob": 0.0,
                "predictor_score": 0,
                "alert_level": "BAJA",
                "alert_reason": "Sin datos de predictor"
            },
            "chaos": {
                "chaos_score": 0,
                "chaos_level": "BAJO",
                "chaos_reason": "Sin datos de caos"
            }
        }]

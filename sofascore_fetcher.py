# Si es un módulo externo
from sofascore_api import SofascoreAPI

# O si es tu propia clase en otro archivo
from mi_modulo.sofascore import SofascoreAPI
async def obtener_partidos_en_vivo():
    try:
        api = SofascoreAPI()
        partidos = await api.get_live_matches()

        resultados = []
        for match in partidos:
            datos = {
                "torneo": match.tournament.name,
                "equipo_local": match.homeTeam.name,
                "equipo_visitante": match.awayTeam.name,
                "minuto": getattr(match.time, "currentPeriodStartMinute", 0),
                "score": f"{match.homeScore.current}–{match.awayScore.current}",
                "estado": match.status.type,
                "id": match.id
            }
            resultados.append(datos)

        await api.close()

        # 🛡️ Fallback si no hay partidos
        if not resultados:
            resultados.append({
                "torneo": "Simulado",
                "equipo_local": "Argentina",
                "equipo_visitante": "Brasil",
                "minuto": 45,
                "score": "2–1",
                "estado": "en_juego",
                "id": 99999
            })

        return resultados

    except Exception as e:
        print(f"⚠️ Error en Sofascore: {e}")
        return [{
            "torneo": "Error",
            "equipo_local": "Sin datos",
            "equipo_visitante": "Sin datos",
            "minuto": 0,
            "score": "0–0",
            "estado": "error",
            "id": 0
        }]

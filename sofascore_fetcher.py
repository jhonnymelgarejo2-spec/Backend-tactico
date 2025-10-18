import asyncio
from sofascore_wrapper.api import SofascoreAPI

async def obtener_partidos_en_vivo():
    api = SofascoreAPI()
    partidos = await api.get_live_matches()

    resultados = []
    for match in partidos:
        datos = {
            "torneo": match.tournament.name,
            "equipo_local": match.homeTeam.name,
            "equipo_visitante": match.awayTeam.name,
            "minuto": match.time.currentPeriodStartMinute,
            "score": f"{match.homeScore.current}–{match.awayScore.current}",
            "estado": match.status.type,
            "id": match.id
        }
        resultados.append(datos)

    await api.close()
    return resultados

# Para ejecutar desde móvil o backend async
if __name__ == "__main__":
    asyncio.run(obtener_partidos_en_vivo())

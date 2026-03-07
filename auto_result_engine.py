import asyncio
from history_store import cargar_historial, guardar_historial
from datetime import datetime

AUTO_RESULT_ACTIVO = True
INTERVALO_SEGUNDOS = 120


def evaluar_resultado(senal):
    
    market = senal.get("market")
    score = senal.get("score")

    if not score:
        return None

    try:
        home, away = map(int, score.split("-"))
    except:
        return None

    goles = home + away

    if market == "OVER_UNDER_0.5_NEXT_15":
        if goles > 0:
            return "ganada"
        else:
            return "perdida"

    return None


async def loop_auto_result():

    while AUTO_RESULT_ACTIVO:

        historial = cargar_historial()
        actualizado = False

        for s in historial:

            if s.get("estado_resultado") != "pendiente":
                continue

            resultado = evaluar_resultado(s)

            if resultado:
                s["estado_resultado"] = resultado
                s["resultado_real"] = "auto"
                s["resuelto_en"] = datetime.utcnow().isoformat()
                actualizado = True

        if actualizado:
            guardar_historial(historial)

        await asyncio.sleep(INTERVALO_SEGUNDOS)

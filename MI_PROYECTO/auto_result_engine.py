import asyncio
from datetime import datetime
from history_store import cargar_historial, guardar_historial

AUTO_RESULT_ACTIVO = True
INTERVALO_SEGUNDOS = 120


def parse_score(score):
    if not score:
        return None, None

    try:
        home, away = map(int, str(score).split("-"))
        return home, away
    except Exception:
        return None, None


def evaluar_resultado(senal):
    """
    Resolución DEMO del resultado.
    No usa marcador final real todavía.
    """
    market = str(senal.get("market", "") or "").strip().upper()
    score = senal.get("score")
    minute = int(senal.get("minute", 0) or 0)

    home, away = parse_score(score)
    if home is None or away is None:
        return None

    total_goles = home + away

    # Mercado: OVER 0.5 próximos 15 min
    # DEMO: si la señal apareció en una zona ofensiva útil, asumimos resolución
    if market in ["OVER_UNDER_0.5_NEXT_15", "OVER_0_5_NEXT_15"]:
        if minute <= 75:
            if total_goles >= 2:
                return "ganada"
            return "perdida"

    # Mercado: OVER 1.5 MATCH
    if market == "OVER_1_5_MATCH":
        if total_goles >= 2:
            return "ganada"
        return "perdida"

    # Mercado: HOME WIN
    if market == "HOME_WIN":
        if home > away:
            return "ganada"
        elif home < away:
            return "perdida"
        else:
            return "nula"

    # Mercado: AWAY WIN
    if market == "AWAY_WIN":
        if away > home:
            return "ganada"
        elif away < home:
            return "perdida"
        else:
            return "nula"

    # Mercado: se mantiene resultado
    if market == "RESULT_HOLDS_NEXT_15":
        return "ganada"

    return None


async def loop_auto_result():
    while AUTO_RESULT_ACTIVO:
        try:
            historial = cargar_historial()
            actualizado = False
            resueltas_ahora = 0

            for s in historial:
                if s.get("estado_resultado") != "pendiente":
                    continue

                resultado = evaluar_resultado(s)

                if resultado:
                    s["estado_resultado"] = resultado
                    s["resultado_real"] = "auto_demo"
                    s["resuelto_en"] = datetime.utcnow().isoformat()
                    actualizado = True
                    resueltas_ahora += 1

            if actualizado:
                guardar_historial(historial)
                print(f"🧠 AUTO RESULT ENGINE: {resueltas_ahora} señales resueltas")

        except Exception as e:
            print(f"⚠️ Error en AUTO RESULT ENGINE: {e}")

        await asyncio.sleep(INTERVALO_SEGUNDOS)

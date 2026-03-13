# prediction_resolver.py

from datetime import datetime
from typing import Dict, List

from history_store import cargar_historial, actualizar_registro


def _parse_score(score: str) -> tuple[int, int]:
    try:
        limpio = str(score or "0-0").replace("–", "-")
        a, b = limpio.split("-")
        return int(a.strip()), int(b.strip())
    except Exception:
        return 0, 0


def _resolver_result_holds(item: Dict, marcador_final: str) -> str:
    marcador_inicio = item.get("score", "0-0")
    return "ganada" if marcador_inicio == marcador_final else "perdida"


def _resolver_over_market(item: Dict, marcador_final: str) -> str:
    ml_i, mv_i = _parse_score(item.get("score", "0-0"))
    ml_f, mv_f = _parse_score(marcador_final)

    goles_inicio = ml_i + mv_i
    goles_final = ml_f + mv_f
    goles_nuevos = goles_final - goles_inicio

    market = str(item.get("market", "")).upper()
    line = item.get("line")

    if market == "OVER_NEXT_15_DYNAMIC":
        return "ganada" if goles_nuevos >= 1 else "perdida"

    if market == "NEXT_GOAL":
        return "ganada" if goles_nuevos >= 1 else "perdida"

    if market == "OVER_MATCH_DYNAMIC":
        try:
            linea = float(line or 0)
            return "ganada" if goles_final > linea else "perdida"
        except Exception:
            return "perdida"

    return "perdida"


def resolver_prediccion(item: Dict, partido_final: Dict) -> str:
    market = str(item.get("market", "")).upper()
    marcador_final = partido_final.get("score_final", partido_final.get("score", "0-0"))

    if market == "RESULT_HOLDS_NEXT_15":
        return _resolver_result_holds(item, marcador_final)

    if "OVER" in market or market == "NEXT_GOAL":
        return _resolver_over_market(item, marcador_final)

    return "pendiente"


def resolver_historial_con_partidos_finalizados(partidos_finalizados: List[Dict]) -> int:
    historial = cargar_historial()
    actualizadas = 0

    mapa_finalizados = {
        str(p.get("id", "")): p for p in partidos_finalizados
    }

    for item in historial:
        if item.get("resuelto") is True:
            continue

        match_id = str(item.get("match_id", ""))
        partido_final = mapa_finalizados.get(match_id)

        if not partido_final:
            continue

        estado_partido = str(
            partido_final.get("estado_partido", partido_final.get("status", ""))
        ).lower()

        if estado_partido not in ["finalizado", "finished", "ft", "ended"]:
            continue

        resultado = resolver_prediccion(item, partido_final)

        if resultado in ["ganada", "perdida"]:
            ok = actualizar_registro(
                item["history_id"],
                {
                    "resultado_real": partido_final.get("score_final", partido_final.get("score", "0-0")),
                    "estado_resultado": resultado,
                    "resuelto": True,
                    "resolved_at": datetime.utcnow().isoformat()
                }
            )
            if ok:
                actualizadas += 1

    return actualizadas

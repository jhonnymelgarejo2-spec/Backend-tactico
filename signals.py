from typing import List, Dict
from signal_engine import generar_senal


def partido_es_apostable(p: Dict) -> tuple[bool, str]:
    minuto = int(p.get("minuto", 0) or 0)
    estado = str(p.get("estado_partido", "activo")).lower()

    if estado in ["finalizado", "finished", "ft", "ended"]:
        return False, "Partido finalizado"

    if minuto >= 88:
        return False, "Minuto demasiado alto"

    return True, "OK"


def generar_senales(partidos: List[Dict]) -> List[Dict]:
    senales = []

    for p in partidos:
        ok, motivo = partido_es_apostable(p)
        if not ok:
            continue

        datos = {
            "id": p.get("id", ""),
            "momentum": p.get("momentum", "MEDIO"),
            "xG": p.get("xG", 0),
            "prob_real": p.get("prob_real", 0.75),
            "prob_implicita": p.get("prob_implicita", 0.54),
            "cuota": p.get("cuota", 1.85),
            "minuto": p.get("minuto", 0),
            "marcador_local": p.get("marcador_local", 0),
            "marcador_visitante": p.get("marcador_visitante", 0),
            "goal_pressure": p.get("goal_pressure", {}),
            "goal_predictor": p.get("goal_predictor", {}),
            "chaos": p.get("chaos", {}),
            "estado_partido": p.get("estado_partido", "activo"),
        }

        senal = generar_senal(datos)

        if not senal:
            continue

        if senal.get("mercado") == "SIN_SEÑAL":
            continue

        if float(senal.get("valor", 0) or 0) <= 0:
            continue

        senales.append({
            "match_id": p.get("id", ""),
            "home": p.get("local", ""),
            "away": p.get("visitante", ""),
            "league": p.get("liga", ""),
            "country": p.get("pais", ""),
            "minute": p.get("minuto", 0),
            "score": f'{p.get("marcador_local", 0)}-{p.get("marcador_visitante", 0)}',
            "market": senal.get("mercado", ""),
            "selection": senal.get("apuesta", ""),
            "line": senal.get("linea"),
            "odd": senal.get("cuota", 1.85),
            "prob": senal.get("prob_real", 0.0),
            "value": senal.get("valor", 0.0),
            "confidence": senal.get("confianza", 0),
            "reason": senal.get("razon", ""),
            "tier": senal.get("tier", "NORMAL"),
            "estado_partido": p.get("estado_partido", "activo"),
            "signal_status": senal.get("signal_status", "OPEN"),
            "goal_prob_5": senal.get("goal_prob_5", 0),
            "goal_prob_10": senal.get("goal_prob_10", 0),
            "goal_prob_15": senal.get("goal_prob_15", 0),
            "all_signals": senal.get("senales_posibles", []),
        })

    senales.sort(
        key=lambda s: (
            {"PREMIUM": 3, "FUERTE": 2, "NORMAL": 1}.get(s.get("tier", "NORMAL"), 0),
            float(s.get("confidence", 0) or 0),
            float(s.get("value", 0) or 0)
        ),
        reverse=True
    )

    return senales

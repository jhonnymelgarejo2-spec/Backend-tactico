from typing import List, Dict
from signal_engine import generar_senal


def generar_senales(partidos: List[Dict]) -> List[Dict]:

    senales = []

    for p in partidos:

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

            # módulos avanzados
            "goal_pressure": p.get("goal_pressure", {}),
            "goal_predictor": p.get("goal_predictor", {}),
            "chaos": p.get("chaos", {}),
        }

        senal = generar_senal(datos)

        if not senal:
            continue

        if senal.get("mercado") == "SIN_SEÑAL":
            continue

        if senal.get("valor", 0) <= 0:
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

            # datos tácticos
            "estado_partido": senal.get("estado_partido", {}),
            "gol_inminente": senal.get("gol_inminente", {}),
            "equipo_con_mas_peligro": senal.get("equipo_con_mas_peligro"),
            "remontada": senal.get("remontada", {}),

            # señales alternativas
            "all_signals": senal.get("senales_posibles", [])
        })

    senales.sort(
        key=lambda s: (
            {"PREMIUM": 3, "FUERTE": 2, "NORMAL": 1}.get(s.get("tier", "NORMAL"), 0),
            s.get("confidence", 0),
            s.get("value", 0)
        ),
        reverse=True
    )

    return senales

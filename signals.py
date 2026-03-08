from typing import List, Dict
from signal_engine import generar_senal

def generar_senales(partidos: List[Dict]) -> List[Dict]:
    """
    Genera señales multi-mercado usando signal_engine.py
    """
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

            # MUY IMPORTANTE: pasar nombres reales
            "equipoA": p.get("local", ""),
            "equipoB": p.get("visitante", ""),
            "liga": p.get("liga", ""),
            "tipo_evento": "Partido regular"
        }

        senal = generar_senal(datos)

        if not senal:
            continue

        if senal.get("mercado") == "SIN_SEÑAL":
            continue

        if senal.get("valor", 0) <= 0:
            continue

        senales.append({
            "match_id": senal.get("id", p.get("id", "")),

            # usar nombres reales del partido como prioridad
            "home": p.get("local", senal.get("equipoA", "")),
            "away": p.get("visitante", senal.get("equipoB", "")),
            "league": p.get("liga", senal.get("liga", "")),
            "event_type": senal.get("tipo_evento", "Partido regular"),
            "minute": p.get("minuto", senal.get("minuto", 0)),

            "score": f'{p.get("marcador_local", 0)}-{p.get("marcador_visitante", 0)}',

            "market": senal.get("mercado", ""),
            "selection": senal.get("apuesta", ""),
            "odd": senal.get("cuota", p.get("cuota", 1.85)),
            "prob": senal.get("prob_real", p.get("prob_real", 0.0)),
            "value": senal.get("valor", 0.0),
            "confidence": senal.get("confianza", 0),
            "reason": senal.get("razon", ""),
            "all_signals": senal.get("senales_posibles", [])
        })

    senales.sort(
        key=lambda s: (s.get("confidence", 0), s.get("value", 0)),
        reverse=True
    )

    return senales

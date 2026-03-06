# signals.py
from typing import List, Dict
from signal_engine import generar_senal

def generar_senales(partidos: List[Dict]) -> List[Dict]:
    """
    Genera señales multi-mercado usando signal_engine.py
    """

    senales = []

    for p in partidos:
        # armamos los datos como los espera el engine
        datos = {
            "id": p.get("id", ""),
            "momentum": p.get("momentum", "MEDIO"),
            "xG": p.get("xG", 0),
            "prob_real": p.get("prob_real", 0.75),
            "prob_implicita": p.get("prob_implicita", 0.54),
            "cuota": p.get("cuota", 1.85),
            "minuto": p.get("minuto", 0)
        }

        senal = generar_senal(datos)

        # Si el engine no detecta oportunidad clara, igual podemos ignorarla
        if senal.get("mercado") == "SIN_SEÑAL":
            continue

        # Convertimos a formato estándar del dashboard
        senales.append({
            "match_id": senal.get("id", ""),
            "home": senal.get("equipoA", ""),
            "away": senal.get("equipoB", ""),
            "league": senal.get("liga", ""),
            "event_type": senal.get("tipo_evento", ""),
            "minute": senal.get("minuto", 0),

            # En demo no tenemos marcador real por engine, así que lo tomamos del partido
            "score": f'{p.get("marcador_local", 0)}-{p.get("marcador_visitante", 0)}',

            "market": senal.get("mercado", ""),
            "selection": senal.get("apuesta", ""),
            "odd": senal.get("cuota", 1.85),
            "prob": senal.get("prob_real", 0.0),
            "value": senal.get("valor", 0.0),
            "confidence": senal.get("confianza", 0),
            "reason": senal.get("razon", ""),
            "all_signals": senal.get("senales_posibles", [])
        })

    # ordenar por confianza y luego por value
    senales.sort(
        key=lambda s: (s.get("confidence", 0), s.get("value", 0)),
        reverse=True
    )

    return senales

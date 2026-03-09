from typing import List, Dict, Tuple
from signal_engine import generar_senal


def partido_es_apostable(p: Dict) -> Tuple[bool, str]:
    minuto = int(p.get("minuto", 0) or 0)
    estado = str(p.get("estado_partido", "activo")).strip().lower()

    if estado in ["finalizado", "finished", "ft", "ended"]:
        return False, "Partido finalizado"

    if minuto >= 88:
        return False, "Minuto demasiado alto"

    return True, "OK"


def filtrar_partidos(partidos: List[Dict], max_partidos: int = 40) -> List[Dict]:
    """
    Filtra partidos válidos para escaneo.
    Evita partidos terminados o demasiado avanzados.
    """
    if not partidos:
        return []

    partidos_filtrados = []

    for p in partidos:
        ok, _ = partido_es_apostable(p)
        if not ok:
            continue

        partidos_filtrados.append(p)

    partidos_filtrados.sort(
        key=lambda p: (
            float(p.get("xG", 0) or 0),
            float((p.get("goal_pressure") or {}).get("pressure_score", 0) or 0),
            float((p.get("chaos") or {}).get("chaos_score", 0) or 0),
            float((p.get("goal_predictor") or {}).get("goal_next_10_prob", 0) or 0),
        ),
        reverse=True
    )

    return partidos_filtrados[:max_partidos]


def generar_senales(partidos: List[Dict]) -> List[Dict]:
    senales = []

    for p in partidos:
        ok, _ = partido_es_apostable(p)
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

            # módulos avanzados
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
            float(s.get("confidence", 0) or 0),
            float(s.get("value", 0) or 0)
        ),
        reverse=True
    )

    return senales

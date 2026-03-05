# scanner.py
from typing import List, Dict
from prediction_engine import run_prediction_bundle

LIGAS_FUERTES = {
    "Premier League",
    "LaLiga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
    "Primeira Liga",
    "Eredivisie",
    "Brasileirão",
    "Primera División",
    "MLS",
}

def filtrar_partidos(partidos: List[Dict], max_partidos: int = 60) -> List[Dict]:
    fuertes = [p for p in partidos if p.get("liga") in LIGAS_FUERTES]
    return fuertes[:max_partidos]


def predecir_next15(partido: Dict) -> Dict:
    """
    Ahora usa el motor real (prediction_engine.py)
    y devuelve un formato simple compatible con signals.py.
    """
    bundle = run_prediction_bundle({
        "minuto": partido.get("minuto", 0),
        "local": partido.get("local", "Equipo A"),
        "visitante": partido.get("visitante", "Equipo B"),
        "marcador_local": partido.get("marcador_local", 0),
        "marcador_visitante": partido.get("marcador_visitante", 0),
        "xG": partido.get("xG", partido.get("xg", 0.0)),
        "momentum": partido.get("momentum", "medio"),
        "prob_real": partido.get("prob_real"),
        "prob_implicita": partido.get("prob_implicita"),
        "cuota": partido.get("cuota"),
    })

    p1plus = float(bundle["pred_next15"]["p_1plus_goals"])
    return {
        "pred_next15_more_goals": p1plus,
        "pred_next15_no_goal": 1 - p1plus,
        "bundle": bundle,  # si luego quieres mostrar todo
    }

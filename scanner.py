# scanner.py
from typing import List, Dict
from prediction_engine import run_prediction_bundle
from goal_pressure_engine import calcular_goal_pressure

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


def calcular_score_partido(p: Dict) -> float:
    score = 0

    minuto = p.get("minuto", 0)
    xg = float(p.get("xG", p.get("xg", 0)) or 0)
    ml = int(p.get("marcador_local", 0))
    mv = int(p.get("marcador_visitante", 0))
    momentum = str(p.get("momentum", "medio")).lower()

    if 18 <= minuto <= 35:
        score += 3
    elif 36 <= minuto <= 75:
        score += 4
    elif 76 <= minuto <= 88:
        score += 2

    if xg >= 2.2:
        score += 4
    elif xg >= 1.5:
        score += 3
    elif xg >= 0.8:
        score += 2

    if "muy alto" in momentum:
        score += 3
    elif "alto" in momentum:
        score += 2
    elif "medio" in momentum:
        score += 1

    diff = abs(ml - mv)
    if diff == 0:
        score += 2
    elif diff == 1:
        score += 1

    if p.get("liga") in LIGAS_FUERTES:
        score += 2

    # Goal Pressure Engine suma inteligencia extra
    pressure = calcular_goal_pressure(p)
    score += pressure["pressure_score"] * 0.5

    return score


def filtrar_partidos(partidos: List[Dict], max_partidos: int = 40) -> List[Dict]:
    candidatos = []

    for p in partidos:
        pressure = calcular_goal_pressure(p)
        p["goal_pressure"] = pressure

        score = calcular_score_partido(p)

        if score >= 5:
            p["_scanner_score"] = round(score, 2)
            candidatos.append(p)

    candidatos.sort(key=lambda x: x["_scanner_score"], reverse=True)

    return candidatos[:max_partidos]


def predecir_next15(partido: Dict) -> Dict:
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
        "bundle": bundle,
        }

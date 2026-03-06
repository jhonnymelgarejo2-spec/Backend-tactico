import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"


def cargar_historial():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar_historial(historial):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=2)


def guardar_senales_en_historial(senales):
    historial = cargar_historial()

    for s in senales:
        registro = {
            "timestamp": datetime.utcnow().isoformat(),
            "match_id": s.get("match_id"),
            "home": s.get("home"),
            "away": s.get("away"),
            "minute": s.get("minute"),
            "score": s.get("score"),
            "market": s.get("market"),
            "selection": s.get("selection"),
            "odd": s.get("odd"),
            "prob": s.get("prob", s.get("prob_goal_next15")),
            "value": s.get("value"),
            "confidence": s.get("confidence"),
            "reason": s.get("reason"),
            "resultado_real": None,
            "estado_resultado": "pendiente"
        }

        historial.append(registro)

    guardar_historial(historial)


def obtener_estadisticas_historial():
    historial = cargar_historial()

    total = len(historial)
    pendientes = sum(1 for x in historial if x.get("estado_resultado") == "pendiente")
    resueltas = total - pendientes

    if total == 0:
        return {
            "total_senales": 0,
            "pendientes": 0,
            "resueltas": 0,
            "confidence_promedio": 0,
            "value_promedio": 0
        }

    confidence_promedio = round(
        sum(float(x.get("confidence", 0) or 0) for x in historial) / total, 2
    )

    value_promedio = round(
        sum(float(x.get("value", 0) or 0) for x in historial) / total, 2
    )

    return {
        "total_senales": total,
        "pendientes": pendientes,
        "resueltas": resueltas,
        "confidence_promedio": confidence_promedio,
        "value_promedio": value_promedio
      }

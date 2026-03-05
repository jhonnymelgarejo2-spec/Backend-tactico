# signals.py
from typing import List, Dict
from scanner import predecir_next15

def generar_senales(partidos: List[Dict]) -> List[Dict]:
    senales = []

    for p in partidos:
        bundle = predecir_next15(p)

        # ✅ ahora el formato fijo
        prob = float(bundle["pred_next15"]["p_plus_goals"])

        # regla simple: si prob >= 0.62 → señal OVER 0.5 next15
        if prob >= 0.62:
            odd = round(1.60 + (1 - prob) * 1.4, 2)
            value = round((prob * odd - 1) * 100, 2)

            senales.append({
                "match_id": p.get("id", ""),
                "home": p.get("local", ""),
                "away": p.get("visitante", ""),
                "minute": p.get("minuto", 0),
                "score": f'{p.get("marcador_local", 0)}-{p.get("marcador_visitante", 0)}',
                "market": "OVER_UNDER_0.5_NEXT_15",
                "selection": "OVER",
                "odd": odd,
                "prob_goal_next15": round(prob, 3),
                "value": value,
                "confidence": int(prob * 100),
                "reason": "Predicción alta de gol en próximos 15 minutos"
            })

    senales.sort(key=lambda x: x["value"], reverse=True)
    return senales

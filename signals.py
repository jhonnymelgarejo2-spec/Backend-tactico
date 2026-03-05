# signals.py
from typing import List, Dict
from scanner import predecir_next15

def generar_senales(partidos: List[Dict]) -> List[Dict]:
    """
    Genera señales de apuesta basadas en predicción (DEMO).
    Luego conectamos Odds API real.
    """
    senales = []

    for p in partidos:
        pred = predecir_next15(p)
        prob = float(pred.get("pred_next15_more_goals", 0))

        # ✅ regla simple: si prob >= 0.62 => señal OVER 0.5 next 15
        if prob >= 0.62:
            odd = round(1.60 + (1 - prob) * 1.4, 2)  # demo
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
                "prob": round(prob, 3),
                "value": value,
                "confidence": int(prob * 100),
                "reason": "Probabilidad alta de gol en próximos 15 minutos (demo)"
            })

    # ✅ ordena por mayor value primero
    senales.sort(key=lambda x: x["value"], reverse=True)
    return senales

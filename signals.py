# signals.py
from typing import List, Dict
from scanner import predecir_next15

def generar_senales(partidos: List[Dict]) -> List[Dict]:
    """
    Genera señales de apuesta basadas en predicción REAL (prediction_engine).
    Por ahora la cuota es simulada. Luego conectamos Odds API real.
    """
    senales = []

    for p in partidos:
        pred = predecir_next15(p)

        # ✅ Probabilidad real: 1+ goles en los próximos 15 min
        prob = float(pred["pred_next15"]["p_1plus_goals"])

        # ✅ regla: si prob >= 0.62 => señal OVER 0.5 next 15
        if prob >= 0.62:
            # cuota simulada (luego va con odds reales)
            odd = round(1.60 + (1 - prob) * 1.4, 2)  # aprox 1.6..2.9
            value = round((prob * odd - 1) * 100, 2)

            most = pred["pred_final"]["most_likely_score"]
            marcador_final_probable = f'{most["home"]}-{most["away"]}'
            prob_marcador = most["prob"]

            reason = pred["pred_next15"]
            detalle = (
                f"pGol15={prob:.2f} | λ15={reason['lambda_15']} | "
                f"rate={reason['rate_goals_per_min']}/min"
            )

            senales.append({
                "match_id": p.get("id", ""),
                "home": p.get("local", ""),
                "away": p.get("visitante", ""),
                "league": p.get("liga", ""),
                "minute": p.get("minuto", 0),
                "score": f'{p.get("marcador_local", 0)}-{p.get("marcador_visitante", 0)}',

                "market": "OVER_UNDER_0.5_NEXT_15",
                "selection": "OVER",
                "odd": odd,

                "prob_goal_next15": round(prob, 3),
                "value": value,
                "confidence": int(prob * 100),

                "final_score_most_likely": marcador_final_probable,
                "final_score_prob": round(prob_marcador, 4),

                "reason": detalle,
            })

    # Ordena por mayor value primero
    senales.sort(key=lambda x: x["value"], reverse=True)
    return senales

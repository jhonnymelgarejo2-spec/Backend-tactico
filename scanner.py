# scanner.py
from typing import List, Dict

# ✅ ligas fuertes (puedes agregar/quitar)
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
    """
    Filtra solo ligas fuertes y corta a máximo N partidos.
    """
    fuertes = [p for p in partidos if p.get("liga") in LIGAS_FUERTES]
    return fuertes[:max_partidos]


# ✅ NUEVO: usamos el motor real
from prediction_engine import run_prediction_bundle

def predecir_next15(partido: Dict) -> Dict:
    """
    Predicción real usando prediction_engine.py
    Devuelve:
      - pred_next15 (probabilidades próximos 15)
      - pred_final  (marcador final más probable)
      - signals     (sugerencias de mercado)
    """

    # Convertimos el partido a lo que espera el motor
    payload = {
        "minute": partido.get("minuto", 0),
        "local": partido.get("local", "Equipo A"),
        "visitante": partido.get("visitante", "Equipo B"),
        "marcador_local": partido.get("marcador_local", 0),
        "marcador_visitante": partido.get("marcador_visitante", 0),

        # Si tu partido ya trae xG, perfecto. Si no, queda 0.0 (motor usa fallback)
        "xG": partido.get("xG", partido.get("xg", 0.0)),

        # Si tienes momentum en tu data, pásalo. Si no, se usa "medio"
        "momentum": partido.get("momentum", "medio"),

        # Si en el futuro traes odds/prob, también lo soporta:
        "prob_real": partido.get("prob_real"),
        "prob_implicita": partido.get("prob_implicita"),
        "cuota": partido.get("cuota"),
    }

    bundle = run_prediction_bundle(payload)

    # Para que sea fácil de usar en /scan o /signals
    return {
        "pred_next15": bundle["pred_next15"],
        "pred_final": bundle["pred_final"],
        "signals": bundle["signals"],
}

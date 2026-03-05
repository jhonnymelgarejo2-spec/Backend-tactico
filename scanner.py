# scanner.py
from typing import List, Dict
import random

# ✅ motor real
from prediction_engine import run_prediction_bundle


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


def _safe_int(x, default=0) -> int:
    try:
        return int(x)
    except Exception:
        return default

def _safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def predecir_next15(partido: Dict) -> Dict:
    """
    ✅ Devuelve SIEMPRE este formato:
    {
      "pred_next15": {"p_plus_goals": float, "p_no_goal": float},
      "pred_final": {...},
      "signals": [...],
      "signal": {...} o None
    }
    """

    # Datos básicos (estos sí vienen del scan)
    minuto = _safe_int(partido.get("minuto", 0), 0)
    marcador_local = _safe_int(partido.get("marcador_local", 0), 0)
    marcador_visitante = _safe_int(partido.get("marcador_visitante", 0), 0)

    # 🔥 payload para el motor real
    # OJO: si no existen xG/odds todavía, ponemos defaults seguros
    payload = {
        "match_id": partido.get("id", ""),
        "home": partido.get("local", "Equipo A"),
        "away": partido.get("visitante", "Equipo B"),
        "minute": minuto,
        "score_home": marcador_local,
        "score_away": marcador_visitante,

        # 👇 Estos por ahora no vienen del scan → defaults
        "momentum": partido.get("momentum", "medio"),
        "xg_total": _safe_float(partido.get("xG", 0.0), 0.0),
        "prob_real": _safe_float(partido.get("prob_real", 0.0), 0.0),
        "prob_implicita": _safe_float(partido.get("prob_implicita", 0.0), 0.0),
        "odd": _safe_float(partido.get("cuota", 0.0), 0.0),
    }

    # ✅ Intentar motor real (prediction_engine)
    try:
        bundle = run_prediction_bundle(payload)

        # Asegura formato mínimo aunque el engine cambie
        pred_next15 = bundle.get("pred_next15") or {}
        p_plus = _safe_float(pred_next15.get("p_plus_goals", 0.0), 0.0)
        p_no = _safe_float(pred_next15.get("p_no_goal", 1.0 - p_plus), 1.0 - p_plus)

        return {
            "pred_next15": {"p_plus_goals": p_plus, "p_no_goal": p_no},
            "pred_final": bundle.get("pred_final") or {},
            "signals": bundle.get("signals") or [],
            "signal": bundle.get("signal"),
        }

    except Exception:
        # ✅ FALLBACK DEMO (para que jamás se caiga)
        base = min(0.15 + (minuto / 90) * 0.35, 0.60)
        if marcador_local == marcador_visitante:
            base += 0.07
        base += random.uniform(-0.03, 0.03)
        prob_gol_15 = max(0.05, min(base, 0.85))

        return {
            "pred_next15": {"p_plus_goals": prob_gol_15, "p_no_goal": 1 - prob_gol_15},
            "pred_final": {},
            "signals": [],
            "signal": None,
    }

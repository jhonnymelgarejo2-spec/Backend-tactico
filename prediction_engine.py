# prediction_engine.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any


# ---------------------------
# Helpers matemáticos
# ---------------------------

def poisson_pmf(k: int, lam: float) -> float:
    """P(X=k) para Poisson(lam)."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def poisson_cdf(k: int, lam: float) -> float:
    """P(X<=k) para Poisson(lam)."""
    return sum(poisson_pmf(i, lam) for i in range(0, k + 1))

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# ---------------------------
# Config / Modelo simple
# ---------------------------

MOMENTUM_MAP = {
    "bajo": 0.85,
    "medio": 1.00,
    "alto": 1.18,
    "muy alto": 1.30,
}

@dataclass
class MatchState:
    minute: int
    home: str = "Equipo A"
    away: str = "Equipo B"
    home_goals: int = 0
    away_goals: int = 0

    xg_total_so_far: float = 0.0
    xg_home_so_far: float | None = None
    xg_away_so_far: float | None = None

    momentum: str = "medio"

    prob_real: float | None = None
    prob_implicita: float | None = None
    odd: float | None = None


def _momentum_multiplier(momentum: str) -> float:
    if not momentum:
        return 1.0
    m = momentum.strip().lower()
    return MOMENTUM_MAP.get(m, 1.0)


def _estimate_goal_rate_per_min(state: MatchState) -> float:
    minute = clamp(float(state.minute), 1.0, 120.0)

    xg = max(0.0, float(state.xg_total_so_far or 0.0))
    if xg <= 0.0:
        base_rate = 2.4 / 90.0
    else:
        base_rate = xg / minute

    base_rate *= _momentum_multiplier(state.momentum)

    return clamp(base_rate, 0.005, 0.08)


def predict_goal_next_15min(state: MatchState) -> Dict[str, Any]:
    rate_per_min = _estimate_goal_rate_per_min(state)
    lam_15 = rate_per_min * 15.0

    p0 = poisson_pmf(0, lam_15)
    p1plus = 1.0 - p0
    p2plus = 1.0 - poisson_cdf(1, lam_15)

    return {
        "window_min": 15,
        "lambda_15": round(lam_15, 4),
        "p_0_goals": round(p0, 4),
        "p_1plus_goals": round(p1plus, 4),
        "p_2plus_goals": round(p2plus, 4),
        "rate_goals_per_min": round(rate_per_min, 4),
    }


def _split_team_lambdas(state: MatchState, lam_total: float) -> Tuple[float, float]:
    if state.xg_home_so_far is not None and state.xg_away_so_far is not None:
        h = max(0.0, float(state.xg_home_so_far))
        a = max(0.0, float(state.xg_away_so_far))
        s = h + a
        if s > 0:
            ph = h / s
            return lam_total * ph, lam_total * (1.0 - ph)

    return lam_total * 0.55, lam_total * 0.45


def predict_final_score(state: MatchState, max_extra_goals_each: int = 5) -> Dict[str, Any]:
    minute = clamp(float(state.minute), 0.0, 120.0)
    remaining = max(0.0, 90.0 - minute)

    rate_per_min = _estimate_goal_rate_per_min(state)
    lam_remaining_total = rate_per_min * remaining

    lam_h, lam_a = _split_team_lambdas(state, lam_remaining_total)

    dist: List[Tuple[int, int, float]] = []
    for gh in range(0, max_extra_goals_each + 1):
        ph = poisson_pmf(gh, lam_h)
        for ga in range(0, max_extra_goals_each + 1):
            pa = poisson_pmf(ga, lam_a)
            prob = ph * pa
            dist.append((state.home_goals + gh, state.away_goals + ga, prob))

    dist.sort(key=lambda x: x[2], reverse=True)
    top = dist[:10]
    best = top[0]

    expected_total = (state.home_goals + state.away_goals) + lam_remaining_total

    return {
        "minute": state.minute,
        "remaining_minutes": round(remaining, 1),
        "lambda_remaining_total": round(lam_remaining_total, 4),
        "lambda_remaining_home": round(lam_h, 4),
        "lambda_remaining_away": round(lam_a, 4),
        "expected_final_goals_total": round(expected_total, 3),
        "most_likely_score": {
            "home": best[0],
            "away": best[1],
            "prob": round(best[2], 4),
        },
        "top_scores": [{"home": h, "away": a, "prob": round(p, 4)} for (h, a, p) in top],
    }


def suggest_markets(state: MatchState) -> Dict[str, Any]:
    p15 = predict_goal_next_15min(state)

    suggestions = []

    if p15["p_1plus_goals"] >= 0.70:
        suggestions.append({
            "market": "OVER_0_5_NEXT_15",
            "why": "Alta probabilidad de al menos 1 gol en los próximos 15 minutos",
            "confidence": round(float(p15["p_1plus_goals"]) * 100, 1),
        })

    if p15["p_0_goals"] >= 0.70:
        suggestions.append({
            "market": "UNDER_0_5_NEXT_15",
            "why": "Alta probabilidad de 0 goles en los próximos 15 minutos",
            "confidence": round(float(p15["p_0_goals"]) * 100, 1),
        })

    if p15["p_0_goals"] >= 0.65:
        suggestions.append({
            "market": "RESULT_HOLDS_NEXT_15",
            "why": "Probabilidad decente de que no cambie el marcador en 15 minutos",
            "confidence": round(float(p15["p_0_goals"]) * 100, 1),
        })

    value = None
    if state.prob_real is not None and state.prob_implicita is not None:
        value = (float(state.prob_real) - float(state.prob_implicita)) * 100.0

    return {
        "next15": p15,
        "value_margin_percent": None if value is None else round(value, 2),
        "suggestions": suggestions,
        "warning": "Predicciones y señales no garantizan resultados. Usar como analítica y con responsabilidad.",
    }


def run_prediction_bundle(payload: Dict[str, Any]) -> Dict[str, Any]:
    state = MatchState(
        minute=int(payload.get("minute", payload.get("minuto", 0)) or 0),
        home=str(payload.get("home", payload.get("local", "Equipo A"))),
        away=str(payload.get("away", payload.get("visitante", "Equipo B"))),
        home_goals=int(payload.get("home_goals", payload.get("marcador_local", 0)) or 0),
        away_goals=int(payload.get("away_goals", payload.get("marcador_visitante", 0)) or 0),
        xg_total_so_far=float(payload.get("xg_total_so_far", payload.get("xG", payload.get("xg", 0.0))) or 0.0),
        xg_home_so_far=payload.get("xg_home_so_far", payload.get("xg_local")),
        xg_away_so_far=payload.get("xg_away_so_far", payload.get("xg_visitante")),
        momentum=str(payload.get("momentum", "medio")),
        prob_real=payload.get("prob_real"),
        prob_implicita=payload.get("prob_implicita"),
        odd=payload.get("odd", payload.get("cuota")),
    )

    return {
        "match": {
            "home": state.home,
            "away": state.away,
            "minute": state.minute,
            "score": f"{state.home_goals}-{state.away_goals}",
        },
        "pred_next15": predict_goal_next_15min(state),
        "pred_final": predict_final_score(state),
        "signals": suggest_markets(state),
                }   

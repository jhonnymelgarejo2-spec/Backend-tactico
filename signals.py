# signals.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from providers import LiveMatch, LiveStats, Odds

@dataclass
class Signal:
    match_id: int
    home: str
    away: str
    minute: int
    score: str

    pred_next15_goal_prob: float  # 0..1
    pred_next15_more_goals: bool
    pred_final_most_probable: str  # "1-0", "1-1", etc.

    market: str
    selection: str
    odd: float
    value: float        # valor estimado %
    confidence: int     # 0..100
    reason: str

def clamp(x: float, a: float, b: float) -> float:
    return max(a, min(b, x))

def estimate_goal_next15(match: LiveMatch, stats: LiveStats) -> float:
    """
    Heurística simple (por ahora):
    - Más tiros al arco + ataques peligrosos + xG alto => más probabilidad de gol en 15 min
    """
    sot = stats.shots_on_target_home + stats.shots_on_target_away
    dang = stats.dangerous_attacks_home + stats.dangerous_attacks_away
    xg = stats.xg_home + stats.xg_away

    # base según minuto (al final suele haber más intentos)
    minute_factor = 0.10 + (match.minute / 90) * 0.15  # 0.10..0.25

    p = (
        minute_factor
        + 0.03 * sot
        + 0.002 * dang
        + 0.08 * xg
    )
    return clamp(p, 0.02, 0.92)

def pick_best_market(p_goal: float, odds: List[Odds]) -> Optional[Odds]:
    """
    Elige el mercado:
    - si p_goal alto => OVER 0.5 next15
    - si p_goal bajo => UNDER 0.5 next15
    """
    want_market = "OVER_UNDER_0_5_NEXT_15"
    relevant = [o for o in odds if o.market == want_market]
    if not relevant:
        return None

    if p_goal >= 0.55:
        picks = [o for o in relevant if o.selection == "OVER"]
    else:
        picks = [o for o in relevant if o.selection == "UNDER"]

    return max(picks, key=lambda x: x.odd, default=None)

def compute_value(p_goal: float, pick: Odds) -> float:
    """
    valor ≈ (prob_real - prob_implicita) * 100
    prob_implicita = 1/odd
    Para UNDER usamos prob = 1 - p_goal
    """
    implied = 1.0 / max(pick.odd, 1e-9)
    real = p_goal if pick.selection == "OVER" else (1.0 - p_goal)
    return (real - implied) * 100.0

def generate_signal(match: LiveMatch, stats: LiveStats, odds: List[Odds]) -> Signal:
    p_goal = estimate_goal_next15(match, stats)
    pick = pick_best_market(p_goal, odds)

    if pick is None:
        # fallback
        pick = Odds(match.id, "OVER_UNDER_0_5_NEXT_15", "NONE", 1.0)

    value = compute_value(p_goal, pick)
    conf = int(clamp(50 + value * 2, 5, 95))

    # pred final simple: si va ganando alguien, lo mantiene; si empate, 1-1
    if match.score_home > match.score_away:
        pred_final = f"{match.score_home}-{match.score_away}"
    elif match.score_away > match.score_home:
        pred_final = f"{match.score_home}-{match.score_away}"
    else:
        pred_final = f"{match.score_home+1}-{match.score_away+1}" if match.minute > 55 else f"{match.score_home}-{match.score_away}"

    reason = f"pGol15={p_goal:.2f}, SOT={stats.shots_on_target_home+stats.shots_on_target_away}, Dang={stats.dangerous_attacks_home+stats.dangerous_attacks_away}, xG={stats.xg_home+stats.xg_away:.2f}"

    return Signal(
        match_id=match.id,
        home=match.home,
        away=match.away,
        minute=match.minute,
        score=f"{match.score_home}-{match.score_away}",
        pred_next15_goal_prob=p_goal,
        pred_next15_more_goals=(p_goal >= 0.5),
        pred_final_most_probable=pred_final,
        market=pick.market,
        selection=pick.selection,
        odd=pick.odd,
        value=round(value, 2),
        confidence=conf,
        reason=reason,
    )

def to_dict(signal: Signal) -> Dict[str, Any]:
    return asdict(signal)

# chaos_detector.py

from typing import Dict


def _f(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _i(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _u(value) -> str:
    return str(value or "").strip().upper()


def detect_chaos(match: Dict) -> Dict:
    minuto = _i(match.get("minuto"), 0)
    ml = _i(match.get("marcador_local"), 0)
    mv = _i(match.get("marcador_visitante"), 0)
    diff = abs(ml - mv)

    xg = _f(match.get("xG"), 0)
    shots = _f(match.get("shots"), 0)
    shots_on_target = _f(match.get("shots_on_target"), 0)
    dangerous_attacks = _f(match.get("dangerous_attacks"), 0)

    momentum = _u(match.get("momentum"))
    chaos = match.get("chaos", {}) or {}
    goal_pressure = match.get("goal_pressure", {}) or {}
    goal_predictor = match.get("goal_predictor", {}) or {}

    raw_chaos_score = _f(chaos.get("chaos_score"), 0)
    pressure_score = _f(goal_pressure.get("pressure_score"), 0)
    predictor_score = _f(goal_predictor.get("predictor_score"), 0)
    goal5 = _f(goal_predictor.get("goal_next_5_prob"), 0)
    goal10 = _f(goal_predictor.get("goal_next_10_prob"), 0)

    chaos_score = 0.0
    reasons = []

    # 1. Tramo final con partido cerrado
    if minuto >= 75 and diff <= 1:
        chaos_score += 1.5
        reasons.append("tramo final con marcador cerrado")

    # 2. Mucha agresividad ofensiva
    if dangerous_attacks >= 22:
        chaos_score += 1.2
        reasons.append("muchos ataques peligrosos")

    # 3. Volumen alto de remates
    if shots >= 16:
        chaos_score += 1.0
        reasons.append("alto volumen de tiros")

    # 4. Remates al arco altos
    if shots_on_target >= 5:
        chaos_score += 1.0
        reasons.append("muchos tiros a puerta")

    # 5. xG alto con marcador corto
    if xg >= 2.0 and diff <= 1:
        chaos_score += 1.2
        reasons.append("xG alto con partido aún abierto")

    # 6. Momentum explosivo
    if momentum in ("MUY ALTO", "EXPLOSIVO", "CAOS"):
        chaos_score += 1.3
        reasons.append("momentum explosivo")

    # 7. Indicador de caos externo
    if raw_chaos_score >= 9:
        chaos_score += 1.5
        reasons.append("chaos_score elevado")

    # 8. Presión real + predictor alto = partido muy sensible
    if pressure_score >= 7 and predictor_score >= 5 and (goal5 >= 0.50 or goal10 >= 0.65):
        chaos_score += 1.3
        reasons.append("presión real con ventana de gol inmediata")

    if chaos_score >= 5.0:
        chaos_level = "ALTO"
        confidence_penalty = 18
        block_signal = True
    elif chaos_score >= 3.0:
        chaos_level = "MEDIO"
        confidence_penalty = 8
        block_signal = False
    else:
        chaos_level = "BAJO"
        confidence_penalty = 0
        block_signal = False

    return {
        "chaos_level": chaos_level,
        "chaos_detector_score": round(chaos_score, 2),
        "chaos_reason": ", ".join(reasons) if reasons else "Partido estable",
        "chaos_block_signal": block_signal,
        "chaos_confidence_penalty": confidence_penalty,
  }

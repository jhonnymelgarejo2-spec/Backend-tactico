from typing import Dict, List, Any


# =========================================================
# HELPERS
# =========================================================
def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def _safe_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def _safe_upper(value):
    return str(value or "").strip().upper()


def _clamp(value, low, high):
    return max(low, min(high, value))


# =========================================================
# NORMALIZADORES
# =========================================================
def _normalizar_jugador(player: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": str(player.get("name") or player.get("player") or "").strip(),
        "team": str(player.get("team") or "").strip(),
        "is_starting": bool(player.get("is_starting", player.get("starting", True))),
        "is_key": bool(player.get("is_key", False)),
        "status": _safe_upper(player.get("status", "AVAILABLE")),
        "position": _safe_upper(player.get("position", "")),
        "goals": _safe_int(player.get("goals", 0), 0),
        "assists": _safe_int(player.get("assists", 0), 0),
        "rating": _safe_float(player.get("rating", 0), 0.0),
        "fatigue": _safe_float(player.get("fatigue", 0), 0.0),
        "impact": _safe_float(player.get("impact", 0), 0.0),
    }


# =========================================================
# SCORE POR PLANTEL
# =========================================================
def analizar_equipo_players(team_name: str, players: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not players:
        return {
            "team": team_name,
            "available_count": 0,
            "starting_count": 0,
            "key_available": 0,
            "key_missing": 0,
            "fatigue_avg": 0.0,
            "attack_impact": 0.0,
            "player_score": 0.0,
            "player_reason": "Sin datos de jugadores",
        }

    rows = [_normalizar_jugador(p) for p in players]

    available = [p for p in rows if p["status"] not in ("OUT", "INJURED", "SUSPENDED")]
    starting = [p for p in available if p["is_starting"]]

    key_available = 0
    key_missing = 0
    fatigue_vals = []
    attack_impact = 0.0
    reasons = []

    for p in rows:
        is_attacker = p["position"] in ("FW", "ST", "CF", "LW", "RW", "AM")
        base_impact = p["impact"]

        if base_impact <= 0:
            base_impact = (p["goals"] * 1.4) + (p["assists"] * 1.0) + (p["rating"] * 0.35)

        if p["is_key"]:
            if p["status"] in ("OUT", "INJURED", "SUSPENDED"):
                key_missing += 1
            else:
                key_available += 1

        if p["status"] not in ("OUT", "INJURED", "SUSPENDED"):
            fatigue_vals.append(p["fatigue"])
            if is_attacker:
                attack_impact += base_impact

    fatigue_avg = round(sum(fatigue_vals) / len(fatigue_vals), 2) if fatigue_vals else 0.0

    player_score = 50.0
    player_score += key_available * 8.0
    player_score -= key_missing * 10.0
    player_score += min(attack_impact, 20.0) * 1.2
    player_score -= min(fatigue_avg, 100.0) * 0.18
    player_score += min(len(starting), 11) * 0.8
    player_score = round(_clamp(player_score, 0, 100), 2)

    if key_available >= 2:
        reasons.append("Tiene jugadores clave disponibles")
    if key_missing >= 1:
        reasons.append("Presenta bajas importantes")
    if attack_impact >= 10:
        reasons.append("Buen impacto ofensivo titular")
    if fatigue_avg >= 60:
        reasons.append("Fatiga media-alta en plantilla")

    if not reasons:
        reasons.append("Plantilla sin sesgo claro")

    return {
        "team": team_name,
        "available_count": len(available),
        "starting_count": len(starting),
        "key_available": key_available,
        "key_missing": key_missing,
        "fatigue_avg": fatigue_avg,
        "attack_impact": round(attack_impact, 2),
        "player_score": player_score,
        "player_reason": " | ".join(reasons),
    }


# =========================================================
# EVALUACION GLOBAL
# =========================================================
def evaluar_player_impact(
    partido: Dict[str, Any],
    home_players: List[Dict[str, Any]] = None,
    away_players: List[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    home_players = home_players or []
    away_players = away_players or []

    home_team = partido.get("local") or partido.get("home") or "LOCAL"
    away_team = partido.get("visitante") or partido.get("away") or "VISITANTE"

    home_data = analizar_equipo_players(home_team, home_players)
    away_data = analizar_equipo_players(away_team, away_players)

    diff = round(home_data["player_score"] - away_data["player_score"], 2)

    probable_side = "EMPATE"
    if diff >= 8:
        probable_side = "LOCAL"
    elif diff <= -8:
        probable_side = "VISITANTE"

    global_score = round(
        _clamp(
            (home_data["player_score"] * 0.5) +
            (away_data["player_score"] * 0.5),
            0,
            100,
        ),
        2,
    )

    state = "NEUTRO"
    if global_score >= 70:
        state = "FUERTE"
    elif global_score >= 55:
        state = "FAVORABLE"
    elif global_score <= 35:
        state = "DEBIL"

    return {
        "player_impact_score": global_score,
        "player_impact_state": state,
        "player_impact_diff": diff,
        "player_impact_probable_side": probable_side,
        "player_impact_reason": (
            f"{home_team}: {home_data['player_reason']} | "
            f"{away_team}: {away_data['player_reason']}"
        ),
        "home_player_summary": home_data,
        "away_player_summary": away_data,
        "home_attack_impact": home_data["attack_impact"],
        "away_attack_impact": away_data["attack_impact"],
        "home_fatigue_avg": home_data["fatigue_avg"],
        "away_fatigue_avg": away_data["fatigue_avg"],
    }


# =========================================================
# APLICAR A SEÑAL
# =========================================================
def aplicar_player_impact_a_senal(senal: Dict[str, Any], player_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(senal, dict):
        return senal

    if not isinstance(player_data, dict):
        return senal

    confidence = _safe_float(senal.get("confidence", 0), 0.0)
    value = _safe_float(senal.get("value", 0), 0.0)
    market = _safe_upper(senal.get("market", ""))

    impact_score = _safe_float(player_data.get("player_impact_score", 0), 0.0)
    probable_side = _safe_upper(player_data.get("player_impact_probable_side", "EMPATE"))

    ajuste = 0.0

    if impact_score >= 72:
        ajuste += 3.0
    elif impact_score >= 60:
        ajuste += 1.5
    elif impact_score <= 35:
        ajuste -= 2.0

    if probable_side in ("LOCAL", "VISITANTE") and ("GOAL" in market or "OVER" in market):
        ajuste += 0.8

    if "HOLD" in market and impact_score >= 72:
        ajuste -= 1.0

    senal["player_impact_adjustment"] = round(ajuste, 2)
    senal["confidence"] = round(_clamp(confidence + ajuste, 0, 100), 2)
    senal["value"] = round(max(0, value + max(0, ajuste * 0.30)), 2)

    senal.update(player_data)
    return senal

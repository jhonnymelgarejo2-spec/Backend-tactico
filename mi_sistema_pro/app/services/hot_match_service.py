from typing import Dict, Any, Optional

from app.utils.helpers import safe_float, safe_int, safe_text


def _is_hot_match(minuto: int, xg: float, shots: int, shots_on_target: int, dangerous_attacks: int, momentum: str) -> bool:
    momentum_u = safe_text(momentum).upper()

    if minuto < 15 or minuto > 88:
        return False

    strong_pressure = xg >= 1.20 and shots_on_target >= 3
    strong_volume = shots >= 10 and dangerous_attacks >= 18
    strong_momentum = momentum_u in {"ALTO", "MUY ALTO"} and dangerous_attacks >= 14
    explosive_combo = xg >= 1.00 and shots_on_target >= 2 and dangerous_attacks >= 16

    return strong_pressure or strong_volume or strong_momentum or explosive_combo


def _build_hot_reason(minuto: int, xg: float, shots: int, shots_on_target: int, dangerous_attacks: int, momentum: str) -> str:
    momentum_u = safe_text(momentum).upper()

    if xg >= 1.20 and shots_on_target >= 3:
        return "Presión ofensiva real por xG y tiros al arco"

    if shots >= 10 and dangerous_attacks >= 18:
        return "Volumen ofensivo alto y ataques peligrosos sostenidos"

    if momentum_u in {"ALTO", "MUY ALTO"} and dangerous_attacks >= 14:
        return "Momentum alto con agresividad ofensiva"

    if xg >= 1.00 and shots_on_target >= 2 and dangerous_attacks >= 16:
        return "Ritmo ofensivo mixto con señales de gol"

    return "Partido con actividad ofensiva relevante"


def build_hot_match(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(match, dict):
        return None

    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    shots = safe_int(match.get("shots"), 0)
    shots_on_target = safe_int(match.get("shots_on_target"), 0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    estado = safe_text(match.get("estado_partido"), "en_juego").lower()
    momentum = safe_text(match.get("momentum"))
    time_fresh = bool(match.get("time_fresh", True))

    if estado == "finalizado":
        return None

    if not time_fresh:
        return None

    if not _is_hot_match(
        minuto=minuto,
        xg=xg,
        shots=shots,
        shots_on_target=shots_on_target,
        dangerous_attacks=dangerous_attacks,
        momentum=momentum,
    ):
        return None

    return {
        "id": safe_text(match.get("id")),
        "local": safe_text(match.get("local")),
        "visitante": safe_text(match.get("visitante")),
        "liga": safe_text(match.get("liga")),
        "pais": safe_text(match.get("pais")),
        "minuto": minuto,
        "marcador_local": safe_int(match.get("marcador_local")),
        "marcador_visitante": safe_int(match.get("marcador_visitante")),
        "xG": xg,
        "shots": shots,
        "shots_on_target": shots_on_target,
        "dangerous_attacks": dangerous_attacks,
        "momentum": momentum,
        "hot_reason": _build_hot_reason(
            minuto=minuto,
            xg=xg,
            shots=shots,
            shots_on_target=shots_on_target,
            dangerous_attacks=dangerous_attacks,
            momentum=momentum,
        ),
        "source": safe_text(match.get("source")),
        "time_fresh": time_fresh,
        "source_delay_seconds": safe_int(match.get("source_delay_seconds"), 0),
    }

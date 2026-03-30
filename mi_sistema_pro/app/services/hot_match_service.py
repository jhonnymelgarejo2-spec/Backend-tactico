from typing import Dict, Any, Optional

from app.utils.helpers import safe_float, safe_int, safe_text


def build_hot_match(match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(match, dict):
        return None

    minuto = safe_int(match.get("minuto"), 0)
    xg = safe_float(match.get("xG"), 0.0)
    dangerous_attacks = safe_int(match.get("dangerous_attacks"), 0)
    estado = safe_text(match.get("estado_partido"), "en_juego").lower()

    if estado == "finalizado":
        return None

    if minuto < 15:
        return None

    if not (xg >= 1.0 or dangerous_attacks >= 12):
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
        "shots": safe_int(match.get("shots")),
        "shots_on_target": safe_int(match.get("shots_on_target")),
        "dangerous_attacks": dangerous_attacks,
        "momentum": safe_text(match.get("momentum")),
        "source": safe_text(match.get("source")),
        "time_fresh": bool(match.get("time_fresh", True)),
        "source_delay_seconds": safe_int(match.get("source_delay_seconds"), 0),
      }

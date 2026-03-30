import time
from typing import Dict, Any, List

from app.config.config import settings
from app.engines.signal_engine import generate_signal
from app.fetchers.live_match_fetcher import obtener_partidos_en_vivo
from app.models.models import ScanResult
from app.utils.helpers import safe_float, safe_int, safe_text


def run_scan_cycle() -> Dict[str, Any]:
    started_at = int(time.time())

    result = ScanResult()
    errors: List[str] = []

    try:
        matches = obtener_partidos_en_vivo()
    except Exception as e:
        matches = []
        errors.append(f"ERROR_FETCH_MATCHES: {e}")

    if not isinstance(matches, list):
        matches = []
        errors.append("ERROR_FETCH_MATCHES: respuesta no válida, no es lista")

    result.total_matches = len(matches)

    signals: List[Dict[str, Any]] = []
    hot_matches: List[Dict[str, Any]] = []

    for match in matches:
        try:
            if not isinstance(match, dict):
                continue

            minuto = safe_int(match.get("minuto"), 0)
            xg = safe_float(match.get("xG"), 0.0)
            da = safe_int(match.get("dangerous_attacks"), 0)
            estado = safe_text(match.get("estado_partido"), "en_juego").lower()

            if estado != "finalizado" and minuto >= 15 and (xg >= 1.0 or da >= 12):
                hot_matches.append({
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
                    "dangerous_attacks": da,
                    "momentum": safe_text(match.get("momentum")),
                    "source": safe_text(match.get("source")),
                    "time_fresh": bool(match.get("time_fresh", True)),
                    "source_delay_seconds": safe_int(match.get("source_delay_seconds"), 0),
                })

            signal = generate_signal(match)
            if signal:
                signals.append(signal)

        except Exception as e:
            errors.append(f"ERROR_PROCESS_MATCH_{safe_text(match.get('id'))}: {e}")

    signals.sort(
        key=lambda s: (
            safe_float(s.get("signal_score"), 0.0),
            safe_float(s.get("confidence"), 0.0),
            safe_float(s.get("value"), 0.0),
        ),
        reverse=True,
    )

    hot_matches.sort(
        key=lambda m: (
            safe_float(m.get("xG"), 0.0),
            safe_int(m.get("shots_on_target"), 0),
            safe_int(m.get("dangerous_attacks"), 0),
        ),
        reverse=True,
    )

    signals = signals[:settings.MAX_SIGNALS]
    hot_matches = hot_matches[:10]

    result.total_signals = len(signals)
    result.signals = signals
    result.hot_matches = hot_matches
    result.errors = errors

    return {
        "ok": True,
        "system": settings.SYSTEM_NAME,
        "version": settings.SYSTEM_VERSION,
        "scan_started_at": started_at,
        "scan_finished_at": int(time.time()),
        "stats": {
            "total_matches": result.total_matches,
            "total_signals": result.total_signals,
            "total_hot_matches": len(result.hot_matches),
            "errors": len(result.errors),
        },
        "signals": result.signals,
        "hot_matches": result.hot_matches,
        "errors": result.errors,
    }
